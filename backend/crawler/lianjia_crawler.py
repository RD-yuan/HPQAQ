import json
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except Exception:
    Retry = None


# ===========================
# 配置区
# ===========================
BASE_URL = "https://bj.lianjia.com/ershoufang/{district}/pg{page}/"

DISTRICTS = {
    "东城": "dongcheng",
    "海淀": "haidian",
    "通州": "tongzhou",
    "怀柔": "huairou",
}

TARGET_PER_DISTRICT = 1000
MAX_PAGES_PER_DISTRICT = 200

# 强烈建议：先用“仅列表模式”跑满 1000/区（快、稳定）
DETAIL_MODE = False  # True 会非常慢且更易风控（不建议）

# 间隔：列表页请求间隔（秒）
SLEEP_LIST_MIN = 0.6
SLEEP_LIST_MAX = 1.2

OUTPUT_NAME = "lianjia_housing_beijing_4districts.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://bj.lianjia.com/",
}

# 备选：手动 Cookie（不建议在任何公共位置粘贴）
MANUAL_COOKIE_STR = "SECKEY_ABVK=+RobYf0w6e1/x+aAkLdRVNq0jrnp4QMe9r1GSXG7AmU%3D; BMAP_SECKEY=bQDX3Y-AYHFj75g9-g4NljrXDcRes3Q2EqmOB9kTWXtHOofZiDMs8PMKsKi3-BS3th88kKmSEDPdaXo3iP91oTc0EMzlK4h82db7DAlp7jCvg8n38xeTDF_bM7cdX6E6VrR1IQ4PRI_86u0Sw-h44kcQtVCZvxFMgehMKdtGlFxQvr8mwJcLFcwOhd3tyBAp; lianjia_uuid=08684bbe-80f4-46f0-8281-b52134a35ae9; _ga=GA1.2.900769530.1764558432; crosSdkDT2019DeviceId=-17jmvd--t2f7fy-o1nb2mjtbqdrhwe-u424wnkqj; ftkrc_=4185d07a-4ebd-486e-9192-5772e869b7cd; lfrc_=3974f4a2-78f6-4f85-b851-3656f6474ff6; login_ucid=2000000515412377; lianjia_token=2.00135d346d480ec81802f01d5cc40a1f41; lianjia_token_secure=2.00135d346d480ec81802f01d5cc40a1f41; security_ticket=Le6NbzkfDhIqQKEuO4GSOru0kHGmj6HHhMzZaz4aPNnabPfysLJ1NX3l6bFvNSzYjA/GLQLZ/glpqnpUVXyDS/GEdFKE9XWf2G8VGWY33/bFS0EyeNt2Mf5tSgqbJO6+G+xwvI7GEH5S34HSDvAFV4nw1tLyIuh3PVm8QlifLsQ=; _jzqckmp=1; _gid=GA1.2.778516721.1765700918; _ga_RCTBRFLNVS=GS2.2.s1765703621$o1$g0$t1765703621$j60$l0$h0; _ga_LRLL77SF11=GS2.2.s1765703643$o1$g1$t1765703671$j32$l0$h0; _ga_GVYN2J1PCG=GS2.2.s1765703643$o1$g1$t1765703671$j32$l0$h0; _ga_C4R21H79WC=GS2.2.s1765703676$o1$g1$t1765703678$j58$l0$h0; _ga_WLZSQZX7DE=GS2.2.s1765703630$o1$g1$t1765704185$j60$l0$h0; _ga_TJZVFLS7KV=GS2.2.s1765703630$o1$g1$t1765704185$j60$l0$h0; lianjia_ssid=3a94498c-8526-4a71-9793-0629d6dad913; Hm_lvt_46bf127ac9b856df503ec2dbf942b67e=1764809305,1765376715,1765700901,1765705031; HMACCOUNT=4DF22A6659352A8E; _jzqa=1.3421507242892507600.1764558424.1765703116.1765705031.10; _jzqc=1; _jzqx=1.1764558424.1765705031.5.jzqsr=ucloud%2Ebupt%2Eedu%2Ecn|jzqct=/.jzqsr=cn%2Ebing%2Ecom|jzqct=/; _ga_654P0WDKYN=GS2.2.s1765704222$o1$g1$t1765705044$j59$l0$h0; select_city=110000; _qzjc=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219ad7e0cceca47-0049a672629ab2-4c657b58-1638720-19ad7e0ccede8d%22%2C%22%24device_id%22%3A%2219ad7e0cceca47-0049a672629ab2-4c657b58-1638720-19ad7e0ccede8d%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%7D%7D; hip=N9jSPiT4n18zdNyLMgphmiJ6zqFqjrVtl2BFCVcp56QCwMinLi6GDzyW1x4AGmkVXnJnstmKNA-i-mjLvPZ-KcCD309ykSiw1OWAofxX58VrwbE14DLXV-FebZmloXpN4sGkzfB6kI6w5Vvwxq5CphqwFX93RBJxrhXwuIXjmieDvPNXkgdRwOwkRxCAiONWMSP5p08JE8eTdDz8XUFQZmXhkdE2bpcvm9HM1Ve1TDIr3W0oc4ANQa4DHSW3Hy5L5QKAxrzlvWMYnLtnkccU5LqGLBZEeIo3dxHz; _gat=1; _gat_past=1; _gat_global=1; _gat_new_global=1; _gat_dianpu_agent=1; Hm_lpvt_46bf127ac9b856df503ec2dbf942b67e=1765707661; _jzqb=1.15.10.1765705031.1; _qzja=1.654706070.1764088221699.1765703115920.1765705062068.1765707625354.1765707661357.0.0.0.92.11; _qzjb=1.1765703115920.44.0.0.0; _qzjto=71.3.0; srcid=eyJ0Ijoie1wiZGF0YVwiOlwiNzk1ZjdjZjczNGFiYTZiMjkxMzYzMzQwODA4MDg2ZjlmYzFhOGZhNTE0MWZiYTQyZmM0OGE3OWMzYzY3YjI3YmM3ZDJlZWY4ZTVmMTYwNmQwNjgyMGUyODNhYTcyNjVmYzJmMGE2ZmEyYTMyZjBlNDc0ZDEyZDg2M2EyOTBhNzA3MmNhN2UzYzM0NzlhNWYyNDI5NGVjN2E0MDU4MmQ0NGU1YTdmYjkwNmRlYmFmMzAwYzUyOWMyNTc4MzdjNmNkMTI2NTVlZDFkYWQ4OTc2YzliZTZlMGFlODM0NWViNzQ1ZWRiY2MzZDIxYmQ2YzJiZmMyODQyM2U2ODc1ZjljZVwiLFwia2V5X2lkXCI6XCIxXCIsXCJzaWduXCI6XCJiNGU1NmEwOVwifSIsInIiOiJodHRwczovL2JqLmxpYW5qaWEuY29tL2Vyc2hvdWZhbmcvZG9uZ2NoZW5nL3BnMS8iLCJvcyI6IndlYiIsInYiOiIwLjEifQ==; _ga_KJTRWRHDL1=GS2.2.s1765703138$o9$g1$t1765707672$j24$l0$h0; _ga_QJN1VP0CMS=GS2.2.s1765703138$o9$g1$t1765707672$j24$l0$h0"


# ===========================
# 路径（修复 debug_html 报错：用脚本所在目录绝对路径）
# ===========================
BASE_DIR = Path(__file__).resolve().parent
DEBUG_DIR = BASE_DIR / "debug_html"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = BASE_DIR / OUTPUT_NAME


def dump_html(tag: str, region: str, page: int, url: str, html: str):
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = DEBUG_DIR / f"{ts}_{tag}_{region}_pg{page}.html"
        p.write_text(html or "", encoding="utf-8", errors="ignore")
        print(f"  🧾 已保存调试页面：{p}")
        print(f"  🔗 URL: {url}")
    except Exception as e:
        # 不允许调试落盘导致程序崩溃
        print(f"  ⚠ 调试页面保存失败（忽略，不中断）：{e}")


# ===========================
# Cookie
# ===========================
def parse_manual_cookie_str(cookie_str: str) -> Dict[str, str]:
    cookie_str = cookie_str.strip().strip(";")
    if not cookie_str:
        return {}
    cookies: Dict[str, str] = {}
    for p in cookie_str.split(";"):
        p = p.strip()
        if "=" not in p:
            continue
        k, v = p.split("=", 1)
        cookies[k.strip()] = v.strip()
    return cookies


def load_browser_cookies(domain: str = ".lianjia.com"):
    try:
        import browser_cookie3
    except Exception:
        return None

    for name in ("edge", "chrome", "firefox"):
        fn = getattr(browser_cookie3, name, None)
        if not fn:
            continue
        try:
            cj = fn(domain_name=domain)
            if cj and len(cj) > 0:
                print(f"✅ 已从浏览器读取 Cookie：{name}（条目数：{len(cj)}）")
                return cj
        except Exception:
            continue
    return None


def get_cookies() -> Union[Dict[str, str], requests.cookies.RequestsCookieJar, None]:
    if MANUAL_COOKIE_STR.strip():
        manual = parse_manual_cookie_str(MANUAL_COOKIE_STR)
        print("✅ 使用手动粘贴的 Cookie，条目数：", len(manual))
        return manual

    cj = load_browser_cookies(".lianjia.com")
    if cj:
        return cj

    print("⚠ 未获取到 Cookie。建议：先登录链家网页版再运行；或把 Cookie 粘贴到 MANUAL_COOKIE_STR。")
    return None


# ===========================
# HTML & 风控判断（只在“解析不到房源”时才认定风控）
# ===========================
def soup_of(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def looks_like_verify_page(html: str) -> bool:
    if not html:
        return True
    s = html
    soup = soup_of(html)
    title = soup.title.get_text(strip=True) if soup.title else ""

    hard_signals = [
        "访问验证", "安全验证", "人机验证", "验证码", "异常访问", "操作太频繁",
        "ke-passport", "登录链家", "链家网用户登录",
    ]
    has_signal = any(x in s for x in hard_signals) or any(x in title for x in hard_signals)

    has_list = soup.find("ul", class_="sellListContent") is not None
    return (not has_list) and has_signal


def polite_sleep(lo: float, hi: float):
    time.sleep(random.uniform(lo, hi))


# ===========================
# 解析：列表页字段（满足作业字段）
# ===========================
@dataclass
class ListRow:
    region: str
    district_slug: str
    name: Optional[str]
    bizcircle: Optional[str]
    total_price_wan: Optional[float]
    unit_price_yuan_sqm: Optional[int]
    layout: Optional[str]
    room_count: Optional[int]
    hall_count: Optional[int]
    area_sqm: Optional[float]
    orientation: Optional[str]
    decoration: Optional[str]
    floor: Optional[str]
    building_year: Optional[int]
    building_age: Optional[int]
    elevator: Optional[str]
    deal_or_publish_time: Optional[str]
    publish_time: Optional[str]
    detail_url: Optional[str]
    house_id: Optional[str]
    tags: List[str]


def extract_house_id(url: str) -> Optional[str]:
    m = re.search(r"/ershoufang/(\d+)\.html", url)
    return m.group(1) if m else None


def parse_publish_date_from_followinfo(text: str) -> Optional[str]:
    if not text:
        return None
    t = text.strip()

    # 常见："... / 7天以前发布"、"... / 2个月以前发布"、"... / 刚刚发布"
    if "刚刚发布" in t:
        return datetime.now().strftime("%Y-%m-%d")

    m_day = re.search(r"(\d+)\s*天以前发布", t)
    if m_day:
        days = int(m_day.group(1))
        d = (datetime.now() - timedelta(days=days)).date()
        return d.strftime("%Y-%m-%d")

    m_month = re.search(r"(\d+)\s*个月以前发布", t)
    if m_month:
        months = int(m_month.group(1))
        d = (datetime.now() - timedelta(days=30 * months)).date()
        return d.strftime("%Y-%m-%d")

    m_year = re.search(r"(\d+)\s*年以前发布", t)
    if m_year:
        years = int(m_year.group(1))
        d = (datetime.now() - timedelta(days=365 * years)).date()
        return d.strftime("%Y-%m-%d")

    return None


def calc_building_age(building_year: Optional[int]) -> Optional[int]:
    if not building_year:
        return None
    try:
        return max(0, datetime.now().year - int(building_year))
    except Exception:
        return None


def parse_list_page(html: str, region_cn: str, district_slug: str) -> List[Dict]:
    soup = soup_of(html)
    container = soup.find("ul", class_="sellListContent")
    if not container:
        return []

    rows: List[Dict] = []

    for li in container.find_all("li", class_="clear"):
        try:
            # 详情链接 & id
            title_div = li.find("div", class_="title")
            a = title_div.find("a") if title_div else None
            detail_url = a["href"].strip() if a and a.get("href") else None
            house_id = extract_house_id(detail_url) if detail_url else None

            # 楼盘 / 商圈
            name = None
            bizcircle = None
            pos_info = li.find("div", class_="positionInfo")
            if pos_info:
                a_tags = pos_info.find_all("a")
                if len(a_tags) >= 1:
                    name = a_tags[0].get_text(strip=True)
                if len(a_tags) >= 2:
                    bizcircle = a_tags[1].get_text(strip=True)
            if not name and a:
                name = a.get_text(strip=True)

            # 总价
            total_price_wan = None
            total_div = li.find("div", class_="totalPrice")
            if total_div and total_div.span:
                try:
                    total_price_wan = float(total_div.span.get_text(strip=True))
                except Exception:
                    total_price_wan = None

            # 单价
            unit_price_yuan_sqm = None
            unit_div = li.find("div", class_="unitPrice")
            if unit_div:
                unit_text = unit_div.get_text(strip=True)
                m_unit = re.search(r"([\d,]+)", unit_text)
                if m_unit:
                    try:
                        unit_price_yuan_sqm = int(m_unit.group(1).replace(",", ""))
                    except Exception:
                        unit_price_yuan_sqm = None

            # houseInfo：户型/面积/朝向/装修/楼层/年份等
            layout = None
            room_count = None
            hall_count = None
            area_sqm = None
            orientation = None
            decoration = None
            floor = None
            building_year = None
            elevator = None  # 列表页通常取不到，做弱匹配/留空

            house_info_div = li.find("div", class_="houseInfo")
            info_text = ""
            if house_info_div:
                info_text = house_info_div.get_text(separator="|", strip=True)
                parts = [p.strip() for p in info_text.split("|") if p.strip()]

                if parts:
                    layout = parts[0]
                    m_room = re.search(r"(\d+)\s*室", layout)
                    m_hall = re.search(r"(\d+)\s*厅", layout)
                    if m_room:
                        room_count = int(m_room.group(1))
                    if m_hall:
                        hall_count = int(m_hall.group(1))

                for p in parts:
                    if "平米" in p:
                        m_area = re.search(r"([\d.]+)", p)
                        if m_area:
                            area_sqm = float(m_area.group(1))
                        break

                for p in parts:
                    if re.fullmatch(r"[东南西北]{1,4}", p):
                        orientation = p
                        break

                for p in parts:
                    if p in ("精装", "简装", "毛坯", "其他"):
                        decoration = p
                        break

                for p in parts:
                    if "楼层" in p or ("层" in p and "共" in p):
                        floor = p
                        break

                for p in parts:
                    m_year = re.search(r"(\d{4})\s*年(?:建)?", p)
                    if m_year:
                        building_year = int(m_year.group(1))
                        break

            # 电梯弱匹配（能取到就取；取不到不强求）
            if info_text:
                if "有电梯" in info_text:
                    elevator = "有"
                elif "无电梯" in info_text:
                    elevator = "无"

            # 标签
            tags: List[str] = []
            tag_div = li.find("div", class_="tag")
            if tag_div:
                for s in tag_div.find_all(["span", "a"]):
                    t = s.get_text(strip=True)
                    if t:
                        tags.append(t)
            if elevator is None and tags:
                if any("电梯" in t for t in tags):
                    elevator = "有"

            # 发布时间（在售用发布时间充当“成交时间字段”）
            publish_time = None
            follow = li.find("div", class_="followInfo")
            if follow:
                follow_text = follow.get_text(" ", strip=True)
                publish_time = parse_publish_date_from_followinfo(follow_text)

            deal_or_publish_time = publish_time  # 在售：用发布时间

            row = ListRow(
                region=region_cn,
                district_slug=district_slug,
                name=name,
                bizcircle=bizcircle,
                total_price_wan=total_price_wan,
                unit_price_yuan_sqm=unit_price_yuan_sqm,
                layout=layout,
                room_count=room_count,
                hall_count=hall_count,
                area_sqm=area_sqm,
                orientation=orientation,
                decoration=decoration,
                floor=floor,
                building_year=building_year,
                building_age=calc_building_age(building_year),
                elevator=elevator,  # 可能为 None
                deal_or_publish_time=deal_or_publish_time,
                publish_time=publish_time,
                detail_url=detail_url,
                house_id=house_id,
                tags=tags,
            )

            # 输出字段（≥10，并包含你要求的那些字段名）
            rows.append({
                "region": row.region,
                "district_slug": row.district_slug,
                "name": row.name,
                "bizcircle": row.bizcircle,

                "total_price_wan": row.total_price_wan,
                "unit_price_yuan_sqm": row.unit_price_yuan_sqm,

                "layout": row.layout,
                "room_count": row.room_count,
                "hall_count": row.hall_count,
                "area_sqm": row.area_sqm,
                "orientation": row.orientation,
                "building_year": row.building_year,
                "building_age": row.building_age,
                "decoration": row.decoration,
                "floor": row.floor,
                "elevator": row.elevator,

                "deal_or_publish_time": row.deal_or_publish_time,
                "publish_time": row.publish_time,

                "detail_url": row.detail_url,
                "house_id": row.house_id,
                "tags": row.tags,
            })

        except Exception:
            continue

    return rows


# ===========================
# 网络 Session
# ===========================
def build_session(cookies) -> requests.Session:
    s = requests.Session()
    if Retry is not None:
        retry = Retry(
            total=4,
            backoff_factor=0.7,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        s.mount("https://", adapter)
        s.mount("http://", adapter)

    if cookies:
        try:
            s.cookies.update(cookies)
        except Exception:
            pass
    return s


def safe_get(session: requests.Session, url: str, timeout: int = 25) -> Optional[requests.Response]:
    try:
        resp = session.get(url, headers=HEADERS, timeout=timeout)
        resp.encoding = "utf-8"
        return resp
    except Exception as e:
        print(f"  ❌ 请求失败：{e}")
        return None


# ===========================
# 爬取：仅列表（快 + 不易风控）
# ===========================
def crawl_district_list_only(session: requests.Session, district_cn: str, district_slug: str) -> List[Dict]:
    collected: List[Dict] = []
    seen_ids = set()

    for page in range(1, MAX_PAGES_PER_DISTRICT + 1):
        if len(collected) >= TARGET_PER_DISTRICT:
            break

        url = BASE_URL.format(district=district_slug, page=page)
        print(f"\n[{district_cn}] 抓取列表页：第 {page} 页  | 当前已收集：{len(collected)}")
        resp = safe_get(session, url)
        if not resp:
            break

        print("  状态码:", resp.status_code)
        if resp.status_code != 200:
            dump_html("list_non200", district_slug, page, url, resp.text)
            break

        rows = parse_list_page(resp.text, district_cn, district_slug)

        if not rows:
            if looks_like_verify_page(resp.text):
                print("  ⚠ 疑似被风控/验证页拦截（列表页无房源结构）。")
                dump_html("list_verify", district_slug, page, url, resp.text)
                # 退避等待一次再重试同页（不绕过验证，只降低触发频率）
                wait = random.uniform(18, 35)
                print(f"  ⏳ 退避等待 {wait:.1f}s 后重试同页一次...")
                time.sleep(wait)

                resp2 = safe_get(session, url)
                if resp2 and resp2.status_code == 200:
                    rows2 = parse_list_page(resp2.text, district_cn, district_slug)
                    if rows2:
                        rows = rows2
                    else:
                        dump_html("list_verify_retry_fail", district_slug, page, url, resp2.text)
                        break
                else:
                    break
            else:
                print("  ⚠ 列表页解析不到房源（可能结构变更或确实无数据）。")
                dump_html("list_empty", district_slug, page, url, resp.text)
                break

        print(f"  ✅ 列表页解析房源数：{len(rows)}")

        for r in rows:
            hid = r.get("house_id") or r.get("detail_url")
            if hid and hid in seen_ids:
                continue
            if hid:
                seen_ids.add(hid)
            collected.append(r)
            if len(collected) >= TARGET_PER_DISTRICT:
                break

        polite_sleep(SLEEP_LIST_MIN, SLEEP_LIST_MAX)

    return collected


def main():
    cookies = get_cookies()
    session = build_session(cookies)

    all_data: List[Dict] = []
    per = {}

    for district_cn, district_slug in DISTRICTS.items():
        rows = crawl_district_list_only(session, district_cn, district_slug)
        per[district_cn] = len(rows)
        all_data.extend(rows)

        if len(rows) < TARGET_PER_DISTRICT:
            print(f"\n⚠ [{district_cn}] 仅抓到 {len(rows)} 条。若 debug_html 是验证页，需要降低频率或改用人工浏览器方式。")
        else:
            print(f"\n✅ [{district_cn}] 完成：{len(rows)} 条（≥{TARGET_PER_DISTRICT}）")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("\n🎉 全部完成！")
    print("各区数量：", per)
    print(f"已保存 {len(all_data)} 条到：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
