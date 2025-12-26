"""
历史均价统计模块
提供按城市、商圈统计 2023-2025 年度历史均价的功能
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import func, extract, and_
from sqlalchemy.exc import SQLAlchemyError


def _parse_date_any(s):
    """解析多种日期格式"""
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
    """安全转换为浮点数"""
    if x is None or x == "":
        return default
    try:
        return float(x)
    except Exception:
        return default


def _as_int(x, default=0):
    """安全转换为整数"""
    if x is None or x == "":
        return default
    try:
        return int(float(x))
    except Exception:
        return default


def get_historical_avg_price_from_db(
    db_session,
    Transaction,
    city_code: str,
    bizcircle: Optional[str] = None,
    start_month: str = "2023-01",
    end_month: str = "2025-12"
) -> List[Dict]:
    """
    从 MySQL 数据库统计历史均价（按年度）
    
    Args:
        db_session: SQLAlchemy session
        Transaction: Transaction 模型类
        city_code: 城市代码
        bizcircle: 商圈名称（可选）
        start_month: 起始月份（格式：YYYY-MM）
        end_month: 结束月份（格式：YYYY-MM）
    
    Returns:
        [{"year": 2023, "avg_unit_price": 50000, "avg_total_price": 300.5, "count": 1234}, ...]
    """
    try:
        # 解析月份参数
        start_year = int(start_month.split("-")[0])
        end_year = int(end_month.split("-")[0])
        
        query = db_session.query(
            extract('year', Transaction.deal_date).label('year'),
            extract('month', Transaction.deal_date).label('month'),
            func.avg(Transaction.unit_price_yuan_sqm).label('avg_unit'),
            func.avg(Transaction.total_price_wan).label('avg_total'),
            func.count(Transaction.id).label('count')
        ).filter(
            and_(
                Transaction.city_code == city_code,
                Transaction.deal_date.isnot(None),
                Transaction.deal_date >= datetime.strptime(start_month + "-01", "%Y-%m-%d").date(),
                Transaction.deal_date <= datetime.strptime(end_month + "-01", "%Y-%m-%d").date()
            )
        )
        
        if bizcircle:
            query = query.filter(Transaction.bizcircle == bizcircle)
        
        rows = query.group_by('year', 'month').order_by('year', 'month').all()
        
        result = []
        for r in rows:
            year = int(r.year) if r.year else 0
            month = int(r.month) if r.month else 1
            result.append({
                "year": year,
                "month": month,
                "year_month": f"{year}-{month:02d}",
                "avg_unit_price_yuan_sqm": int(r.avg_unit) if r.avg_unit else 0,
                "avg_total_price_wan": round(float(r.avg_total), 2) if r.avg_total else 0.0,
                "count": r.count
            })
        
        return result
    
    except SQLAlchemyError as e:
        print(f"[statistics] DB query error: {e}")
        return []


def get_historical_avg_price_from_json(
    data_dir: Path,
    city_json_map: Dict[str, str],
    city_code: str,
    bizcircle: Optional[str] = None,
    start_month: str = "2023-01",
    end_month: str = "2025-12"
) -> List[Dict]:
    """
    从 JSON 文件统计历史均价（按年度）
    
    Args:
        data_dir: data 目录路径
        city_json_map: 城市代码到 JSON 文件名的映射
        city_code: 城市代码
        bizcircle: 商圈名称（可选）
        start_month: 起始月份（格式：YYYY-MM）
        end_month: 结束月份（格式：YYYY-MM）
    
    Returns:
        [{"year": 2023, "avg_unit_price": 50000, "avg_total_price": 300.5, "count": 1234}, ...]
    """
    # 解析月份参数
    start_year = int(start_month.split("-")[0])
    start_month_num = int(start_month.split("-")[1])
    end_year = int(end_month.split("-")[0])
    end_month_num = int(end_month.split("-")[1])
    
    city_code = (city_code or "").strip().lower()
    filename = city_json_map.get(city_code, f"crawl_history_{city_code}.json")
    path = data_dir / filename
    
    if not path.exists():
        return []
    
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        
        if isinstance(obj, list):
            items = obj
        elif isinstance(obj, dict):
            items = obj.get("items") or obj.get("data") or []
        else:
            items = []
        
        # 按月度分桶统计
        month_buckets = {}  # {year_month: {"sum_unit": ..., "sum_total": ..., "count": ...}}
        
        for raw in items:
            if not isinstance(raw, dict):
                continue
            
            # 过滤商圈
            if bizcircle and raw.get("bizcircle") != bizcircle:
                continue
            
            # 解析日期
            deal_date = raw.get("deal_date")
            d_obj = _parse_date_any(deal_date)
            if not d_obj:
                continue
            
            year = d_obj.year
            month = d_obj.month
            
            # 过滤月份范围
            if year < start_year or year > end_year:
                continue
            if year == start_year and month < start_month_num:
                continue
            if year == end_year and month > end_month_num:
                continue
            
            # 提取价格
            unit_price = _as_int(raw.get("unit_price_yuan_sqm"), 0)
            total_price = _as_float(raw.get("total_price_wan"), 0.0)
            
            # 累加到对应年月
            year_month = f"{year}-{month:02d}"
            if year_month not in month_buckets:
                month_buckets[year_month] = {"year": year, "month": month, "sum_unit": 0, "sum_total": 0.0, "count": 0}
            
            bucket = month_buckets[year_month]
            bucket["sum_unit"] += unit_price
            bucket["sum_total"] += total_price
            bucket["count"] += 1
        
        # 计算均价
        result = []
        for year_month in sorted(month_buckets.keys()):
            bucket = month_buckets[year_month]
            cnt = bucket["count"]
            if cnt > 0:
                result.append({
                    "year": bucket["year"],
                    "month": bucket["month"],
                    "year_month": year_month,
                    "avg_unit_price_yuan_sqm": int(bucket["sum_unit"] / cnt),
                    "avg_total_price_wan": round(bucket["sum_total"] / cnt, 2),
                    "count": cnt
                })
        
        return result
    
    except Exception as e:
        print(f"[statistics] JSON parse error for {city_code}: {e}")
        return []


def get_available_bizcircles_from_db(
    db_session,
    Transaction,
    city_code: str
) -> List[str]:
    """从数据库获取指定城市的所有商圈列表"""
    try:
        rows = db_session.query(Transaction.bizcircle).filter(
            and_(
                Transaction.city_code == city_code,
                Transaction.bizcircle.isnot(None),
                Transaction.bizcircle != ''
            )
        ).distinct().order_by(Transaction.bizcircle).all()
        
        return [r.bizcircle for r in rows if r.bizcircle]
    
    except SQLAlchemyError as e:
        print(f"[statistics] DB query error: {e}")
        return []


def get_available_bizcircles_from_json(
    data_dir: Path,
    city_json_map: Dict[str, str],
    city_code: str
) -> List[str]:
    """从 JSON 文件获取指定城市的所有商圈列表"""
    city_code = (city_code or "").strip().lower()
    filename = city_json_map.get(city_code, f"crawl_history_{city_code}.json")
    path = data_dir / filename
    
    if not path.exists():
        return []
    
    try:
        with path.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        
        if isinstance(obj, list):
            items = obj
        elif isinstance(obj, dict):
            items = obj.get("items") or obj.get("data") or []
        else:
            items = []
        
        bizcircles = set()
        for raw in items:
            if isinstance(raw, dict):
                biz = raw.get("bizcircle")
                if biz and biz.strip():
                    bizcircles.add(biz.strip())
        
        return sorted(list(bizcircles))
    
    except Exception as e:
        print(f"[statistics] JSON parse error for {city_code}: {e}")
        return []
