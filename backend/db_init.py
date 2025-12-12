from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import config

def init_db():
    """初始化数据库，创建所有表"""
    engine = create_engine(config.SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成，表结构已创建")
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

if __name__ == "__main__":
    init_db()
