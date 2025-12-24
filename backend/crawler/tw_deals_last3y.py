# backend/crawlers/tw_deals_last3y.py
# -*- coding: utf-8 -*-
"""
台湾实价登录（台北市/新北市）近三年“买卖成交”抓取脚本：
- 按季度下载官方批次 ZIP（DownloadSeason）
- 只保留：交易标的包含「房地/建物」且不是纯车位/纯土地
- 解析后再按 deal_date >= (今天 - 3年) 精确过滤
- 以 house_id 去重，合并写入 data/crawl_history_*.json

依赖：pip install requests
运行：python backend/crawlers/tw_deals_last3y.py
"""

from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from zipfile import ZipFile, BadZipFile

import requests

BASE = "https://plvr.land.moi.gov.tw"
SEASON_ZIP_URL = f"{BASE}/DownloadSeason?season={{season}}&type=zip&fileName=lvr_landcsv.zip"

# 台北市=a，新北市=f（官方 zip 内文件前缀）
CITY_PREFIX = {
    "taipei": "a",
    "newtaipei": "f",
}

OUTPUT_FILE = {
    "taipei": "crawl_history_taipei.json",
    "newtaipei": "crawl_history_newtaipei.json",
}

KEEP_WORDS = ("房地", "建物")
DROP_EXACT = ("車位",)
DROP_WORDS = ("土地",)  # 纯土地也丢掉（如你想保留房地+土地，可删掉这一条）


def now_iso_local() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def subtract_years(d: date, years: int) -> date:
    """dateutil-free 的减年；处理 2/29."""
    try:
        return d.replace(year=d.year - years)
    except ValueError:
        # e.g. Feb 29 -> Feb 28
        return d.replace(year=d.year - years, day=28)


def current_season(today: Optional[date] = None) -> str:
    today = today or date.today()
    q = (today.month - 1) // 3 + 1  # 1..4
    roc = today.year - 1911
    return f"{roc}S{q}"


def season_of(d: date) -> str:
    q = (d.month - 1) // 3 + 1
    roc = d.year - 1911
    return f"{roc}S{q}"


def season_to_tuple(season: str) -> Tuple[int, int]:
    s = season.strip().upper()
    if "S" not in s:
        raise ValueError(f"Bad season: {season}")
    roc_s, q_s = s.split("S", 1)
    return int(roc_s), int(q_s)


def tuple_to_season(roc: int, q: int) -> str:
    return f"{roc}S{q}"


def iter_seasons(start: str, end: str) -> Iterable[str]:
    s_roc, s_q = season_to_tuple(start)
    e_roc, e_q = season_to_tuple(end)
    roc, q = s_roc, s_q
    while (roc, q) <= (e_roc, e_q):
        yield tuple_to_season(roc, q)
        q += 1
        if q == 5:
            q = 1
            roc += 1


def try_float(x: object) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "" or s.lower() == "nan":
            return None
        return float(s)
    except Exception:
        return None


def try_int(x: object) -> Optional[int]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "" or s.lower() == "nan":
            return None
        return int(float(s))
    except Exception:
        return None


def parse_roc_yyyymmdd(s: str) -> Optional[str]:
    """民国 yyyMMdd -> YYYY-MM-DD"""
    if not s:
        return None
    s = str(s).strip()
    if not s.isdigit() or len(s) != 7:
        return None
    roc = int(s[:3])
    mm = int(s[3:5])
    dd = int(s[5:7])
    yyyy = roc + 1911
    try:
        return date(yyyy, mm, dd).isoformat()
    except ValueError:
        return None


def parse_roc_year(s: str) -> Optional[int]:
    """建築完成年月常见民国 yyyMMdd 或 yyyMM，取前三位年"""
    if not s:
        return None
    s = str(s).strip()
    if not s.isdigit() or len(s) < 3:
        return None
    roc = int(s[:3])
    return roc + 1911


def get_first(row: Dict[str, str], keys: List[str]) -> Optional[str]:
    """兼容 BOM/字段名差异：按 keys 顺序找第一个存在且非空的值。"""
    for k in keys:
        if k in row and str(row.get(k) or "").strip() != "":
            return row.get(k)
        bom_k = "\ufeff" + k
        if bom_k in row and str(row.get(bom_k) or "").strip() != "":
            return row.get(bom_k)
    return None


def download_zip(url: str, dst: Path, timeout: int = 60) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # 简单缓存：存在且>1KB就不下
    if dst.exists() and dst.stat().st_size > 1024:
        return True
    headers = {"User-Agent": "Mozilla/5.0 (HPQAQ bot)"}
    r = requests.get(url, headers=headers, stream=True, timeout=timeout)
    if r.status_code != 200:
        return False
    with open(dst, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 256):
            if chunk:
                f.write(chunk)
    return dst.exists() and dst.stat().st_size > 1024


def open_zip(path: Path) -> Optional[ZipFile]:
    try:
        return ZipFile(path, "r")
    except BadZipFile:
        return None


def find_member(zf: ZipFile, prefix: str, suffix: str) -> Optional[str]:
    want = f"{prefix.lower()}{suffix.lower()}"
    for name in zf.namelist():
        if name.lower().endswith(want):
            return name
    return None


def load_existing(out_path: Path) -> Tuple[List[dict], set]:
    if not out_path.exists():
        return [], set()
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return [], set()
        seen = set()
        for r in data:
            if isinstance(r, dict) and r.get("house_id"):
                seen.add(str(r["house_id"]))
        return data, seen
    except Exception:
        return [], set()


def keep_target(target: str) -> bool:
    t = (target or "").strip()
    if not t:
        return False
    if t in DROP_EXACT:
        return False
    if any(w in t for w in DROP_WORDS) and not any(w in t for w in KEEP_WORDS):
        return False
    return any(w in t for w in KEEP_WORDS)


def parse_city_records(zf: ZipFile, city_prefix: str, season: str, start_date_iso: str) -> List[dict]:
    """
    解析 *_lvr_land_a.csv（买卖主档）
    start_date_iso: 'YYYY-MM-DD' 用于最终过滤
    """
    member = find_member(zf, city_prefix, "_lvr_land_a.csv")
    if not member:
        return []

    out: List[dict] = []
    crawl_time = now_iso_local()

    with zf.open(member) as f:
        text = io.TextIOWrapper(f, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text)

        for row in reader:
            district = (get_first(row, ["鄉鎮市區"]) or "").strip()
            target = (get_first(row, ["交易標的"]) or "").strip()
            if not district or not keep_target(target):
                continue

            deal_date = parse_roc_yyyymmdd(get_first(row, ["交易年月日"]) or "")
            # 精确过滤：只要近三年
            if not deal_date or deal_date < start_date_iso:
                continue

            addr = (get_first(row, ["土地區段位置或建物區門牌", "土地位置建物門牌", "土地區段位置建物區門牌", "土地位置建物門牌"]) or "").strip() or None
            house_id = (get_first(row, ["編號", "移轉編號"]) or "").strip() or None
            if not house_id:
                continue

            total_price = try_int(get_first(row, ["總價元"]))
            unit_price = try_int(get_first(row, ["單價元平方公尺", "單價每平方公尺", "單價元/平方公尺", "單價每平方公尺元", "單價每平方公尺(元)"]))
            area = try_float(get_first(row, ["建物移轉總面積平方公尺"]))

            room = try_int(get_first(row, ["建物現況格局-房"]))
            hall = try_int(get_first(row, ["建物現況格局-廳"]))
            layout = None
            if room is not None or hall is not None:
                rr = "" if room is None else f"{room}室"
                hh = "" if hall is None else f"{hall}厅"
                layout = (rr + hh) if (rr + hh) else None

            building_year = parse_roc_year(get_first(row, ["建築完成年月"]) or "")

            rec = {
                "region": district,
                "bizcircle": None,
                "community": addr,
                "house_id": house_id,
                "detail_url": None,
                "total_price_wan": round(total_price / 10000.0, 1) if total_price is not None else None,
                "unit_price_yuan_sqm": unit_price,
                "layout": layout,
                "room_count": room,
                "hall_count": hall,
                "area_sqm": area,
                "orientation": None,
                "building_year": building_year,
                "floor": (get_first(row, ["移轉層次"]) or "").strip() or None,
                "deal_date": deal_date,
                "crawl_time": crawl_time,
                "source_season": season,  # 额外字段：便于排查数据来自哪个季度
            }
            out.append(rec)

    return out


@dataclass
class CityCfg:
    key: str
    prefix: str
    out_path: Path


def main():
    # 项目根目录：backend/crawlers -> 上两级
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 近三年起始日期（精确到日）
    today = date.today()
    start_date = subtract_years(today, 3)
    start_date_iso = start_date.isoformat()

    # 为减少“季度边界缺口”，从“起始日期所在季度”开始拉，直到当前季度
    start_season = season_of(start_date)
    end_season = current_season(today)

    seasons = list(iter_seasons(start_season, end_season))
    print(f"[HPQAQ] Today={today.isoformat()}  StartDate(3y)={start_date_iso}")
    print(f"[HPQAQ] Seasons: {seasons[0]} .. {seasons[-1]} (count={len(seasons)})")

    cache_dir = data_dir / "_tmp_tw_open_data_last3y"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cities = [
        CityCfg("taipei", CITY_PREFIX["taipei"], data_dir / OUTPUT_FILE["taipei"]),
        CityCfg("newtaipei", CITY_PREFIX["newtaipei"], data_dir / OUTPUT_FILE["newtaipei"]),
    ]

    existing: Dict[str, List[dict]] = {}
    seen: Dict[str, set] = {}
    for c in cities:
        arr, s = load_existing(c.out_path)
        existing[c.key] = arr
        seen[c.key] = s
        print(f"[{c.key}] existing={len(arr)} unique_ids={len(s)}")

    for season in seasons:
        url = SEASON_ZIP_URL.format(season=season)
        zip_path = cache_dir / f"lvr_landcsv_{season}.zip"

        ok = download_zip(url, zip_path)
        if not ok:
            print(f"[{season}] download failed -> skip")
            time.sleep(0.4)
            continue

        zf = open_zip(zip_path)
        if not zf:
            print(f"[{season}] bad zip -> skip")
            time.sleep(0.2)
            continue

        with zf:
            for c in cities:
                rows = parse_city_records(zf, c.prefix, season, start_date_iso=start_date_iso)
                if not rows:
                    continue

                add = 0
                for r in rows:
                    hid = str(r["house_id"])
                    if hid in seen[c.key]:
                        continue
                    seen[c.key].add(hid)
                    existing[c.key].append(r)
                    add += 1

                if add:
                    print(f"[{season}] [{c.key}] +{add} (total={len(existing[c.key])})")

        time.sleep(0.5)  # 给服务器一点喘息

    # 写回
    for c in cities:
        # 再做一次保险过滤（避免旧文件里混入更早数据）
        filtered = [r for r in existing[c.key] if (r.get("deal_date") and r["deal_date"] >= start_date_iso)]
        filtered.sort(key=lambda r: r.get("deal_date") or "9999-99-99")
        c.out_path.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{c.key}] wrote {c.out_path} records={len(filtered)} (>= {start_date_iso})")


if __name__ == "__main__":
    main()
