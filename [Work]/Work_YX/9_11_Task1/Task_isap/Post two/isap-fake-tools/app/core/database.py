import psycopg2
import asyncpg
import logging
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 同步数据库连接池
sync_connection = None

# 异步数据库连接池
async_connection = None

async def connect():
    """建立数据库连接"""
    global async_connection
    logger.info(f"连接数据库: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    if not async_connection:
        try:
            async_connection = await asyncpg.connect(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB
            )
            logger.info(f"数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            logger.error(f"提示: 请确保PostgreSQL服务器正在运行，并且配置正确")
            # 不返回连接对象，让调用者处理异常
            raise
    return async_connection

async def disconnect():
    """关闭数据库连接"""
    global async_connection
    if async_connection:
        await async_connection.close()
        async_connection = None
        logger.info("数据库连接已关闭")

async def execute(query, *args):
    """执行SQL查询"""
    logger.info(f"执行SQL: {query}, 参数: {args}")
    conn = await connect()
    try:
        result = await conn.execute(query, *args)
        logger.info(f"SQL执行成功")
        return result
    except Exception as e:
        logger.error(f"执行SQL失败: {query}, 参数: {args}, 错误: {e}")
        raise e

async def fetchall(query, *args):
    """执行查询并返回所有结果"""
    logger.info(f"执行查询: {query}, 参数: {args}")
    conn = await connect()
    try:
        # asyncpg使用fetch方法而不是fetchall
        result = await conn.fetch(query, *args)
        logger.info(f"查询执行成功，返回 {len(result)} 条记录")
        return result
    except Exception as e:
        logger.error(f"执行查询失败: {query}, 参数: {args}, 错误: {e}")
        raise e

async def fetch_val(query, *args):
    """执行查询并返回单个值"""
    logger.info(f"执行查询: {query}, 参数: {args}")
    conn = await connect()
    try:
        result = await conn.fetchval(query, *args)
        logger.info(f"查询执行成功")
        return result
    except Exception as e:
        logger.error(f"执行查询失败: {query}, 参数: {args}, 错误: {e}")
        raise e

async def execute_many(query=None, values=None):
    """批量执行SQL查询 - 高效地插入多行数据"""
    logger.info(f"批量执行SQL，查询: {query}, 值数量: {len(values) if values else 0}")
    conn = await connect()
    async with conn.transaction():
        if not values:
            logger.warning("没有提供要插入的数据")
            return

        # 检查 values 是否为字典列表（即包含字段名）
        if isinstance(values[0], dict):
            import re
            # 从查询中提取字段名
            field_match = re.search(r'INSERT INTO \w+ \((.+?)\)', query, re.IGNORECASE)
            if not field_match:
                raise ValueError("无法从查询中解析字段名")

            field_names = [field.strip() for field in field_match.group(1).split(',')]
            # 将字典列表转换为元组列表，确保顺序正确
            prepared_values = [
                tuple(item.get(field, None) for field in field_names) for item in values
            ]
        else:
            # 假设 values 已经是正确顺序的元组或列表
            prepared_values = values

        # 使用 asyncpg 的 executemany 方法进行高效批量插入
        await conn.executemany(query, prepared_values)
        logger.info("批量执行SQL完成")

# 数据库类，正确处理self参数
class Database:
    async def connect(self):
        return await connect()
        
    async def disconnect(self):
        return await disconnect()
        
    async def execute(self, query, *args):
        return await execute(query, *args)
        
    async def fetchall(self, query, *args):
        return await fetchall(query, *args)
        
    async def fetch_val(self, query, *args):
        return await fetch_val(query, *args)
        
    async def execute_many(self, query=None, values=None):
        return await execute_many(query=query, values=values)

# 数据库实例，用于向后兼容
database = Database()

async def test_connection():
    """测试数据库连接和权限"""
    logger.info("测试数据库连接和权限")
    try:
        conn = await connect()
        # 测试基本查询权限
        result = await conn.fetchval("SELECT 1")
        logger.info(f"基本查询测试成功: {result}")
        
        # 测试列出所有表
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        table_names = [table['table_name'] for table in tables]
        logger.info(f"数据库中的表: {table_names}")
        
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False
