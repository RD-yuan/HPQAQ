import schedule
import time
import logging
from crawler.lian_jia_spider import LianJiaSpider
from config import CRAWLER_CONFIG
import threading

# 设置日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_crawler():
    """运行链家爬虫"""
    logger.info("开始执行定时爬虫任务")
    
    try:
        # 初始化爬虫
        config = CRAWLER_CONFIG['lianjia']
        spider = LianJiaSpider(config)
        spider.init_database()
        
        # 爬取所有配置的城市
        for city_name, city_code in config['cities'].items():
            spider.crawl_city(city_name, city_code)
            
    except Exception as e:
        logger.error(f"定时爬虫任务执行失败: {str(e)}")
    finally:
        if 'spider' in locals() and hasattr(spider, 'close'):
            spider.close()
        logger.info("定时爬虫任务执行完成")

def start_scheduler():
    """启动定时任务"""
    logger.info("启动定时任务调度器")
    
    # 设置定时任务：每天凌晨2点执行一次
    schedule.every().day.at("02:00").do(run_crawler)
    
    logger.info("定时任务已设置：每天凌晨2点执行爬虫")
    logger.info("按 Ctrl+C 停止调度器")
    
    # 立即执行一次爬虫任务
    run_crawler()
    
    # 开始调度循环
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次任务
    except KeyboardInterrupt:
        logger.info("定时任务调度器已停止")

if __name__ == "__main__":
    start_scheduler()
