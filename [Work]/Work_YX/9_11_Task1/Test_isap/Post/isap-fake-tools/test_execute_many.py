import asyncio
from app.core.database import database
from app.core.config import settings

async def test_execute_many():
    """测试 execute_many 函数是否修复成功"""
    try:
        print(f"开始测试 execute_many 函数...")
        print(f"连接到数据库: {settings.POSTGRES_SERVER}")
        
        # 尝试创建一个临时测试表
        test_table = "test_execute_many_table"
        
        # 先删除可能存在的测试表
        await database.execute(query=f"DROP TABLE IF EXISTS {test_table}")
        
        # 创建测试表
        create_table_sql = f"""
        CREATE TABLE {test_table} (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50),
            value INTEGER
        )
        """
        await database.execute(query=create_table_sql)
        print(f"✓ 创建测试表成功")
        
        # 准备测试数据
        test_data = [
            {"name": "测试1", "value": 100},
            {"name": "测试2", "value": 200},
            {"name": "测试3", "value": 300}
        ]
        
        # 测试 execute_many 函数 - 使用标准的PostgreSQL参数占位符格式
        insert_sql = f"INSERT INTO {test_table} (name, value) VALUES ($1, $2)"
        await database.execute_many(query=insert_sql, values=test_data)
        print(f"✓ execute_many 调用成功，插入了 {len(test_data)} 条记录")
        
        # 查询数据验证插入结果
        result = await database.fetchall(query=f"SELECT * FROM {test_table}")
        print(f"✓ 查询结果: 找到 {len(result)} 条记录")
        
        # 清理测试表
        await database.execute(query=f"DROP TABLE IF EXISTS {test_table}")
        print(f"✓ 清理测试表成功")
        
        print("\n🎉 测试成功完成！execute_many 函数已经可以正常工作。")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保断开连接 - 注意这里disconnect不需要参数
        await database.disconnect()

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_execute_many())