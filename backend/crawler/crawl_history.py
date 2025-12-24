"""
房天下历史成交数据爬虫
特性：
- 断点续爬：<脚本同名>.checkpoint.json
- 数据落盘：<脚本同名>.json（每页/触发验证/Ctrl+C 都会保存）
- 触发风控/验证页：暂停 → 手动验证 → 复制最新 Cookie → 重试继续爬
- 识别"超页/无结果页"：自动结束该区

依赖：
pip install -U requests beautifulsoup4 lxml
"""

import json
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

# 商圈成交记录URL模板（按商圈爬取历史成交数据）
# 格式：https://sh.esf.fang.com/chengjiao-{district}-{bizcircle}/i3{page}/
# 注意：sh 表示上海，修改城市需要改为对应城市拼音缩写，如 bj=北京, sz=深圳
BIZCIRCLE_CHENGJIAO_URL = "https://sh.esf.fang.com/chengjiao-{district}-{bizcircle}/"

# 区域成交首页URL模板（用于获取该区域下的商圈列表）
DISTRICT_CHENGJIAO_URL = "https://sh.esf.fang.com/chengjiao-{district}/"

# 要爬取的区域列表：每项为 (区域中文名, 区域代码)
# 区域代码需要从房天下网站URL中获取，不同城市的区域代码不同
# 示例：上海浦东的URL是 https://sh.esf.fang.com/chengjiao-a025/，则代码为 "a025"
# 如需修改城市，请访问目标城市的房天下二手房页面，查看各区域URL中的代码
DISTRICTS: List[Tuple[str, str]] = [
    ("浦东", "a025"),
    # ("徐汇", "a019"),
    # ("闵行", "a018"),
    # ("静安", "a021"),
    # ("虹口", "a023"),
    # ("长宁", "a020"),
    # ("宝山", "a030"),
]

TARGET_BIZCIRCLES_PER_DISTRICT = 1   # 每个区域爬取的商圈数量（可调整以控制数据量）
MAX_PAGES_PER_BIZCIRCLE = 50          # 每个商圈最多爬取的页数（每页约20条成交记录）
MAX_EMPTY_PAGES = 12                   # 连续多少页无数据后停止该商圈（避免无限爬取空页）
START_PAGE = 1                        # 起始页码（通常为1，除非需要跳过前几页）

# 年份过滤设置（只爬取指定年份范围内的数据）
MIN_YEAR = 2023                       # 最早年份（包含），早于此年份的数据会被跳过并停止该商圈
MAX_YEAR = 2025                       # 最晚年份（包含），晚于此年份的数据会被跳过但继续爬取

SLEEP_MIN = 1.5                       # 请求间隔最小秒数（避免请求过快被封）
SLEEP_MAX = 3.0                       # 请求间隔最大秒数（随机延迟在此范围内）
SAVE_EVERY_PAGES = 1                  # 每爬取多少页保存一次数据（1表示每页都保存）

VERIFY_KEYWORDS = [
    "访问验证", "安全验证", "人机验证", "验证码", "异常访问", "操作太频繁", "系统繁忙",
    "请输入验证码", "滑动验证",
]

END_KEYWORDS = [
    "没有找到符合条件的房源",
    "没有找到相关房源",
    "抱歉，没有找到",
    "暂无相关房源",
    "暂无房源",
    "no-result",
    "noresult",
    "noResult",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Referer": "https://sh.esf.fang.com/",
}


# ===========================
# 输出：同名 json + checkpoint + debug_html
# ===========================
BASE_DIR = Path(__file__).resolve().parent
STEM = Path(__file__).stem
OUTPUT_FILE = BASE_DIR / f"{STEM}.json"
CHECKPOINT_FILE = BASE_DIR / f"{STEM}.checkpoint.json"
DEBUG_DIR = BASE_DIR / f"{STEM}_debug_html"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


# ===========================
# 原子写文件
# ===========================
def atomic_write_text(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text or "", encoding="utf-8", errors="ignore")
    tmp.replace(path)


def atomic_write_json(path: Path, obj):
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def dump_html(tag: str, district_slug: str, page: int, url: str, html: str):
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = DEBUG_DIR / f"{ts}_{tag}_{district_slug}_pg{page}.html"
        atomic_write_text(p, html or "")
        print(f"  🧾 已保存调试页面：{p}")
        print(f"  🔗 URL: {url}")
    except Exception as e:
        print(f"  ⚠ 调试页面保存失败（忽略）：{e}")


# ===========================
# 断点 / 数据落盘
# ===========================
def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_data(data: List[Dict]):
    try:
        atomic_write_json(OUTPUT_FILE, data)
        print(f"  💾 已保存：{len(data)} 条 -> {OUTPUT_FILE.name}")
    except Exception as e:
        print(f"  ⚠ 保存数据失败（忽略）：{e}")


def save_checkpoint(current_district_slug: str, next_page: int, stats: Dict[str, int]):
    ck = {
        "current_district_slug": current_district_slug,
        "next_page": next_page,
        "stats": stats,
        "ts": datetime.now().isoformat(),
    }
    try:
        atomic_write_json(CHECKPOINT_FILE, ck)
        print(f"  🧷 已保存断点：{CHECKPOINT_FILE.name}")
    except Exception as e:
        print(f"  ⚠ 保存断点失败（忽略）：{e}")


# ===========================
# Cookie 手动粘贴
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


def prompt_cookie_and_update_session(session: requests.Session) -> bool:
    print("\n================ 手动更新 Cookie ================")
    print("浏览器完成人机验证后：F12 → Network → 刷新页面 → 点开请求 →")
    print("Request Headers 里复制整行 Cookie（单行）→ 粘贴到这里。")
    print("直接回车表示放弃（停止当前任务）。")
    print("================================================\n")

    cookie_str = input("粘贴 Cookie（单行）> ").strip()
    if not cookie_str:
        return False

    cookie_dict = parse_manual_cookie_str(cookie_str)
    if not cookie_dict:
        print("⚠ Cookie 解析失败：没有解析出任何 k=v。")
        return False

    try:
        session.cookies.clear()
    except Exception:
        pass
    session.cookies.update(cookie_dict)

    print(f"✅ Cookie 已更新：条目数 = {len(cookie_dict)}（内容已隐藏）")
    return True


# ===========================
# Session / 请求重试
# ===========================
def build_session() -> requests.Session:
    s = requests.Session()
    if Retry is not None:
        retry = Retry(
            total=4,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        s.mount("https://", adapter)
        s.mount("http://", adapter)
    return s


def safe_get(session: requests.Session, url: str, timeout: int = 25) -> Optional[requests.Response]:
    try:
        resp = session.get(url, headers=HEADERS, timeout=timeout)
        resp.encoding = "utf-8"
        return resp
    except Exception as e:
        print(f"  ❌ 请求失败：{e}")
        return None


def polite_sleep():
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


# ===========================
# 解析 & 页面分类
# ===========================
def soup_of(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def has_deal_list(html: str) -> bool:
    soup = soup_of(html)
    return soup.find("div", class_="houseList") is not None


def get_bizcircles_from_district(html: str, district_code: str) -> List[Tuple[str, str]]:
    """从区域成交首页提取商圈列表，只提取当前区域的商圈"""
    soup = soup_of(html)
    bizcircles = []
    
    # 查找商圈链接，格式如：/chengjiao-a025-b01646/
    links = soup.find_all("a", href=True)
    for link in links:
        href = link.get("href", "")
        # 匹配商圈URL格式：/chengjiao-{district}-{bizcircle}/
        # 只提取当前区域的商圈（district_code必须匹配）
        pattern = rf"/chengjiao-{re.escape(district_code)}-([a-z0-9]+)/?$"
        m = re.search(pattern, href)
        if m:
            bizcircle_code = m.group(1)
            bizcircle_name = link.get_text(strip=True)
            if bizcircle_name and len(bizcircle_name) > 1:
                bizcircles.append((bizcircle_name, bizcircle_code))
    
    # 去重
    seen = set()
    unique_bizcircles = []
    for name, code in bizcircles:
        if code not in seen:
            seen.add(code)
            unique_bizcircles.append((name, code))
    
    return unique_bizcircles


def looks_like_verify_page(html: str) -> bool:
    soup = soup_of(html)
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = (title or "") + " " + (html or "")
    return any(k in text for k in VERIFY_KEYWORDS)


def looks_like_end_page(html: str, page: int) -> bool:
    soup = soup_of(html)
    title = soup.title.get_text(strip=True) if soup.title else ""
    text = (title or "") + " " + (html or "")

    if any(k.lower() in text.lower() for k in END_KEYWORDS):
        return True

    if soup.find(attrs={"class": re.compile(r"no[-_]?result", re.I)}):
        return True

    return False


def classify_page(html: str, page: int) -> str:
    if has_deal_list(html):
        return "OK"

    if looks_like_end_page(html, page):
        return "END"

    if looks_like_verify_page(html):
        return "VERIFY"

    return "UNKNOWN_EMPTY"


# ===========================
# 列表页解析（房天下历史成交）
# ===========================
def parse_deal_date(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})", text)
    if m:
        try:
            return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
        except Exception:
            return None
    return None


def parse_bizcircle_deals(html: str, bizcircle_name: str, district_cn: str) -> List[Dict]:
    soup = soup_of(html)
    
    rows: List[Dict] = []
    container = soup.find("div", class_="houseList")
    if not container:
        return rows
    
    for item in container.find_all("dl"):
        try:
            # 查找dd标签（包含所有信息）
            dd = item.find("dd", class_="info")
            if not dd:
                continue
            
            # 提取标题和链接
            title_elem = dd.find("p", class_="title")
            if not title_elem:
                continue
            
            title_link = title_elem.find("a")
            if not title_link:
                continue
            
            title_text = title_link.get_text(strip=True)
            detail_url = title_link.get("href", "").strip()
            
            house_id = None
            if detail_url:
                m = re.search(r"/chengjiao/(\d+)_", detail_url)
                if m:
                    house_id = m.group(1)
            
            # 从标题提取小区名称、户型和面积
            # 标题格式通常为：小区名 户型 面积
            # 例如："由由一村 2室1厅 64.24平米"
            community = None
            layout = None
            room_count = None
            hall_count = None
            area_sqm = None
            
            # 提取户型
            m_layout = re.search(r"(\d+室\d+厅)", title_text)
            if m_layout:
                layout = m_layout.group(1)
                m_room = re.search(r"(\d+)室", layout)
                m_hall = re.search(r"(\d+)厅", layout)
                if m_room:
                    room_count = int(m_room.group(1))
                if m_hall:
                    hall_count = int(m_hall.group(1))
                
                # 小区名称在户型之前
                community_part = title_text.split(layout)[0].strip()
                if community_part:
                    community = community_part
            else:
                # 如果没有户型，尝试从面积前提取小区名
                m_area_temp = re.search(r"([\d.]+)平米", title_text)
                if m_area_temp:
                    community_part = title_text.split(m_area_temp.group(0))[0].strip()
                    if community_part:
                        community = community_part
            
            # 提取面积
            m_area = re.search(r"([\d.]+)平米", title_text)
            if m_area:
                try:
                    area_sqm = float(m_area.group(1))
                except Exception:
                    pass
            
            # 提取朝向（在mt18的p标签中）
            orientation = None
            orient_elem = dd.find("p", class_="mt18")
            if orient_elem:
                orient_text = orient_elem.get_text(strip=True).split("|")[0].strip()
                if orient_text and orient_text.replace("向", "") in ["东", "南", "西", "北", "东南", "西南", "东北", "西北", "南北"]:
                    orientation = orient_text.replace("向", "")
            
            # 楼层信息（暂时没有明确标识）
            floor = None
            
            # 提取成交日期（在area div中的time p标签）
            deal_date = None
            area_div = dd.find("div", class_="area")
            if area_div:
                time_elem = area_div.find("p", class_="time")
                if time_elem:
                    date_text = time_elem.get_text(strip=True)
                    if re.match(r"\d{4}-\d{2}-\d{2}", date_text):
                        deal_date = date_text
            
            # 提取价格（在moreInfo div中）
            total_price_wan = None
            unit_price_yuan_sqm = None
            
            more_info = dd.find("div", class_="moreInfo")
            if more_info:
                # 总价：<span class="price">1046</span>
                price_span = more_info.find("span", class_="price")
                if price_span:
                    try:
                        total_price_wan = float(price_span.get_text(strip=True))
                    except Exception:
                        pass
                
                # 单价：<b>67415元</b>
                danjia_p = more_info.find("p", class_="danjia")
                if danjia_p:
                    b_tag = danjia_p.find("b")
                    if b_tag:
                        unit_text = b_tag.get_text(strip=True).replace("元", "")
                        try:
                            unit_price_yuan_sqm = int(unit_text)
                        except Exception:
                            pass
            
            # 过滤掉没有价格的数据
            if total_price_wan is None and unit_price_yuan_sqm is None:
                continue
            
            rows.append({
                "region": district_cn,
                "bizcircle": bizcircle_name,
                "community": community,
                "house_id": house_id,
                "detail_url": detail_url,
                "total_price_wan": total_price_wan,
                "unit_price_yuan_sqm": unit_price_yuan_sqm,
                "layout": layout,
                "room_count": room_count,
                "hall_count": hall_count,
                "area_sqm": area_sqm,
                "orientation": orientation,
                "building_year": None,
                "floor": floor,
                "deal_date": deal_date,
                "crawl_time": datetime.now().isoformat(timespec="seconds"),
            })
        except Exception:
            continue

    return rows


# ===========================
# 核心：获取可用页面
# ===========================
class EndOfDistrict(Exception):
    pass


def fetch_html_or_handle(
    session: requests.Session,
    url: str,
    context: str,
    page: int,
    all_data: List[Dict],
    stats: Dict[str, int],
) -> str:
    while True:
        resp = safe_get(session, url)
        if not resp or resp.status_code != 200:
            save_data(all_data)
            save_checkpoint(context, page, stats)
            raise RuntimeError("请求失败或非200，已保存数据与断点。")

        html = resp.text
        kind = classify_page(html, page)

        if kind == "OK":
            return html

        if kind == "END":
            dump_html("end_page", context, page, url, html)
            save_data(all_data)
            save_checkpoint(context, page, stats)
            raise EndOfDistrict()

        if kind == "VERIFY":
            print("  ⚠ 触发风控/人机验证：需要你手动验证后更新 Cookie。")
            dump_html("verify", context, page, url, html)
            save_data(all_data)
            save_checkpoint(context, page, stats)

            ok = prompt_cookie_and_update_session(session)
            if not ok:
                save_data(all_data)
                save_checkpoint(context, page, stats)
                raise SystemExit("未提供 Cookie，已保存数据与断点，程序结束。")

            time.sleep(random.uniform(2.0, 4.0))
            continue

        dump_html("unknown_empty", context, page, url, html)
        save_data(all_data)
        save_checkpoint(context, page, stats)

        print("\n================ 空页/异常页（无法自动判断） ================")
        print(f"URL: {url}")
        print("1) 如果你确认这是风控/验证页：请在浏览器通过验证后粘贴最新 Cookie（单行）")
        print("2) 如果你确认该区已经没有更多房源：请输入 END 结束该区")
        print("3) 直接回车：停止程序（已保存数据与断点）")
        print("==========================================================\n")

        s = input("粘贴 Cookie / 输入 END / 回车停止 > ").strip()
        if not s:
            raise SystemExit("用户停止，已保存数据与断点。")
        if s.upper() == "END":
            raise EndOfDistrict()

        cookie_dict = parse_manual_cookie_str(s)
        if not cookie_dict:
            print("⚠ 输入既不是 END 也不是有效 Cookie，将再次提示。")
            continue

        try:
            session.cookies.clear()
        except Exception:
            pass
        session.cookies.update(cookie_dict)
        print(f"✅ Cookie 已更新：条目数 = {len(cookie_dict)}（内容已隐藏）")
        time.sleep(random.uniform(2.0, 4.0))


def get_bizcircle_page_url(district: str, bizcircle: str, page: int) -> str:
    """生成商圈成交记录的分页URL"""
    base = BIZCIRCLE_CHENGJIAO_URL.format(district=district, bizcircle=bizcircle)
    if page == 1:
        return base
    else:
        return base.rstrip('/') + f"/i3{page}/"


# ===========================
# 主流程：按商圈爬取历史成交数据
# ===========================
def main():
    print("=" * 60)
    print("房天下历史成交数据爬虫 - 按商圈爬取模式")
    print("=" * 60)
    
    all_data: List[Dict] = load_json(OUTPUT_FILE, [])
    
    seen = set()
    stats: Dict[str, int] = {cn: 0 for cn, _ in DISTRICTS}
    for r in all_data:
        hid = r.get("house_id") or r.get("detail_url")
        if hid:
            seen.add(hid)
        cn = r.get("region")
        if cn in stats:
            stats[cn] += 1
    
    ck = load_json(CHECKPOINT_FILE, {})
    current_district = ck.get("current_district")
    current_bizcircle_idx = ck.get("current_bizcircle_idx", 0)
    current_page = ck.get("current_page", START_PAGE)
    
    session = build_session()
    
    print("\n如你已准备好 Cookie，可直接粘贴（回车跳过，触发验证时再粘）：")
    init_cookie = input("开局 Cookie（可空）> ").strip()
    if init_cookie:
        cdict = parse_manual_cookie_str(init_cookie)
        if cdict:
            session.cookies.update(cdict)
            print(f"✅ 开局 Cookie 已设置：条目数 = {len(cdict)}（内容已隐藏）")
        else:
            print("⚠ 开局 Cookie 解析失败，已忽略。")
    
    try:
        for district_cn, district_slug in DISTRICTS:
            if current_district and district_cn != current_district:
                continue
            
            print(f"\n{'='*60}")
            print(f"开始爬取区域：{district_cn}")
            print(f"{'='*60}")
            
            bizcircles_list = []
            bizcircle_file = BASE_DIR / f"bizcircles_{district_slug}.json"
            
            if bizcircle_file.exists():
                print(f"  📋 从缓存加载商圈列表：{bizcircle_file.name}")
                bizcircles_list = load_json(bizcircle_file, [])
            else:
                print(f"  🔍 正在获取 {district_cn} 的商圈列表...")
                try:
                    url = DISTRICT_CHENGJIAO_URL.format(district=district_slug)
                    resp = safe_get(session, url)
                    if resp and resp.status_code == 200:
                        bizcircles_list = get_bizcircles_from_district(resp.text, district_slug)
                        if bizcircles_list:
                            atomic_write_json(bizcircle_file, bizcircles_list)
                            print(f"  ✅ 共获取 {len(bizcircles_list)} 个商圈，已缓存")
                        else:
                            print(f"  ⚠ 未能提取到 {district_cn} 的商圈")
                        polite_sleep()
                except Exception as e:
                    print(f"    ⚠ 获取商圈列表失败：{e}")
            
            if not bizcircles_list:
                print(f"  ⚠ {district_cn} 未获取到商圈列表，跳过")
                continue
            
            start_idx = current_bizcircle_idx if current_district == district_cn else 0
            bizcircles_to_crawl = bizcircles_list[start_idx:start_idx + TARGET_BIZCIRCLES_PER_DISTRICT]
            
            for idx, (bizcircle_name, bizcircle_code) in enumerate(bizcircles_to_crawl, start=start_idx):
                print(f"\n  [{district_cn}] 商圈 {idx+1}/{len(bizcircles_list)}: {bizcircle_name} ({bizcircle_code})")
                
                empty_page_count = 0  # 连续空页计数器
                
                for page in range(START_PAGE, MAX_PAGES_PER_BIZCIRCLE + 1):
                    url = get_bizcircle_page_url(district_slug, bizcircle_code, page)
                    
                    try:
                        html = fetch_html_or_handle(session, url, f"{district_cn}_{bizcircle_name}", page, all_data, stats)
                    except EndOfDistrict:
                        print(f"    ✅ {bizcircle_name} 第{page}页已无更多成交记录")
                        break
                    except Exception as e:
                        print(f"    ⚠ 第{page}页请求失败：{e}")
                        break
                    
                    rows = parse_bizcircle_deals(html, bizcircle_name, district_cn)
                    if not rows:
                        empty_page_count += 1
                        print(f"    ℹ 第{page}页解析不到数据（连续空页: {empty_page_count}/{MAX_EMPTY_PAGES}）")
                        
                        if empty_page_count >= MAX_EMPTY_PAGES:
                            print(f"    ⛔ 连续{MAX_EMPTY_PAGES}页无数据，停止该商圈")
                            break
                        
                        polite_sleep()
                        continue  # 继续爬取下一页
                    
                    # 有数据，重置空页计数器
                    empty_page_count = 0
                    
                    # 检查年份过滤
                    has_old_data = False  # 是否遇到早于MIN_YEAR的数据
                    added = 0
                    filtered_by_year = 0
                    
                    for r in rows:
                        # 检查年份
                        deal_date = r.get("deal_date")
                        if deal_date:
                            try:
                                deal_year = int(deal_date.split("-")[0])
                                
                                # 如果早于MIN_YEAR，标记并停止该商圈
                                if deal_year < MIN_YEAR:
                                    has_old_data = True
                                    continue
                                
                                # 如果晚于MAX_YEAR，跳过但继续
                                if deal_year > MAX_YEAR:
                                    filtered_by_year += 1
                                    continue
                            except Exception:
                                pass  # 日期解析失败，保留该数据
                        
                        # 去重
                        hid = r.get("house_id") or r.get("detail_url")
                        if hid and hid in seen:
                            continue
                        if hid:
                            seen.add(hid)
                        
                        all_data.append(r)
                        stats[district_cn] += 1
                        added += 1
                    
                    # 输出统计信息
                    if filtered_by_year > 0:
                        print(f"    第 {page} 页：解析 {len(rows)} 条，过滤 {filtered_by_year} 条（超出年份），新增 {added} 条，累计 {stats[district_cn]} 条")
                    else:
                        print(f"    第 {page} 页：解析 {len(rows)} 条，新增 {added} 条，累计 {stats[district_cn]} 条")
                    
                    # 如果遇到早于MIN_YEAR的数据，停止该商圈
                    if has_old_data:
                        print(f"    ⏹ 检测到 {MIN_YEAR} 年之前的数据，停止该商圈")
                        break
                    
                    if page % SAVE_EVERY_PAGES == 0:
                        save_data(all_data)
                        ck_data = {
                            "current_district": district_cn,
                            "current_bizcircle_idx": idx,
                            "current_page": page + 1,
                            "stats": stats,
                        }
                        atomic_write_json(CHECKPOINT_FILE, ck_data)
                    
                    polite_sleep()
                
                save_data(all_data)
            
            current_district = None
            current_bizcircle_idx = 0
            save_data(all_data)
            atomic_write_json(CHECKPOINT_FILE, {"stats": stats})
    
    except KeyboardInterrupt:
        print("\n⚠ 检测到 Ctrl+C 打断：正在保存数据与断点...")
        save_data(all_data)
        print("✅ 已保存。下次直接重新运行脚本即可断点续爬。")
        return
    
    print("\n" + "=" * 60)
    print("🎉 爬取完成")
    print("=" * 60)
    print("各区数量：", stats)
    print(f"总计：{sum(stats.values())} 条")
    print(f"输出文件：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
