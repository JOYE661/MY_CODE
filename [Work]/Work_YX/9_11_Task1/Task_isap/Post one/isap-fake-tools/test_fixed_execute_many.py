import asyncio
from app.core.database import database
from app.core.config import settings

async def test_fixed_execute_many():
    """测试修复后的execute_many函数是否正常工作"""
    try:
        print(f"开始测试修复后的execute_many函数...")
        print(f"连接到数据库: {settings.POSTGRES_SERVER}")
        
        # 尝试创建一个临时测试表
        test_table = "test_fixed_execute_many_table"
        
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
        
        # 准备测试数据 - 使用与data_generator.py相同的字典格式
        test_data = [
            {"name": "测试1", "value": 100},
            {"name": "测试2", "value": 200},
            {"name": "测试3", "value": 300}
        ]
        
        # 使用PostgreSQL标准的位置参数格式
        columns = ["name", "value"]
        placeholders = [f"${i+1}" for i, _ in enumerate(columns)]
        insert_sql = f"INSERT INTO {test_table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # 测试execute_many函数
        await database.execute_many(query=insert_sql, values=test_data)
        print(f"✓ execute_many调用成功，插入了 {len(test_data)} 条记录")
        
        # 查询数据验证插入结果
        result = await database.fetchall(query=f"SELECT * FROM {test_table}")
        print(f"✓ 查询结果: 找到 {len(result)} 条记录")
        print(f"✓ 查询到的数据: {result}")
        
        # 清理测试表
        await database.execute(query=f"DROP TABLE IF EXISTS {test_table}")
        print(f"✓ 清理测试表成功")
        
        print("\n🎉 测试成功完成！execute_many函数的语法错误问题已修复。")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_fixed_execute_many())