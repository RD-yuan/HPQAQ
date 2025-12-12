# HPQAQ
一个包含 爬虫、Python 后端、SQLite 数据库、Vue3 前端 的房价分析系统，用于展示中国大陆一线城市与台湾主要城市的房价信息，包括房源列表与价格走势。

A housing price analysis system with crawler, Python backend, SQLite, and Vue3 frontend, showing listings and price trends for Mainland China tier-1 and major Taiwan cities.

## 技术栈

### 后端
- Python 3.x
- FastAPI - Web 框架
- SQLAlchemy - ORM 框架
- SQLite - 数据库
- BeautifulSoup4 - 网页解析
- Requests - HTTP 请求
- Schedule - 定时任务

### 前端
- Vue 3
- Vite - 构建工具
- Axios - HTTP 客户端

## 项目结构

```
HPQAQ/
├── backend/           # 后端代码
│   ├── app.py         # FastAPI 应用入口
│   ├── config.py      # 配置文件
│   ├── db_init.py     # 数据库初始化
│   ├── models.py      # 数据库模型
│   ├── routes.py      # API 路由
│   ├── crawler/       # 爬虫模块
│   │   ├── base_spider.py  # 爬虫基类
│   │   ├── lian_jia_spider.py  # 链家爬虫
│   │   ├── crawl_cn.py  # 中国大陆城市爬虫
│   │   └── crawl_tw.py  # 台湾地区爬虫
│   ├── scheduler.py   # 定时任务
│   └── hpqaq.db       # SQLite 数据库文件
├── frontend/          # 前端代码
│   ├── src/           # 源代码
│   ├── public/        # 静态资源
│   ├── index.html     # HTML 入口
│   └── vite.config.js # Vite 配置
└── README.md          # 项目说明文档
```

## 安装和运行

### 后端

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv venv
```

3. 激活虚拟环境
```bash
# Windows
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

4. 安装依赖
```bash
pip install -r requirements.txt
```

5. 初始化数据库
```bash
python db_init.py
```

6. 启动后端服务
```bash
uvicorn app:app --reload
```

后端服务将在 `http://localhost:8000` 运行

### 前端

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 启动开发服务器
```bash
npm run dev
```

前端服务将在 `http://localhost:5173` 运行

## 功能特性

### 1. 数据爬取
- 定时爬取中国大陆一线城市（北京、上海、广州、深圳）的房价数据
- 支持爬取台湾主要城市的房价数据
- 数据来源：链家网等房产平台

### 2. 数据存储
- 使用 SQLite 数据库存储房源信息
- 支持数据的增删改查操作
- 自动记录爬取时间和更新时间

### 3. API 接口
- 房源列表查询
- 房源详情查询
- 城市房价统计
- 数据可视化接口

### 4. 前端展示
- 房源列表展示
- 价格走势图表
- 城市筛选功能
- 响应式设计

## 数据库设计

### 房源表 (houses)

| 字段名 | 数据类型 | 描述 |
|--------|----------|------|
| id | String(50) | 房源唯一ID |
| title | String(200) | 房源标题 |
| city | String(20) | 所在城市 |
| district | String(50) | 区域 |
| street | String(100) | 街道 |
| community | String(100) | 小区名称 |
| total_price | Float | 总价（万元） |
| unit_price | Integer | 单价（元/平方米） |
| house_type | String(20) | 户型 |
| area | Float | 建筑面积（平方米） |
| orientation | String(20) | 朝向 |
| floor | String(20) | 楼层 |
| building_year | Integer | 建筑年代 |
| renovation | String(20) | 装修情况 |
| house_structure | String(20) | 房屋结构 |
| elevator | Boolean | 是否有电梯 |
| longitude | Float | 经度 |
| latitude | Float | 纬度 |
| property_right | String(50) | 产权信息 |
| house_usage | String(50) | 房屋用途 |
| property_years | Integer | 产权年限 |
| description | Text | 房源描述 |
| tags | String(200) | 房源标签 |
| url | String(300) | 房源链接 |
| crawl_time | DateTime | 爬取时间 |
| update_time | DateTime | 更新时间 |

## API 接口

### 健康检查
- `GET /health` - 检查服务健康状态

### 房源管理
- `GET /api/v1/houses` - 获取房源列表（支持分页、筛选）
- `GET /api/v1/houses/{id}` - 获取房源详情
- `POST /api/v1/houses` - 创建房源（管理接口）
- `PUT /api/v1/houses/{id}` - 更新房源（管理接口）
- `DELETE /api/v1/houses/{id}` - 删除房源（管理接口）

### 统计分析
- `GET /api/v1/statistics/city/{city}` - 获取城市房价统计
- `GET /api/v1/statistics/trend` - 获取价格走势数据

## 爬虫功能

### 链家爬虫
- 支持多城市房源爬取
- 自动解析房源详情
- 数据去重处理

### 定时任务
- 使用 Schedule 库实现定时爬取
- 可配置爬取频率

## 开发说明

### 配置文件
- 修改 `config.py` 可以配置数据库连接、爬虫参数等

### 增加新的爬虫
1. 继承 `BaseSpider` 类
2. 实现 `crawl` 方法
3. 在 `scheduler.py` 中配置定时任务

### 前端开发
- 使用 Vue 3 Composition API
- 组件化设计
- 响应式数据管理

## 许可证

MIT License

## 作者

编写人：guangqain
