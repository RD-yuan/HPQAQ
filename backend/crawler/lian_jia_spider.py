from .base_spider import BaseSpider
from models import House
from db_init import init_db
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class LianJiaSpider(BaseSpider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = None
        
    def init_database(self):
        """初始化数据库连接"""
        SessionLocal = init_db()
        self.session = SessionLocal()
    
    def crawl_city(self, city_name: str, city_code: str):
        """爬取指定城市的房源数据"""
        logger.info(f"开始爬取城市: {city_name} ({city_code})")
        
        base_url = self.config['base_url'].format(city=city_code)
        total_houses = 0
        
        # 爬取多页数据
        for page in range(1, self.config.get('max_pages', 100) + 1):
            page_url = f"{base_url}pg{page}/"
            logger.info(f"爬取第 {page} 页: {page_url}")
            
            html = self.get_page(page_url)
            if not html:
                logger.error(f"无法获取第 {page} 页数据")
                continue
            
            # 解析列表页
            house_links = self.parse_list_page(html, city_name)
            
            if not house_links:
                logger.info(f"第 {page} 页没有房源数据，爬取结束")
                break
            
            # 爬取详情页
            for link in house_links:
                self.crawl_house_detail(link, city_name)
                total_houses += 1
            
        logger.info(f"城市 {city_name} 爬取完成，共获取 {total_houses} 条房源数据")
    
    def parse_list_page(self, html: str, city_name: str) -> List[str]:
        """解析列表页，提取房源详情页链接"""
        tree = self.parse_html(html)
        if not tree:
            return []
        
        # 提取房源列表项
        house_items = self.extract_list(tree, '//ul[@class="sellListContent"]/li[@class="clear LOGCLICKDATA"]')
        house_links = []
        
        for item in house_items:
            # 提取详情页链接
            link = self.extract_attr(item, './/div[@class="info clear"]/div[@class="title"]/a', 'href')
            if link:
                house_links.append(link)
        
        logger.info(f"从列表页提取到 {len(house_links)} 个房源链接")
        return house_links
    
    def crawl_house_detail(self, url: str, city_name: str):
        """爬取房源详情页"""
        html = self.get_page(url)
        if not html:
            logger.error(f"无法获取房源详情页: {url}")
            return
        
        # 解析详情页数据
        house_data = self.parse_detail_page(html, city_name, url)
        if not house_data:
            logger.error(f"解析房源详情页失败: {url}")
            return
        
        # 保存数据到数据库
        self.save_data(house_data)
    
    def parse_detail_page(self, html: str, city_name: str, url: str) -> Dict[str, Any]:
        """解析详情页数据"""
        tree = self.parse_html(html)
        if not tree:
            return {}
        
        try:
            # 提取房源基本信息
            house_id = self._extract_house_id(url)
            title = self.extract_text(tree, '//div[@class="title"]/h1')
            
            # 提取价格信息
            total_price_text = self.extract_text(tree, '//div[@class="price"]/span[@class="total"]')
            total_price = float(total_price_text)
            
            unit_price_text = self.extract_text(tree, '//span[@class="unitPriceValue"]')
            unit_price = int(re.sub(r'[^\d]', '', unit_price_text)) if unit_price_text else None
            
            # 提取基本属性
            base_info = {}
            base_info_items = self.extract_list(tree, '//div[@class="base"]/div[@class="content"]/ul/li')
            for item in base_info_items:
                label = self.extract_text(item, './/span[@class="label"]')
                value = self.extract_text(item, './/text()')
                value = re.sub(label, '', value).strip()
                base_info[label] = value
            
            # 提取小区和位置信息
            community = self.extract_text(tree, '//div[@class="communityName"]/a[@class="info"]')
            area_info = self.extract_list(tree, '//div[@class="areaName"]/span[@class="info"]/a')
            district = area_info[0].text.strip() if area_info else ''
            street = area_info[1].text.strip() if len(area_info) > 1 else ''
            
            # 提取房源特色标签
            tags = self.extract_list(tree, '//div[@class="tags clear"]/div[@class="content"]/ul/li')
            tags_text = ','.join([tag.text.strip() for tag in tags if tag.text])
            
            # 构造房源数据
            house_data = {
                'id': house_id,
                'title': title,
                'city': city_name,
                'district': district,
                'street': street,
                'community': community,
                'total_price': total_price,
                'unit_price': unit_price,
                'house_type': base_info.get('房屋户型', ''),
                'area': float(re.search(r'([\d.]+)', base_info.get('建筑面积', '')).group(1)) if base_info.get('建筑面积') else None,
                'orientation': base_info.get('房屋朝向', ''),
                'floor': base_info.get('所在楼层', ''),
                'renovation': base_info.get('装修情况', ''),
                'house_structure': base_info.get('建筑结构', ''),
                'elevator': '有电梯' in base_info.get('配备电梯', '') if base_info.get('配备电梯') else None,
                'tags': tags_text,
                'url': url
            }
            
            # 尝试提取建筑年代
            build_info_items = self.extract_list(tree, '//div[@class="transaction"]/div[@class="content"]/ul/li')
            for item in build_info_items:
                label = self.extract_text(item, './/span[@class="label"]')
                value = self.extract_text(item, './/text()')
                value = re.sub(label, '', value).strip()
                
                if label == '建筑年代':
                    year_match = re.search(r'(\d{4})', value)
                    if year_match:
                        house_data['building_year'] = int(year_match.group(1))
                elif label == '产权年限':
                    house_data['property_years'] = int(re.search(r'(\d+)', value).group(1)) if re.search(r'(\d+)', value) else None
                elif label == '房屋用途':
                    house_data['house_usage'] = value
                elif label == '产权所属':
                    house_data['property_right'] = value
            
            return house_data
            
        except Exception as e:
            logger.error(f"解析详情页数据失败: {str(e)}")
            return {}
    
    def _extract_house_id(self, url: str) -> str:
        """从URL中提取房源ID"""
        match = re.search(r'/(\d+)\.html', url)
        return match.group(1) if match else f"{int(datetime.now().timestamp())}"
    
    def save_data(self, house_data: Dict[str, Any]) -> bool:
        """保存数据到数据库"""
        if not house_data or not self.session:
            return False
        
        try:
            # 检查数据是否已存在
            existing_house = self.session.query(House).filter(House.id == house_data['id']).first()
            
            if existing_house:
                # 更新现有数据
                for key, value in house_data.items():
                    setattr(existing_house, key, value)
                logger.info(f"更新房源数据: {house_data['id']}")
            else:
                # 创建新数据
                house = House(**house_data)
                self.session.add(house)
                logger.info(f"新增房源数据: {house_data['id']}")
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            self.session.rollback()
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()
            logger.info("数据库连接已关闭")

if __name__ == "__main__":
    from config import CRAWLER_CONFIG
    
    # 初始化爬虫
    config = CRAWLER_CONFIG['lianjia']
    spider = LianJiaSpider(config)
    spider.init_database()
    
    try:
        # 爬取所有配置的城市
        for city_name, city_code in config['cities'].items():
            spider.crawl_city(city_name, city_code)
    finally:
        spider.close()
