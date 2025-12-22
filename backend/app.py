from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 目录：backend/ frontend/ data/
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))
DATA_DIR = os.environ.get("DATA_DIR", os.path.normpath(os.path.join(BASE_DIR, "..", "data")))

# 文件名支持：crawl_history_beijing.json / crawl_history_bj.json 等
FILE_RE = re.compile(r"^crawl_history_(?P<city>[a-zA-Z]+)\.json$", re.IGNORECASE)

# 可选：把全拼统一映射到缩写（你也可以只用缩写文件名）
CITY_ALIAS = {
    "beijing": "bj",
    "shanghai": "sh",
    "guangzhou": "gz",
    "shenzhen": "sz",
    "bj": "bj",
    "sh": "sh",
    "gz": "gz",
    "sz": "sz",
}

# 缓存：按 city_key 缓存数据 + 文件 mtime（方便热更新）
CACHE: Dict[str, Dict[str, Any]] = {}

app = Flask(__name__)


def _read_json_records(path: str) -> List[Dict[str, Any]]:
    """
    兼容：
    1) JSON array: [ {...}, ... ]
    2) JSON dict 包裹: {data:[...]} / {items:[...]} / ...
    3) NDJSON: 每行一个 JSON object
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    # 先尝试标准 JSON
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, list):
            return [r for r in obj if isinstance(r, dict)]
        if isinstance(obj, dict):
            for k in ("data", "items", "records", "list"):
                v = obj.get(k)
                if isinstance(v, list):
                    return [r for r in v if isinstance(r, dict)]
            return [obj]
    except json.JSONDecodeError:
        pass

    # 再尝试 NDJSON
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if isinstance(r, dict):
                    out.append(r)
            except Exception:
                continue
    return out


def _normalize_city_key(raw: str) -> str:
    k = (raw or "").strip().lower()
    return CITY_ALIAS.get(k, k)


def _scan_data_files() -> Dict[str, str]:
    """
    返回 {city_key: filepath}
    city_key 会归一为 bj/sh/gz/sz 或其它
    """
    if not os.path.isdir(DATA_DIR):
        return {}
    mapping: Dict[str, str] = {}
    for fn in os.listdir(DATA_DIR):
        m = FILE_RE.match(fn)
        if not m:
            continue
        city_raw = m.group("city")
        city_key = _normalize_city_key(city_raw)
        mapping[city_key] = os.path.join(DATA_DIR, fn)
    return mapping


def _load_city_data(city_key: str) -> List[Dict[str, Any]]:
    files = _scan_data_files()
    if city_key not in files:
        raise KeyError(f"city '{city_key}' not found. available={sorted(files.keys())}")

    path = files[city_key]
    mtime = os.path.getmtime(path)

    cached = CACHE.get(city_key)
    if cached and cached.get("mtime") == mtime:
        return cached["rows"]

    rows = _read_json_records(path)
    # 轻量清洗：确保字段存在但不强制（字段缺失前端显示为 '-'）
    CACHE[city_key] = {"mtime": mtime, "rows": rows, "path": path}
    return rows


def _parse_int(v: Optional[str], default: int) -> int:
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default


def _apply_filters(rows: List[Dict[str, Any]], q: Dict[str, str]) -> List[Dict[str, Any]]:
    # 精确匹配（最稳定）
    def eq(field: str, value: Optional[str], r: Dict[str, Any]) -> bool:
        if not value:
            return True
        return str(r.get(field, "")).strip() == value.strip()

    region = q.get("region")
    bizcircle = q.get("bizcircle")
    community = q.get("community")
    layout = q.get("layout")

    out = []
    for r in rows:
        if not eq("region", region, r):
            continue
        if not eq("bizcircle", bizcircle, r):
            continue
        if not eq("community", community, r):
            continue
        if not eq("layout", layout, r):
            continue
        out.append(r)
    return out


def _sort_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # 以 deal_date/crawl_time 倒序（字符串可比，格式像 2025-11-14 / 2025-12-16T20:03:19）
    def key(r: Dict[str, Any]) -> Tuple[str, str]:
        return (str(r.get("deal_date") or ""), str(r.get("crawl_time") or ""))

    return sorted(rows, key=key, reverse=True)


@app.get("/api/health")
def health():
    files = _scan_data_files()
    return jsonify(
        {
            "ok": True,
            "frontend_dir": FRONTEND_DIR,
            "data_dir": DATA_DIR,
            "cities": sorted(files.keys()),
        }
    )


@app.get("/api/cities")
def cities():
    files = _scan_data_files()
    return jsonify({"cities": sorted(files.keys())})


@app.get("/api/listings")
def listings():
    city = _normalize_city_key(request.args.get("city", ""))
    if not city:
        return jsonify({"error": "missing_city", "message": "请传 city=bj/sh/gz/sz"}), 400

    page = max(1, _parse_int(request.args.get("page"), 1))
    page_size = max(1, min(_parse_int(request.args.get("page_size"), 20), 200))

    try:
        rows = _load_city_data(city)
    except KeyError as e:
        return jsonify({"error": "city_not_found", "message": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": "file_not_found", "message": str(e)}), 500

    rows = _apply_filters(rows, dict(request.args))
    rows = _sort_rows(rows)

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    items = rows[start:end]

    return jsonify({"items": items, "total": total, "page": page, "page_size": page_size})


@app.get("/api/price_trend")
def price_trend():
    city = _normalize_city_key(request.args.get("city", ""))
    if not city:
        return jsonify({"error": "missing_city", "message": "请传 city=bj/sh/gz/sz"}), 400

    try:
        rows = _load_city_data(city)
    except KeyError as e:
        return jsonify({"error": "city_not_found", "message": str(e)}), 400

    rows = _apply_filters(rows, dict(request.args))

    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        deal_date = r.get("deal_date")
        if isinstance(deal_date, str) and len(deal_date) >= 7:
            month = deal_date[:7]  # YYYY-MM
            buckets[month].append(r)

    points = []
    for month in sorted(buckets.keys()):
        items = buckets[month]
        unit_prices = [i.get("unit_price_yuan_sqm") for i in items if isinstance(i.get("unit_price_yuan_sqm"), (int, float))]
        totals = [i.get("total_price_wan") for i in items if isinstance(i.get("total_price_wan"), (int, float))]

        avg_unit = round(sum(unit_prices) / len(unit_prices)) if unit_prices else None
        avg_total = round(sum(totals) / len(totals), 2) if totals else None

        points.append(
            {
                "month": month,
                "avg_unit_price_yuan_sqm": avg_unit,
                "avg_total_price_wan": avg_total,
                "count": len(items),
            }
        )

    return jsonify({"points": points})


# ====== 关键：用 app.py 直接进入页面（托管 frontend/）======
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    # /api 继续走 API，不被静态路由吞掉
    if path.startswith("api"):
        return jsonify({"error": "not_found"}), 404

    # 根路径：优先返回 init.html
    if path == "":
        init_fp = os.path.join(FRONTEND_DIR, "init.html")
        if os.path.exists(init_fp):
            return send_from_directory(FRONTEND_DIR, "init.html")

    # 若请求的是 frontend 中真实存在的文件，直接返回
    if path and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)

    # fallback -> index.html（兼容刷新/直达）
    return send_from_directory(FRONTEND_DIR, "index.html")



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
