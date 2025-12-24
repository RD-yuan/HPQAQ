# backend/crawlers/tw_deals_crawler.py
# -*- coding: utf-8 -*-
"""
抓取台湾（台北市 / 新北市）实价登录「买卖」成交数据，并输出为与你现有 crawl_history_*.json 类似的结构。

数据源：内政部不动产成交案件实价登录 Open Data（当期批次 zip）
注意：
- 这是“成交资料”，不是挂牌/房源列表。
- 部分字段（如朝向、商圈）在实价登录中通常没有，脚本会置 None。
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
import zipfile


OPEN_DATA_ZIP_URL = "https://plvr.land.moi.gov.tw/Download?type=zip&fileName=lvr_landcsv.zip"

# 实价登录 zip 内部文件：以县市代号开头的小写字母
# 本脚本基于当期 zip 的实际文件名结构：
# - a_lvr_land_a.csv  => 台北市（Taipei City）
# - f_lvr_land_a.csv  => 新北市（New Taipei City）
CITY_FILE_PREFIX = {
    "taipei": "a",
    "newtaipei": "f",
}

OUTPUT_FILE = {
    "taipei": "crawl_history_taipei.json",
    "newtaipei": "crawl_history_newtaipei.json",
}


def now_iso_seconds() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def safe_float(x: object) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "" or s.lower() == "nan":
            return None
        return float(s)
    except Exception:
        return None


def safe_int(x: object) -> Optional[int]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "" or s.lower() == "nan":
            return None
        return int(float(s))
    except Exception:
        return None


def roc_yyyymmdd_to_iso(roc_date: str) -> Optional[str]:
    """
    实价登录日期通常是民国：YYYMMDD（例：1141113 => 2025-11-13）
    """
    s = (roc_date or "").strip()
    if not s.isdigit():
        return None
    if len(s) == 7:
        roc_year = int(s[:3])
        mm = int(s[3:5])
        dd = int(s[5:7])
    elif len(s) == 6:
        roc_year = int(s[:2])
        mm = int(s[2:4])
        dd = int(s[4:6])
    else:
        return None

    year = roc_year + 1911
    try:
        return dt.date(year, mm, dd).isoformat()
    except ValueError:
        return None


def roc_yyyymmdd_to_year(roc_date: str) -> Optional[int]:
    """
    建筑完成年月字段也常用民国年月日或民国年月（这里做宽松处理，取前3位年）。
    例如：0940817 => 2005 年
    """
    s = (roc_date or "").strip()
    if not s.isdigit():
        return None
    if len(s) >= 3:
        # 常见 7 位：YYYMMDD
        roc_year = int(s[:3]) if len(s) >= 7 else int(s[:2]) if len(s) == 6 else None
        if roc_year is None:
            return None
        return roc_year + 1911
    return None


def download_zip(url: str, dest_path: Path, timeout: int = 60) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (HPQAQ bot; +https://csqaq.cn/)",
        "Accept": "*/*",
    }

    with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)


def load_existing_json(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def dedup_merge(existing: List[dict], new_items: List[dict]) -> List[dict]:
    """
    用 house_id 做去重（实价登录的 编号/移转编号 通常能唯一定位一笔成交）。
    """
    seen = set()
    merged: List[dict] = []
    for item in existing:
        hid = item.get("house_id")
        if hid:
            seen.add(hid)
        merged.append(item)

    for item in new_items:
        hid = item.get("house_id")
        if hid and hid in seen:
            continue
        if hid:
            seen.add(hid)
        merged.append(item)

    # 可选：按成交日期排序（无日期的放后面）
    def sort_key(x: dict) -> Tuple[int, str]:
        d = x.get("deal_date")
        if isinstance(d, str) and len(d) == 10:
            return (0, d)
        return (1, "")

    merged.sort(key=sort_key)
    return merged


def is_english_hint_row(row: Dict[str, str]) -> bool:
    """
    实价登录 csv 通常第一行是英文字段说明（不是数据），这里识别并跳过。
    """
    town = (row.get("鄉鎮市區") or "").strip()
    serial = (row.get("編號") or "").strip().lower()
    if town.startswith("The villages") or serial.startswith("serial"):
        return True
    return False


def row_to_hpqaq_record(row: Dict[str, str], crawl_time: str) -> Optional[dict]:
    """
    转换为你现有 JSON schema（字段名保持一致）。
    注意：币别为新台币 TWD（total_price_wan = 总价元 / 10000）
    """
    target = (row.get("交易標的") or "").strip()
    if not target:
        return None

    # 过滤“二手房成交”：只保留包含 建物/房地 的成交，排除纯车位/纯土地
    if target == "車位":
        return None
    if ("建物" not in target) and ("房地" not in target):
        return None

    total_price_yuan = safe_float(row.get("總價元"))
    unit_price = safe_int(row.get("單價元平方公尺"))
    area = safe_float(row.get("建物移轉總面積平方公尺"))

    room = safe_int(row.get("建物現況格局-房"))
    hall = safe_int(row.get("建物現況格局-廳"))

    layout = None
    if room is not None and hall is not None:
        layout = f"{room}室{hall}厅"
    elif room is not None:
        layout = f"{room}室"

    address = (row.get("土地位置建物門牌") or "").strip() or None
    district = (row.get("鄉鎮市區") or "").strip() or None

    house_id = (row.get("編號") or row.get("移轉編號") or "").strip() or None

    return {
        "region": district,                      # 区（例如：万华区 / 板桥区）
        "bizcircle": None,                      # 实价登录通常没商圈字段
        "community": address,                   # 这里用门牌地址代替（你也可后续做地理解析）
        "house_id": house_id,                   # 实价登录编号/移转编号
        "detail_url": None,                     # 实价登录批次不提供每笔网页详情链接
        "total_price_wan": round(total_price_yuan / 10000, 1) if total_price_yuan else None,
        "unit_price_yuan_sqm": unit_price,      # 单价(元/㎡)，这里是 TWD/㎡
        "layout": layout,
        "room_count": room,
        "hall_count": hall,
        "area_sqm": area,
        "orientation": None,                    # 多数批次无朝向
        "building_year": roc_yyyymmdd_to_year(row.get("建築完成年月") or ""),
        "floor": (row.get("移轉層次") or "").strip() or None,
        "deal_date": roc_yyyymmdd_to_iso(row.get("交易年月日") or ""),
        "crawl_time": crawl_time,
    }


def iter_city_rows(zf: zipfile.ZipFile, city_prefix: str) -> Iterable[Dict[str, str]]:
    """
    读取某城市的 *_lvr_land_a.csv（买卖成交主表）
    """
    csv_name = f"{city_prefix}_lvr_land_a.csv"
    if csv_name not in zf.namelist():
        # 容错：有些 zip 可能大小写不同
        lower_map = {name.lower(): name for name in zf.namelist()}
        real_name = lower_map.get(csv_name.lower())
        if not real_name:
            raise FileNotFoundError(f"zip 内找不到 {csv_name}")
        csv_name = real_name

    with zf.open(csv_name) as f:
        text = io.TextIOWrapper(f, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text)
        for row in reader:
            if is_english_hint_row(row):
                continue
            yield row


@dataclass
class CrawlResult:
    city_key: str
    count_new: int
    out_path: Path


def crawl(out_dir: Path, keep_zip: bool = False) -> List[CrawlResult]:
    out_dir.mkdir(parents=True, exist_ok=True)

    tmp_dir = out_dir / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / "lvr_landcsv.zip"

    download_zip(OPEN_DATA_ZIP_URL, zip_path)

    crawl_time = now_iso_seconds()
    results: List[CrawlResult] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for city_key, prefix in CITY_FILE_PREFIX.items():
            new_items: List[dict] = []
            for row in iter_city_rows(zf, prefix):
                rec = row_to_hpqaq_record(row, crawl_time=crawl_time)
                if rec:
                    new_items.append(rec)

            out_path = out_dir / OUTPUT_FILE[city_key]
            existing = load_existing_json(out_path)
            merged = dedup_merge(existing, new_items)
            out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

            results.append(CrawlResult(city_key=city_key, count_new=len(new_items), out_path=out_path))

    if not keep_zip:
        try:
            zip_path.unlink(missing_ok=True)
        except Exception:
            pass

    return results


if __name__ == "__main__":
    # 默认把输出放到项目根目录的 data/
    project_root = Path(__file__).resolve().parents[2]  # backend/crawlers/.. -> 项目根
    out_dir = project_root / "data"

    res = crawl(out_dir=out_dir, keep_zip=False)
    for r in res:
        print(f"[OK] {r.city_key}: +{r.count_new} records -> {r.out_path}")
