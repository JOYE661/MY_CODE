#!/usr/bin/env python3
"""
后台数据生成服务
这个脚本可以在后台独立运行，不依赖于浏览器
"""

import asyncio
import time
from datetime import datetime, date
import signal
import sys
from app.services.data_generator import DataGenerator
from app.core.database import database
from app.core.config import settings

class BackgroundDataGenerator:
    def __init__(self):
        self.generator = DataGenerator()
        self.running = False
        self.available_tables = self.generator.get_available_tables()
        
    async def connect_database(self):
        """连接数据库"""
        try:
            await database.connect()
            print(f"[{datetime.now()}] ✅ 成功连接到数据库: {settings.POSTGRES_DB}")
            return True
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 数据库连接失败: {e}")
            return False
    
    async def disconnect_database(self):
        """断开数据库连接"""
        try:
            await database.disconnect()
            print(f"[{datetime.now()}] 🔌 已断开数据库连接")
        except Exception as e:
            print(f"[{datetime.now()}] ⚠️ 断开数据库连接时出错: {e}")
    
    async def generate_data_batch(self, tables, records_per_batch):
        """生成一批数据"""
        try:
            today = date.today()
            total_records = await self.generator.generate_data_for_tables(
                tables,
                records_per_batch,
                today,
                today
            )
            print(f"[{datetime.now()}] 📦 生成了 {total_records} 条记录")
            return total_records
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 数据生成失败: {e}")
            return 0
    
    async def clear_data(self, tables):
        """清空数据"""
        try:
            print(f"[{datetime.now()}] 🧹 开始清空数据...")
            await self.generator.clear_table_data(tables)
            print(f"[{datetime.now()}] ✅ 数据清空完成")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 数据清空失败: {e}")
    
    def signal_handler(self, signum, frame):
        """信号处理器，用于优雅关闭"""
        print(f"\n[{datetime.now()}] 🛑 收到停止信号，正在关闭...")
        self.running = False
    
    async def run_continuous_generation(self, tables=None, interval_seconds=30, records_per_batch=10):
        """持续生成数据"""
        # 如果没有指定表，则使用所有可用表
        if tables is None:
            tables = self.available_tables
        
        if not tables:
            print(f"[{datetime.now()}] ⚠️ 没有可用的表进行数据生成")
            return
        
        print(f"[{datetime.now()}] 🚀 启动持续数据生成服务")
        print(f"   表: {', '.join(tables)}")
        print(f"   间隔: {interval_seconds} 秒")
        print(f"   每批记录数: {records_per_batch}")
        print(f"   按 Ctrl+C 停止服务")
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
        batch_count = 0
        
        try:
            while self.running:
                batch_count += 1
                print(f"[{datetime.now()}] 📦 开始生成第 {batch_count} 批数据...")
                
                # 生成数据
                records_generated = await self.generate_data_batch(tables, records_per_batch)
                
                if records_generated > 0:
                    print(f"[{datetime.now()}] ✅ 第 {batch_count} 批数据生成完成")
                else:
                    print(f"[{datetime.now()}] ⚠️ 第 {batch_count} 批数据生成失败")
                
                # 等待下次生成
                print(f"[{datetime.now()}] ⏱️ 等待 {interval_seconds} 秒后继续...")
                for _ in range(interval_seconds):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                    
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] 🛑 用户中断，正在关闭...")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 运行时出错: {e}")
        finally:
            self.running = False
            print(f"[{datetime.now()}] 🛑 持续数据生成服务已停止")
    
    async def run_once(self, tables=None, records_per_day=100):
        """运行一次数据生成"""
        # 如果没有指定表，则使用所有可用表
        if tables is None:
            tables = self.available_tables
            
        if not tables:
            print(f"[{datetime.now()}] ⚠️ 没有可用的表进行数据生成")
            return
            
        try:
            today = date.today()
            print(f"[{datetime.now()}] 🚀 开始一次性数据生成...")
            print(f"   表: {', '.join(tables)}")
            print(f"   记录数: {records_per_day}")
            print(f"   日期: {today}")
            
            total_records = await self.generator.generate_data_for_tables(
                tables,
                records_per_day,
                today,
                today
            )
            
            print(f"[{datetime.now()}] ✅ 数据生成完成，共生成 {total_records} 条记录")
            return total_records
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 数据生成失败: {e}")
            return 0

async def main():
    """主函数"""
    # 创建后台数据生成器实例
    bg_generator = BackgroundDataGenerator()
    
    # 连接数据库
    if not await bg_generator.connect_database():
        print("无法连接到数据库，程序退出")
        return
    
    try:
        # 根据命令行参数决定运行模式
        if len(sys.argv) > 1 and sys.argv[1] == "continuous":
            # 持续生成模式
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            records = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            
            # 获取指定的表列表（如果有的话）
            tables = None
            if len(sys.argv) > 4:
                table_list_str = sys.argv[4]
                if table_list_str != "all":
                    tables = table_list_str.split(",")
            
            await bg_generator.run_continuous_generation(
                tables=tables,
                interval_seconds=interval,
                records_per_batch=records
            )
        else:
            # 一次性生成模式
            records = int(sys.argv[1]) if len(sys.argv) > 1 else 100
            
            # 获取指定的表列表（如果有的话）
            tables = None
            if len(sys.argv) > 2:
                table_list_str = sys.argv[2]
                if table_list_str != "all":
                    tables = table_list_str.split(",")
            
            await bg_generator.run_once(
                tables=tables,
                records_per_day=records
            )
    finally:
        # 断开数据库连接
        await bg_generator.disconnect_database()

if __name__ == "__main__":
    asyncio.run(main())