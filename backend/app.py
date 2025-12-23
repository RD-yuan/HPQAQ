import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# === 配置部分 ===
# 请将 password 替换为您在数据库中设置的密码
DB_USER = 'hp_user'
DB_PASS = '123456'
DB_HOST = '127.0.0.1'
DB_NAME = 'house_price_db'

app = Flask(__name__)
# 使用 pymysql 连接 MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
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
    
    # === 字段长度配置 (与导入时保持一致) ===
    bizcircle = db.Column(db.String(100), index=True)
    community = db.Column(db.String(500), index=True) # 500 长度
    layout = db.Column(db.String(50))
    
    total_price_wan = db.Column(db.Numeric(10, 2))
    unit_price_yuan_sqm = db.Column(db.Integer)
    area_sqm = db.Column(db.Numeric(10, 2))
    
    deal_date = db.Column(db.Date, index=True)
    
    house_id = db.Column(db.String(100), unique=True)
    orientation = db.Column(db.String(50))
    building_year = db.Column(db.String(20))
    floor = db.Column(db.String(50))
    detail_url = db.Column(db.String(500)) # 500 长度
    crawl_time = db.Column(db.DateTime, default=datetime.now)

# === 辅助路径 ===
FRONTEND_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

# === API 接口 ===

@app.get("/api/health")
def health():
    """
    前端初始化时调用此接口获取城市列表。
    必须从数据库查询 City 表返回给前端。
    """
    try:
        cities = City.query.order_by(City.code).all()
        return jsonify({
            "ok": True,
            "db": "mysql",
            "cities": [c.code for c in cities] # 返回 ['xinbei']
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/cities")
def get_cities():
    cities = City.query.order_by(City.code).all()
    return jsonify({"cities": [c.code for c in cities]})

@app.get("/api/listings")
def get_listings():
    """获取成交列表"""
    city_code = request.args.get("city", "").strip().lower()
    if not city_code:
        return jsonify({"error": "missing_city"}), 400

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    
    # 构造查询
    query = Transaction.query.filter_by(city_code=city_code)
    
    # 筛选
    if region := request.args.get("region"):
        query = query.filter(Transaction.region_name == region)
    if bizcircle := request.args.get("bizcircle"):
        query = query.filter(Transaction.bizcircle == bizcircle)
    if community := request.args.get("community"):
        query = query.filter(Transaction.community.contains(community))
    if layout := request.args.get("layout"):
        query = query.filter(Transaction.layout == layout)

    # 排序
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

@app.get("/api/price_trend")
def get_price_trend():
    """获取价格走势"""
    city_code = request.args.get("city", "").strip().lower()
    if not city_code:
        return jsonify({"error": "missing_city"}), 400

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

# === 静态文件托管 ===
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if path.startswith("api"):
        return jsonify({"error": "not_found"}), 404
    if path == "":
        return send_from_directory(FRONTEND_DIR, "index.html")
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)