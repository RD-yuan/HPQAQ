import json
import os
import re
from datetime import datetime
from app import app, db, City, Transaction, Region

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))

# 城市名称映射
CITY_NAMES = {
    "beijing": "北京", "bj": "北京",
    "shanghai": "上海", "sh": "上海",
    "guangzhou": "广州", "gz": "广州",
    "shenzhen": "深圳", "sz": "深圳",
    "tianjin": "天津", "tj": "天津",
    "taibei": "台北",
    "xinbei": "新北"
}

def parse_price(val):
    """处理价格，移除可能的非数字字符"""
    if val is None or val == "":
        return 0
    try:
        return float(val)
    except:
        return 0

def import_json_file(filepath):
    filename = os.path.basename(filepath)
    # 从文件名提取城市代码 (如 crawl_history_beijing.json -> beijing)
    match = re.match(r"crawl_history_([a-zA-Z]+)\.json", filename)
    if not match:
        print(f"Skipping {filename}: name format not match")
        return

    city_code_raw = match.group(1).lower()
    # 统一化城市代码 (beijing -> bj)
    city_code = "bj" if city_code_raw == "beijing" else city_code_raw
    city_code = "sh" if city_code_raw == "shanghai" else city_code
    city_code = "gz" if city_code_raw == "guangzhou" else city_code
    city_code = "sz" if city_code_raw == "shenzhen" else city_code
    
    city_name = CITY_NAMES.get(city_code, city_code)

    print(f"Importing {city_name} ({city_code}) from {filename}...")

    with app.app_context():
        # 1. 确保城市存在
        city = City.query.filter_by(code=city_code).first()
        if not city:
            city = City(code=city_code, name=city_name)
            db.session.add(city)
            db.session.commit()
            print(f"Created city: {city_name}")

        # 2. 读取数据
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return

        if isinstance(data, dict): 
            data = data.get("data", []) or data.get("items", [])
        
        if not isinstance(data, list):
            print("Data format error: expected list")
            return

        # 3. 批量插入
        count = 0
        for item in data:
            # 必须有 house_id
            house_id = str(item.get("house_id", ""))
            if not house_id:
                continue

            # 检查是否已存在 (避免重复)
            exists = Transaction.query.filter_by(house_id=house_id).first()
            if exists:
                continue

            # 尝试解析日期
            deal_date_str = item.get("deal_date")
            deal_date = None
            if deal_date_str:
                try:
                    deal_date = datetime.strptime(deal_date_str, "%Y-%m-%d").date()
                except:
                    pass

            trans = Transaction(
                city_code=city_code,
                region_name=item.get("region"),
                bizcircle=item.get("bizcircle"),
                community=item.get("community"),
                layout=item.get("layout"),
                total_price_wan=parse_price(item.get("total_price_wan")),
                unit_price_yuan_sqm=parse_price(item.get("unit_price_yuan_sqm")),
                area_sqm=parse_price(item.get("area_sqm")),
                deal_date=deal_date,
                house_id=house_id,
                orientation=item.get("orientation"),
                building_year=item.get("building_year"),
                floor=item.get("floor"),
                detail_url=item.get("detail_url")
            )
            db.session.add(trans)
            count += 1
            
            # 每 100 条提交一次，防止内存溢出
            if count % 100 == 0:
                db.session.commit()
                print(f"Imported {count} records...")

        db.session.commit()
        print(f"Finished {city_name}: added {count} new records.")

def main():
    # 首次运行时创建表
    with app.app_context():
        db.create_all()
        print("Database initialized.")

    if not os.path.exists(DATA_DIR):
        print(f"Data directory not found: {DATA_DIR}")
        return

    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json") and fn.startswith("crawl_history_"):
            import_json_file(os.path.join(DATA_DIR, fn))

if __name__ == "__main__":
    main()