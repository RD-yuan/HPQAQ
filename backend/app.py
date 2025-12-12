from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

# 创建FastAPI应用
app = FastAPI(
    title="链家房源数据分析API",
    description="提供链家房源数据的查询和分析功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库引擎
engine = create_engine(config.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 导入路由
from routes import *

@app.get("/")
def root():
    return {"message": "链家房源数据分析API服务已启动"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
