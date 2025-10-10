from fastapi import APIRouter
from app.api.api_v1.endpoints import data_generation

# 创建API路由器
api_router = APIRouter()

# 包含数据生成相关的路由
api_router.include_router(data_generation.router, prefix="/data", tags=["data_generation"])