# 数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./hpqaq.db"

# 爬虫配置
CRAWLER_CONFIG = {
    # 链家网站配置
    "lianjia": {
        "base_url": "https://{city}.lianjia.com/ershoufang/",
        "cities": {
            "beijing": "bj",
            "shanghai": "sh",
            "hangzhou": "hz",
            "shenzhen": "sz"
        },
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
        "max_pages": 100,  # 每个城市最大爬取页数
        "timeout": 10,     # 请求超时时间
        "retry_times": 3,  # 重试次数
        "delay": 2         # 请求延迟（秒）
    }
}
