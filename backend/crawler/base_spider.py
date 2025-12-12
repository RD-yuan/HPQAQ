import requests
from fake_useragent import UserAgent
import time
import random
from typing import Dict, List, Optional, Any
from lxml import etree
import logging

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BaseSpider:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        self.ua = UserAgent()
        self._setup_session()
    
    def _setup_session(self):
        """设置会话信息，包括请求头和代理等"""
        # 使用配置中的请求头或随机生成
        headers = self.config.get('headers', {})
        if not headers.get('User-Agent'):
            headers['User-Agent'] = self.ua.random
        
        self.session.headers.update(headers)
        # 启用自动处理Cookie
        self.session.cookies.update({})
    
    def get_page(self, url: str, retry: int = 0) -> Optional[str]:
        """获取页面内容，支持重试机制和反爬策略"""
        try:
            # 随机延迟，避免请求过于频繁
            time.sleep(random.uniform(0.5, self.config.get('delay', 2)))
            
            response = self.session.get(
                url,
                timeout=self.config.get('timeout', 10),
                proxies=self._get_proxy()
            )
            
            response.raise_for_status()  # 检查响应状态码
            response.encoding = response.apparent_encoding  # 自动检测编码
            
            logger.info(f"成功获取页面: {url}")
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"获取页面失败 ({url}): {str(e)}")
            
            # 重试逻辑
            if retry < self.config.get('retry_times', 3):
                logger.info(f"重试获取页面 ({retry + 1}/{self.config.get('retry_times', 3)}): {url}")
                return self.get_page(url, retry + 1)
            
        return None
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """获取代理IP，这里可以扩展为从代理池获取"""
        # 暂时不使用代理，后续可以扩展
        return None
    
    def parse_html(self, html: str) -> Optional[etree._Element]:
        """解析HTML页面，返回lxml对象"""
        try:
            return etree.HTML(html)
        except Exception as e:
            logger.error(f"解析HTML失败: {str(e)}")
            return None
    
    def extract_text(self, element: etree._Element, xpath: str) -> str:
        """提取元素文本"""
        elements = element.xpath(xpath)
        return elements[0].strip() if elements else ''
    
    def extract_attr(self, element: etree._Element, xpath: str, attr: str) -> str:
        """提取元素属性"""
        elements = element.xpath(xpath)
        return elements[0].get(attr, '').strip() if elements else ''
    
    def extract_list(self, element: etree._Element, xpath: str) -> List[etree._Element]:
        """提取元素列表"""
        return element.xpath(xpath)
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """保存数据的基础方法，子类需要重写实现具体的保存逻辑"""
        raise NotImplementedError("子类必须实现save_data方法")
