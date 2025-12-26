import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
import statistics

# === 配置部分 ===
DB_USER = 'hp_user'
DB_PASS = '123456'
DB_HOST = '127.0.0.1'
DB_NAME = 'house_price_db'

app = Flask(__name__)

# 使用 pymysql 连接 MySQL（数据库可用时走这个；不可用则自动回退 JSON）
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)

# === 数据模型 (Model) ===
class City(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, index=True)
    name = db.Column(db.String(50))

class Region(db.Model):
    __tablename__ = 'regions'
    id = db.Column(db.Integer, primary_key=True)
    city_code = db.Column(db.String(20), db.ForeignKey('cities.code'), index=True)
    name = db.Column(db.String(50))

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    city_code = db.Column(db.String(20), db.ForeignKey('cities.code'), index=True)
    region_name = db.Column(db.String(50), index=True)

    bizcircle = db.Column(db.String(100), index=True)
    community = db.Column(db.String(500), index=True)
    layout = db.Column(db.String(50))

    total_price_wan = db.Column(db.Numeric(10, 2))
    unit_price_yuan_sqm = db.Column(db.Integer)
    area_sqm = db.Column(db.Numeric(10, 2))

    deal_date = db.Column(db.Date, index=True)

    house_id = db.Column(db.String(100), unique=True)
    orientation = db.Column(db.String(50))
    building_year = db.Column(db.String(20))
    floor = db.Column(db.String(50))
    detail_url = db.Column(db.String(500))
    crawl_time = db.Column(db.DateTime, default=datetime.now)

# === JSON 回退数据源 ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

CITY_JSON_MAP = {
    "beijing": "crawl_history_beijing.json",
    "shanghai": "crawl_history_shanghai.json",
    "guangzhou": "crawl_history_guangzhou.json",
    "shenzhen": "crawl_history_shenzhen.json",
    "tianjin": "crawl_history_tianjin.json",
    "taibei": "crawl_history_taibei.json",
    "xinbei": "crawl_history_xinbei.json",
}

def db_is_available() -> bool:
    """
    探测数据库是否可用：
    - MySQL 没安装/没启动/端口拒绝/驱动缺失 -> 返回 False
    - MySQL 正常 -> True
    """
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
        return False

def _parse_date_any(s):
    if not s:
        return None
    if isinstance(s, datetime):
        return s.date()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(s), fmt).date()
        except ValueError:
            continue
    return None

def _as_float(x, default=0.0):
    if x is None or x == "":
        return default
    try:
        return float(x)
    except Exception:
        return default

def _as_int(x, default=0):
    if x is None or x == "":
        return default
    try:
        return int(float(x))
    except Exception:
        return default

def load_city_items_from_json(city_code: str):
    """从 data/crawl_history_xxx.json 读取数据列表"""
    city_code = (city_code or "").strip().lower()
    filename = CITY_JSON_MAP.get(city_code, f"crawl_history_{city_code}.json")
    path = DATA_DIR / filename

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)

    # 兼容：可能是 list，也可能是 {"items":[...]} / {"data":[...]}
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        if isinstance(obj.get("items"), list):
            return obj["items"]
        if isinstance(obj.get("data"), list):
            return obj["data"]
    return []

def normalize_item(raw: dict):
    """
    把 JSON 记录归一为前端需要的输出结构。
    你给的 JSON 样例字段已完全匹配这里。
    """
    if not isinstance(raw, dict):
        raw = {}

    deal_date = raw.get("deal_date")
    d_obj = _parse_date_any(deal_date)

    return {
        "house_id": raw.get("house_id"),
        "region": raw.get("region") or raw.get("region_name"),
        "bizcircle": raw.get("bizcircle"),
        "community": raw.get("community"),
        "layout": raw.get("layout"),
        "area_sqm": _as_float(raw.get("area_sqm"), 0.0),
        "total_price_wan": _as_float(raw.get("total_price_wan"), 0.0),
        "unit_price_yuan_sqm": _as_int(raw.get("unit_price_yuan_sqm"), 0),
        "deal_date": d_obj.isoformat() if d_obj else (str(deal_date) if deal_date else None),
        "detail_url": raw.get("detail_url"),
        "orientation": raw.get("orientation"),
        "building_year": raw.get("building_year"),
        "floor": raw.get("floor"),
        "_deal_date_obj": d_obj,
    }

# === 辅助路径 ===
FRONTEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# === API 接口 ===
@app.get("/api/health")
def health():
    """
    前端初始化时调用此接口获取城市列表：
    - DB 可用：从 City 表读取
    - DB 不可用：从 CITY_JSON_MAP 返回
    """
    try:
        if db_is_available():
            cities = City.query.order_by(City.code).all()
            return jsonify({
                "ok": True,
                "db": "mysql",
                "cities": [c.code for c in cities]
            })
        else:
            return jsonify({
                "ok": True,
                "db": "json",
                "cities": sorted(CITY_JSON_MAP.keys())
            })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/cities")
def get_cities():
    if db_is_available():
        cities = City.query.order_by(City.code).all()
        return jsonify({"cities": [c.code for c in cities]})
    return jsonify({"cities": sorted(CITY_JSON_MAP.keys())})

@app.get("/api/listings")
def get_listings():
    """获取成交列表（DB 可用走 DB，不可用走 JSON）"""
    city_code = request.args.get("city", "").strip().lower()
    if not city_code:
        return jsonify({"error": "missing_city"}), 400

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)

    # --- 1) DB 可用：原 ORM 查询 ---
    if db_is_available():
        query = Transaction.query.filter_by(city_code=city_code)

        if region := request.args.get("region"):
            query = query.filter(Transaction.region_name == region)
        if bizcircle := request.args.get("bizcircle"):
            query = query.filter(Transaction.bizcircle == bizcircle)
        if community := request.args.get("community"):
            query = query.filter(Transaction.community.contains(community))
        if layout := request.args.get("layout"):
            query = query.filter(Transaction.layout == layout)

        query = query.order_by(Transaction.deal_date.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        items = []
        for item in pagination.items:
            items.append({
                "house_id": item.house_id,
                "region": item.region_name,
                "bizcircle": item.bizcircle,
                "community": item.community,
                "layout": item.layout,
                "area_sqm": float(item.area_sqm) if item.area_sqm else 0,
                "total_price_wan": float(item.total_price_wan) if item.total_price_wan else 0,
                "unit_price_yuan_sqm": item.unit_price_yuan_sqm,
                "deal_date": item.deal_date.isoformat() if item.deal_date else None,
                "detail_url": item.detail_url,
                "orientation": item.orientation,
                "building_year": item.building_year,
                "floor": item.floor
            })

        return jsonify({
            "items": items,
            "total": pagination.total,
            "page": page,
            "page_size": page_size
        })

    # --- 2) DB 不可用：JSON 回退 ---
    raw_items = load_city_items_from_json(city_code)
    items = [normalize_item(r) for r in raw_items]

    # 过滤（按你的接口参数）
    if region := request.args.get("region"):
        items = [x for x in items if (x.get("region") or "") == region]
    if bizcircle := request.args.get("bizcircle"):
        items = [x for x in items if (x.get("bizcircle") or "") == bizcircle]
    if community := request.args.get("community"):
        items = [x for x in items if community in (x.get("community") or "")]
    if layout := request.args.get("layout"):
        items = [x for x in items if (x.get("layout") or "") == layout]

    # 排序：按 deal_date 倒序
    items.sort(key=lambda x: x.get("_deal_date_obj") or datetime.min.date(), reverse=True)

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    # 去掉内部字段
    for x in page_items:
        x.pop("_deal_date_obj", None)

    return jsonify({
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size
    })

@app.get("/api/price_trend")
def get_price_trend():
    """获取价格走势（DB 可用走 DB，不可用走 JSON）"""
    city_code = request.args.get("city", "").strip().lower()
    if not city_code:
        return jsonify({"error": "missing_city"}), 400

    # --- 1) DB 可用：原 MySQL 聚合 ---
    if db_is_available():
        query = db.session.query(
            func.date_format(Transaction.deal_date, '%Y-%m').label('month'),
            func.avg(Transaction.unit_price_yuan_sqm).label('avg_unit'),
            func.avg(Transaction.total_price_wan).label('avg_total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.city_code == city_code,
            Transaction.deal_date.isnot(None)
        )

        if region := request.args.get("region"):
            query = query.filter(Transaction.region_name == region)
        if bizcircle := request.args.get("bizcircle"):
            query = query.filter(Transaction.bizcircle == bizcircle)

        rows = query.group_by('month').order_by('month').all()

        points = []
        for r in rows:
            points.append({
                "month": r.month,
                "avg_unit_price_yuan_sqm": int(r.avg_unit) if r.avg_unit else 0,
                "avg_total_price_wan": round(float(r.avg_total), 2) if r.avg_total else 0,
                "count": r.count
            })

        return jsonify({"points": points})

    # --- 2) DB 不可用：JSON 回退聚合 ---
    raw_items = load_city_items_from_json(city_code)
    items = [normalize_item(r) for r in raw_items]

    if region := request.args.get("region"):
        items = [x for x in items if (x.get("region") or "") == region]
    if bizcircle := request.args.get("bizcircle"):
        items = [x for x in items if (x.get("bizcircle") or "") == bizcircle]

    bucket = {}  # month -> {"sum_unit":..., "sum_total":..., "count":...}
    for x in items:
        d = x.get("_deal_date_obj")
        if not d:
            continue
        month = d.strftime("%Y-%m")
        b = bucket.setdefault(month, {"sum_unit": 0, "sum_total": 0.0, "count": 0})
        b["sum_unit"] += _as_int(x.get("unit_price_yuan_sqm"), 0)
        b["sum_total"] += _as_float(x.get("total_price_wan"), 0.0)
        b["count"] += 1

    points = []
    for month in sorted(bucket.keys()):
        b = bucket[month]
        cnt = b["count"] or 1
        points.append({
            "month": month,
            "avg_unit_price_yuan_sqm": int(b["sum_unit"] / cnt),
            "avg_total_price_wan": round(b["sum_total"] / cnt, 2),
            "count": b["count"]
        })

    return jsonify({"points": points})

@app.get("/api/historical_avg_price")
def get_historical_avg_price():
    """
    获取历史均价统计（按年度或月度）
    查询参数：
    - city: 城市代码（必填）
    - bizcircle: 商圈名称（可选）
    - start_year: 起始年份（默认 2023）- 兼容旧版
    - end_year: 结束年份（默认 2025）- 兼容旧版
    - start_month: 起始月份（格式：YYYY-MM）- 新版
    - end_month: 结束月份（格式：YYYY-MM）- 新版
    """
    city_code = request.args.get("city", "").strip().lower()
    if not city_code:
        return jsonify({"error": "missing_city"}), 400
    
    bizcircle = request.args.get("bizcircle", "").strip() or None
    
    # 优先使用月份参数，如果没有则使用年份参数（兼容旧版）
    start_month = request.args.get("start_month", "").strip()
    end_month = request.args.get("end_month", "").strip()
    
    if start_month and end_month:
        # 使用月份参数
        if start_month > end_month:
            return jsonify({"error": "invalid_month_range"}), 400
        start_year = int(start_month.split("-")[0])
        end_year = int(end_month.split("-")[0])
    else:
        # 使用年份参数（兼容旧版）
        start_year = request.args.get("start_year", 2023, type=int)
        end_year = request.args.get("end_year", 2025, type=int)
        start_month = f"{start_year}-01"
        end_month = f"{end_year}-12"
        
        if start_year > end_year:
            return jsonify({"error": "invalid_year_range"}), 400
    
    # --- 1) DB 可用：从数据库统计 ---
    if db_is_available():
        result = statistics.get_historical_avg_price_from_db(
            db.session,
            Transaction,
            city_code,
            bizcircle,
            start_month,
            end_month
        )
        return jsonify({
            "ok": True,
            "source": "mysql",
            "city": city_code,
            "bizcircle": bizcircle,
            "data": result
        })
    
    # --- 2) DB 不可用：从 JSON 统计 ---
    result = statistics.get_historical_avg_price_from_json(
        DATA_DIR,
        CITY_JSON_MAP,
        city_code,
        bizcircle,
        start_month,
        end_month
    )
    return jsonify({
        "ok": True,
        "source": "json",
        "city": city_code,
        "bizcircle": bizcircle,
        "data": result
    })

@app.get("/api/bizcircles")
def get_bizcircles():
    """
    获取指定城市的所有商圈列表
    查询参数：
    - city: 城市代码（必填）
    """
    city_code = request.args.get("city", "").strip().lower()
    if not city_code:
        return jsonify({"error": "missing_city"}), 400
    
    # --- 1) DB 可用：从数据库获取 ---
    if db_is_available():
        bizcircles = statistics.get_available_bizcircles_from_db(
            db.session,
            Transaction,
            city_code
        )
        return jsonify({
            "ok": True,
            "source": "mysql",
            "city": city_code,
            "bizcircles": bizcircles
        })
    
    # --- 2) DB 不可用：从 JSON 获取 ---
    bizcircles = statistics.get_available_bizcircles_from_json(
        DATA_DIR,
        CITY_JSON_MAP,
        city_code
    )
    return jsonify({
        "ok": True,
        "source": "json",
        "city": city_code,
        "bizcircles": bizcircles
    })

# === 静态文件托管 ===
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if path.startswith("api"):
        return jsonify({"error": "not_found"}), 404
    if path == "":
        return send_from_directory(FRONTEND_DIR, "init.html")
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
