#!/usr/bin/env python3
"""
测试表结构创建功能的脚本
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.table_manager import table_manager
from app.core.database import connect, disconnect

async def test_table_creation():
    """测试表创建功能"""
    print("🔍 开始测试表结构创建功能...")
    
    try:
        # 连接数据库
        await connect()
        print("✅ 数据库连接成功")
        
        # 测试表状态检查
        print("\n📊 检查表状态...")
        table_status = await table_manager.get_table_status()
        for table_name, status in table_status.items():
            print(f"   {table_name}: {status['message']}")
        
        # 测试表创建
        print("\n🏗️  测试表创建功能...")
        test_table = "crm_customer"
        exists_before = await table_manager._check_table_exists(test_table)
        print(f"   表 {test_table} 创建前是否存在: {exists_before}")
        
        if not exists_before:
            print(f"   尝试创建表 {test_table}...")
            success = await table_manager.ensure_table_exists(test_table)
            print(f"   表创建结果: {'成功' if success else '失败'}")
            
            exists_after = await table_manager._check_table_exists(test_table)
            print(f"   表 {test_table} 创建后是否存在: {exists_after}")
        
        # 测试初始化所有表
        print("\n🔧 测试初始化所有表...")
        results = await table_manager.initialize_all_tables()
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        print(f"   表初始化结果: {success_count}/{total_count} 个表成功")
        
        # 显示最终表状态
        print("\n📊 最终表状态...")
        final_status = await table_manager.get_table_status()
        for table_name, status in final_status.items():
            print(f"   {table_name}: {status['message']}")
        
        print("\n✅ 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 断开数据库连接
        await disconnect()
        print("🔌 数据库连接已关闭")

if __name__ == "__main__":
    asyncio.run(test_table_creation())
