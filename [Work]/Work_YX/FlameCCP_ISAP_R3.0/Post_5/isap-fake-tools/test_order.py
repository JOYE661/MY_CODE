import asyncio
from app.core.database import connect, fetchall

async def test():
    try:
        # 测试oms_order表是否存在
        conn = await connect()
        result = await fetchall('SELECT COUNT(*) FROM oms_order')
        print(f'oms_order表中有 {result[0]["count"]} 条记录')
        
        # 查看一些示例数据
        result = await fetchall('SELECT order_id FROM oms_order LIMIT 5')
        print('示例order_id:')
        for row in result:
            print(f'  {row["order_id"]}')
    except Exception as e:
        print(f'查询失败: {e}')

asyncio.run(test())
