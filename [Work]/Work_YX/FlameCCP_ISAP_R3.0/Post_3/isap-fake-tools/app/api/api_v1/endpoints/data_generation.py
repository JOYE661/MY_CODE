from fastapi import APIRouter, Query, BackgroundTasks
from typing import List, Optional
from app.schemas.data_generation import GenerateDataRequest, GenerateDataResponse
from app.services.data_generator import DataGenerator

router = APIRouter()

data_generator = DataGenerator()

@router.post("/generate", response_model=GenerateDataResponse, summary="生成演示数据")
async def generate_data(
    request: GenerateDataRequest,
    background_tasks: BackgroundTasks
):
    """
    生成演示数据
    
    - **tables**: 要生成数据的表名列表，如果为空则生成所有配置的表
    - **records_per_day**: 每天要生成的记录数量
    - **start_date**: 开始日期，格式为YYYY-MM-DD
    - **end_date**: 结束日期，格式为YYYY-MM-DD
    - **async_mode**: 是否异步生成数据
    """
    if request.async_mode:
        # 异步模式下，将任务添加到后台任务
        background_tasks.add_task(
            data_generator.generate_data_for_tables,
            request.tables,
            request.records_per_day,
            request.start_date,
            request.end_date
        )
        return GenerateDataResponse(
            status="success",
            message="数据生成任务已在后台启动",
            task_id="task_async_" + str(hash(str(request)))
        )
    else:
        # 同步模式下，直接生成数据
        result = await data_generator.generate_data_for_tables(
            request.tables,
            request.records_per_day,
            request.start_date,
            request.end_date
        )
        return GenerateDataResponse(
            status="success",
            message=f"数据生成完成，共生成{result}条记录",
            task_id="task_sync_" + str(hash(str(request)))
        )

@router.get("/tables", response_model=List[str], summary="获取所有可生成数据的表")
async def get_available_tables():
    """
    获取所有可生成数据的表名
    """
    return data_generator.get_available_tables()

@router.post("/clear", response_model=GenerateDataResponse, summary="清空表数据")
async def clear_table_data(
    tables: Optional[List[str]] = Query(None, description="要清空数据的表名列表，如果为空则清空所有表")
):
    """
    清空表数据
    
    - **tables**: 要清空数据的表名列表，如果为空则清空所有配置的表
    """
    await data_generator.clear_table_data(tables)
    return GenerateDataResponse(
        status="success",
        message="表数据清空完成",
        task_id="task_clear_" + str(hash(str(tables)))
    )