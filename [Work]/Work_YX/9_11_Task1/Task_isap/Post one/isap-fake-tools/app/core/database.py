import psycopg2
import asyncpg
from app.core.config import settings

# 同步数据库连接池
sync_connection = None

# 异步数据库连接池
async_connection = None

async def connect():
    """建立数据库连接"""
    global async_connection
    print(f"连接数据库: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    if not async_connection:
        try:
            async_connection = await asyncpg.connect(
                host=settings.POSTGRES_SERVER,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB
            )
            print(f"数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            print(f"提示: 请确保PostgreSQL服务器正在运行，并且配置正确")
            # 不返回连接对象，让调用者处理异常
            raise
    return async_connection

async def disconnect():
    """关闭数据库连接"""
    global async_connection
    if async_connection:
        await async_connection.close()
        async_connection = None

async def execute(query, *args):
    """执行SQL查询"""
    conn = await connect()
    return await conn.execute(query, *args)

async def fetchall(query, *args):
    """执行查询并返回所有结果"""
    conn = await connect()
    # asyncpg使用fetch方法而不是fetchall
    return await conn.fetch(query, *args)

async def execute_many(query=None, values=None):
    """批量执行SQL查询 - 支持PostgreSQL标准位置参数"""
    conn = await connect()
    async with conn.transaction():
        # 使用位置参数传递方式，确保与PostgreSQL标准兼容
        for params in values:
            # 将参数字典的值按顺序作为位置参数传递
            await conn.execute(query, *params.values())

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
        
    async def execute_many(self, query=None, values=None):
        return await execute_many(query=query, values=values)

# 数据库实例，用于向后兼容
database = Database()