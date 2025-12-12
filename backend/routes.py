from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app import get_db, app
from models import House
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1", tags=["房源数据"])

# 房源列表接口
@router.get("/houses", response_model=Dict[str, Any])
def get_houses(
    city: str = Query(None, description="城市名称"),
    district: str = Query(None, description="区域"),
    min_price: float = Query(None, description="最低总价（万元）"),
    max_price: float = Query(None, description="最高总价（万元）"),
    min_area: float = Query(None, description="最小面积（平方米）"),
    max_area: float = Query(None, description="最大面积（平方米）"),
    house_type: str = Query(None, description="户型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取房源列表，支持多条件筛选和分页"""
    try:
        # 构建查询条件
        query = db.query(House)
        
        if city:
            query = query.filter(func.lower(House.city) == func.lower(city))
        if district:
            query = query.filter(func.lower(House.district) == func.lower(district))
        if min_price:
            query = query.filter(House.total_price >= min_price)
        if max_price:
            query = query.filter(House.total_price <= max_price)
        if min_area:
            query = query.filter(House.area >= min_area)
        if max_area:
            query = query.filter(House.area <= max_area)
        if house_type:
            query = query.filter(House.house_type.like(f"%{house_type}%"))
        
        # 计算总数
        total_count = query.count()
        
        # 分页
        houses = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 格式化返回数据
        houses_list = []
        for house in houses:
            houses_list.append({
                "id": house.id,
                "title": house.title,
                "city": house.city,
                "district": house.district,
                "street": house.street,
                "community": house.community,
                "total_price": house.total_price,
                "unit_price": house.unit_price,
                "house_type": house.house_type,
                "area": house.area,
                "orientation": house.orientation,
                "floor": house.floor,
                "building_year": house.building_year,
                "renovation": house.renovation,
                "elevator": house.elevator,
                "tags": house.tags,
                "url": house.url,
                "crawl_time": house.crawl_time.isoformat() if house.crawl_time else None
            })
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size,
                "houses": houses_list
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取房源列表失败: {str(e)}")

# 房源详情接口
@router.get("/houses/{house_id}", response_model=Dict[str, Any])
def get_house_detail(house_id: str, db: Session = Depends(get_db)):
    """获取单个房源的详细信息"""
    try:
        house = db.query(House).filter(House.id == house_id).first()
        
        if not house:
            raise HTTPException(status_code=404, detail="房源不存在")
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "id": house.id,
                "title": house.title,
                "city": house.city,
                "district": house.district,
                "street": house.street,
                "community": house.community,
                "total_price": house.total_price,
                "unit_price": house.unit_price,
                "house_type": house.house_type,
                "area": house.area,
                "orientation": house.orientation,
                "floor": house.floor,
                "building_year": house.building_year,
                "renovation": house.renovation,
                "house_structure": house.house_structure,
                "elevator": house.elevator,
                "longitude": house.longitude,
                "latitude": house.latitude,
                "property_right": house.property_right,
                "house_usage": house.house_usage,
                "property_years": house.property_years,
                "tags": house.tags,
                "url": house.url,
                "crawl_time": house.crawl_time.isoformat() if house.crawl_time else None,
                "update_time": house.update_time.isoformat() if house.update_time else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取房源详情失败: {str(e)}")

# 城市统计接口
@router.get("/statistics/cities", response_model=Dict[str, Any])
def get_city_statistics(db: Session = Depends(get_db)):
    """获取各城市的房源统计数据"""
    try:
        # 按城市分组统计
        city_stats = db.query(
            House.city,
            func.count(House.id).label("total_count"),
            func.avg(House.total_price).label("avg_total_price"),
            func.avg(House.unit_price).label("avg_unit_price"),
            func.min(House.total_price).label("min_total_price"),
            func.max(House.total_price).label("max_total_price"),
            func.avg(House.area).label("avg_area")
        ).group_by(House.city).all()
        
        # 格式化返回数据
        result = []
        for city_stat in city_stats:
            result.append({
                "city": city_stat.city,
                "total_count": city_stat.total_count,
                "avg_total_price": round(city_stat.avg_total_price, 2) if city_stat.avg_total_price else None,
                "avg_unit_price": round(city_stat.avg_unit_price, 0) if city_stat.avg_unit_price else None,
                "min_total_price": round(city_stat.min_total_price, 2) if city_stat.min_total_price else None,
                "max_total_price": round(city_stat.max_total_price, 2) if city_stat.max_total_price else None,
                "avg_area": round(city_stat.avg_area, 2) if city_stat.avg_area else None
            })
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取城市统计数据失败: {str(e)}")

# 价格走势接口
@router.get("/statistics/price-trend", response_model=Dict[str, Any])
def get_price_trend(
    city: str = Query(..., description="城市名称"),
    months: int = Query(3, ge=1, le=36, description="查询月数"),
    db: Session = Depends(get_db)
):
    """获取指定城市的价格走势"""
    try:
        # 计算开始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # 查询每月平均价格
        trend_data = db.query(
            func.date_format(func.date(House.crawl_time), "%Y-%m").label("month"),
            func.avg(House.total_price).label("avg_total_price"),
            func.avg(House.unit_price).label("avg_unit_price"),
            func.count(House.id).label("total_count")
        ).filter(
            and_(
                func.lower(House.city) == func.lower(city),
                House.crawl_time >= start_date,
                House.crawl_time <= end_date
            )
        ).group_by(func.date_format(func.date(House.crawl_time), "%Y-%m")).order_by("month").all()
        
        # 格式化返回数据
        result = []
        for trend in trend_data:
            result.append({
                "month": trend.month,
                "avg_total_price": round(trend.avg_total_price, 2) if trend.avg_total_price else None,
                "avg_unit_price": round(trend.avg_unit_price, 0) if trend.avg_unit_price else None,
                "total_count": trend.total_count
            })
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取价格走势失败: {str(e)}")

# 区域统计接口
@router.get("/statistics/districts", response_model=Dict[str, Any])
def get_district_statistics(
    city: str = Query(..., description="城市名称"),
    db: Session = Depends(get_db)
):
    """获取指定城市各区域的房源统计数据"""
    try:
        # 按区域分组统计
        district_stats = db.query(
            House.district,
            func.count(House.id).label("total_count"),
            func.avg(House.total_price).label("avg_total_price"),
            func.avg(House.unit_price).label("avg_unit_price")
        ).filter(
            func.lower(House.city) == func.lower(city)
        ).group_by(House.district).order_by(func.count(House.id).desc()).all()
        
        # 格式化返回数据
        result = []
        for district_stat in district_stats:
            result.append({
                "district": district_stat.district,
                "total_count": district_stat.total_count,
                "avg_total_price": round(district_stat.avg_total_price, 2) if district_stat.avg_total_price else None,
                "avg_unit_price": round(district_stat.avg_unit_price, 0) if district_stat.avg_unit_price else None
            })
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取区域统计数据失败: {str(e)}")

# 注册路由
app.include_router(router)
