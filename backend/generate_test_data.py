from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, House
import config
from datetime import datetime, timedelta
import random
import uuid

# 创建数据库引擎
engine = create_engine(config.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def generate_test_data():
    """生成测试数据并插入数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    db = SessionLocal()
    
    try:
        # 测试城市列表
        cities = ['北京', '上海', '杭州', '深圳']
        
        # 各城市的区域列表
        districts = {
            '北京': ['海淀', '朝阳', '西城', '东城', '丰台', '石景山'],
            '上海': ['浦东', '闵行', '静安', '黄浦', '徐汇', '长宁'],
            '杭州': ['西湖', '余杭', '滨江', '江干', '下城', '上城'],
            '深圳': ['南山', '福田', '罗湖', '宝安', '龙岗', '盐田']
        }
        
        # 房屋类型列表
        house_types = ['一室一厅', '两室一厅', '两室两厅', '三室一厅', '三室两厅', '四室两厅']
        
        # 朝向列表
        orientations = ['东', '南', '西', '北', '东南', '西南', '东北', '西北']
        
        # 楼层列表
        floors = ['低层', '中层', '高层', '顶层']
        
        # 装修情况列表
        renovations = ['精装', '简装', '毛坯']
        
        # 生成测试数据
        for city in cities:
            # 每个城市生成100条测试数据
            for i in range(100):
                # 随机选择区域
                district = random.choice(districts[city])
                
                # 随机生成房屋基本信息
                house_type = random.choice(house_types)
                area = round(random.uniform(50, 200), 1)
                orientation = random.choice(orientations)
                floor = random.choice(floors)
                renovation = random.choice(renovations)
                
                # 随机生成价格信息
                if city == '北京' or city == '上海':
                    total_price = round(random.uniform(200, 1500), 1)
                    unit_price = round(total_price * 10000 / area)
                elif city == '深圳':
                    total_price = round(random.uniform(180, 1200), 1)
                    unit_price = round(total_price * 10000 / area)
                else:  # 杭州
                    total_price = round(random.uniform(150, 800), 1)
                    unit_price = round(total_price * 10000 / area)
                
                # 随机生成建筑年代
                building_year = random.randint(1990, 2023)
                
                # 随机生成电梯信息
                elevator = random.choice([True, False])
                
                # 生成房源ID
                house_id = f"{uuid.uuid4()}"
                
                # 生成标题
                title = f"{district} {random.randint(10000, 99999)}小区 {house_type} {area}㎡"
                
                # 随机生成街道和小区名称
                street = f"{district}街道"
                community = f"{district}{random.randint(100, 999)}小区"
                
                # 随机生成标签
                tags = ','.join(random.sample(['近地铁', '南北通透', '精装修', '有电梯', '采光好', '满五年'], k=random.randint(1, 4)))
                
                # 随机生成爬取时间（最近3个月内）
                crawl_time = datetime.now() - timedelta(days=random.randint(0, 90))
                
                # 创建房源对象
                house = House(
                    id=house_id,
                    title=title,
                    city=city,
                    district=district,
                    street=street,
                    community=community,
                    total_price=total_price,
                    unit_price=unit_price,
                    house_type=house_type,
                    area=area,
                    orientation=orientation,
                    floor=floor,
                    building_year=building_year,
                    renovation=renovation,
                    elevator=elevator,
                    tags=tags,
                    url=f"https://{city}.lianjia.com/ershoufang/{house_id}/",
                    crawl_time=crawl_time
                )
                
                # 添加到数据库
                db.add(house)
            
        # 提交事务
        db.commit()
        print("测试数据生成完成！")
        print(f"共生成 {len(cities) * 100} 条房源数据")
        
    except Exception as e:
        print(f"生成测试数据时发生错误: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_data()