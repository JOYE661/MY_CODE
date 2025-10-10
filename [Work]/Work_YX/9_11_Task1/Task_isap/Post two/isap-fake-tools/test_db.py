import asyncio
from app.core.database import connect

async def test():
    try:
        conn = await connect()
        print('数据库连接成功')
        await conn.close()
    except Exception as e:
        print(f'数据库连接失败: {e}')

asyncio.run(test())
