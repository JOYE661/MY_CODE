import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import database

from app.core.database import connect, disconnect

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # 直接调用connect函数，而不是通过database对象调用
        await connect()
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("应用程序将继续运行，但数据插入功能可能不可用")
    yield
    # Shutdown
    try:
        # 直接调用disconnect函数
        await disconnect()
        print("数据库连接已关闭")
    except:
        pass

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(api_router, prefix=settings.API_V1_STR)

# 添加根路径路由
@app.get("/")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0",
        "docs": "/docs",
        "status": "running"
    }

if __name__ == "__main__":
    # 调用数据库连接函数
    try:
        # 直接使用FastAPI的lifespan处理数据库连接
        print("启动应用程序，数据库连接将由FastAPI的lifespan处理")
    except Exception as e:
        print(f"初始化失败: {e}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)