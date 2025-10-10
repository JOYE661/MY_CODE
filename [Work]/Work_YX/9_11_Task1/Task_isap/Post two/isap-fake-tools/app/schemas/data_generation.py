from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class GenerateDataRequest(BaseModel):
    tables: Optional[List[str]] = Field(
        None, 
        description="要生成数据的表名列表，如果为空则生成所有配置的表"
    )
    records_per_day: int = Field(
        100, 
        description="每天要生成的记录数量"
    )
    start_date: date = Field(
        description="开始日期，格式为YYYY-MM-DD"
    )
    end_date: date = Field(
        description="结束日期，格式为YYYY-MM-DD"
    )
    async_mode: bool = Field(
        False, 
        description="是否异步生成数据"
    )

class GenerateDataResponse(BaseModel):
    status: str = Field(
        description="操作状态，success表示成功"
    )
    message: str = Field(
        description="操作结果消息"
    )
    task_id: Optional[str] = Field(
        None, 
        description="任务ID，用于异步任务跟踪"
    )