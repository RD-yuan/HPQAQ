from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class House(Base):
    __tablename__ = 'houses'
    
    id = Column(String(50), primary_key=True, comment='房源唯一ID')
    title = Column(String(200), nullable=False, comment='房源标题')
    city = Column(String(20), nullable=False, comment='所在城市')
    district = Column(String(50), comment='区域')
    street = Column(String(100), comment='街道')
    community = Column(String(100), comment='小区名称')
    
    # 价格信息
    total_price = Column(Float, nullable=False, comment='总价（万元）')
    unit_price = Column(Integer, comment='单价（元/平方米）')
    
    # 房屋基本信息
    house_type = Column(String(20), comment='户型')
    area = Column(Float, comment='建筑面积（平方米）')
    orientation = Column(String(20), comment='朝向')
    floor = Column(String(20), comment='楼层')
    building_year = Column(Integer, comment='建筑年代')
    renovation = Column(String(20), comment='装修情况')
    house_structure = Column(String(20), comment='房屋结构')
    elevator = Column(Boolean, comment='是否有电梯')
    
    # 位置信息
    longitude = Column(Float, comment='经度')
    latitude = Column(Float, comment='纬度')
    
    # 其他信息
    property_right = Column(String(50), comment='产权信息')
    house_usage = Column(String(50), comment='房屋用途')
    property_years = Column(Integer, comment='产权年限')
    
    # 房源详情
    description = Column(Text, comment='房源描述')
    tags = Column(String(200), comment='房源标签')
    
    # 爬取信息
    url = Column(String(300), nullable=False, comment='房源链接')
    crawl_time = Column(DateTime, default=datetime.now, comment='爬取时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<House(id='{self.id}', title='{self.title}', total_price={self.total_price})>"
