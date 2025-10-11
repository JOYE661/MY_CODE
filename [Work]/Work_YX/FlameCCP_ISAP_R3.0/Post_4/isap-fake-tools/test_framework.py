import json
import os
from datetime import date
from app.services.data_generator import DataGenerator
from app.core.config import settings

# 简单的模拟Faker类，用于测试
class MockFaker:
    def __init__(self):
        self.seed = 42
    
    def uuid4(self):
        return "mock-uuid-1234"
    
    def word(self):
        return "mock-word"
    
    def name(self):
        return "张三"
    
    def phone_number(self):
        return "13800138000"
    
    def email(self):
        return "test@example.com"
    
    def date_of_birth(self):
        return "1990-01-01"
    
    def address(self):
        return "北京市朝阳区"

# 修补DataGenerator类，避免数据库连接
class TestDataGenerator(DataGenerator):
    def __init__(self):
        # 加载配置但不连接数据库
        self.faker = MockFaker()
        self.table_configs = self._load_table_configs()
        self.record_counters = {}
    
    # 重写生成字段值的方法，使用简单的模拟值
    def _generate_field_value(self, field_config, table_name, current_date):
        field_type = field_config.get('type', 'string')
        field_generator = field_config.get('generator', None)
        
        if field_generator == 'uuid':
            return f"{table_name}-id-{current_date}-{len(self.record_counters)}"
        elif field_generator == 'current_timestamp':
            return f"{current_date} 12:00:00"
        elif field_generator == 'incremental':
            counter_key = f"{table_name}_{field_config.get('name', 'id')}"
            if counter_key not in self.record_counters:
                self.record_counters[counter_key] = 1
            else:
                self.record_counters[counter_key] += 1
            return self.record_counters[counter_key]
        elif field_generator and field_generator.startswith('random_choice:'):
            choices = field_generator[14:].split(',')
            return choices[0] if choices else "default"
        
        if field_type == 'string':
            return f"{table_name}-{field_config.get('name', 'field')}-value"
        elif field_type == 'integer':
            return 42
        elif field_type == 'decimal':
            return 99.99
        elif field_type == 'boolean':
            return True
        
        return None


def test_data_generator():
    """测试数据生成器的基本功能"""
    print("开始测试数据生成器框架...")
    
    # 创建测试用的数据生成器实例
    generator = TestDataGenerator()
    
    # 获取可用的表
    available_tables = generator.get_available_tables()
    print(f"可用的表: {available_tables}")
    
    # 测试生成记录
    print("测试生成单条记录...")
    if available_tables:
        for table_name in available_tables[:3]:  # 只测试前3个表
            if table_name in generator.table_configs:
                config = generator.table_configs[table_name]
                current_date = date.today()
                
                # 生成单条记录用于测试
                record = generator._generate_record(config, table_name, current_date)
                
                # 打印表名和记录结构
                print(f"\n表名: {table_name}")
                print(f"字段数量: {len(record)}")
                print(f"字段列表: {list(record.keys())}")
                print(f"示例字段值: {{ 'customer_id': '{record.get('customer_id', 'N/A')}', 'order_id': '{record.get('order_id', 'N/A')}' }}")
    
    # 验证配置文件加载机制
    print("\n验证配置文件加载机制...")
    config_dir = settings.CONFIG_FILE_PATH
    config_files = [f[:-5] for f in os.listdir(config_dir) if f.endswith('.json')]
    print(f"配置目录: {config_dir}")
    print(f"配置文件数量: {len(config_files)}")
    print(f"配置文件名: {config_files}")
    
    print("\n框架测试完成！")
    print("\n使用说明:")
    print("1. 确保已配置正确的PostgreSQL数据库连接信息在.env文件中")
    print("2. 运行 'python3 main.py' 启动FastAPI服务器")
    print("3. 访问 http://localhost:8000/docs 查看API文档和测试接口")
    print("4. 通过API接口控制数据生成任务")
    print("5. 要为新表生成数据，只需在configs目录下添加相应的JSON配置文件")

if __name__ == "__main__":
    # 运行测试
    test_data_generator()