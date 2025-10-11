import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from faker import Faker
from app.core.config import settings
from app.core.database import database
from app.services.table_manager import table_manager

class DataGenerator:
    def __init__(self):
        self.faker = Faker('zh_CN')
        self.table_configs = self._load_table_configs()
        self.record_counters = {}
    
    def _load_table_configs(self) -> Dict[str, Dict]:
        """加载所有表的配置文件"""
        configs = {}
        config_dir = settings.CONFIG_FILE_PATH
        
        # 如果配置目录不存在，创建它
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # 遍历配置目录下的所有JSON文件
        for filename in os.listdir(config_dir):
            if filename.endswith('.json'):
                table_name = filename[:-5]  # 移除.json后缀
                with open(os.path.join(config_dir, filename), 'r', encoding='utf-8') as f:
                    configs[table_name] = json.load(f)
        
        return configs
    
    def get_available_tables(self) -> List[str]:
        """获取所有可生成数据的表名"""
        return list(self.table_configs.keys())
    
    async def generate_data_for_tables(
        self, 
        tables: Optional[List[str]], 
        records_per_day: int, 
        start_date: datetime.date, 
        end_date: datetime.date
    ) -> int:
        """为指定的表生成数据"""
        # 如果未指定表，生成所有配置的表的数据
        if not tables:
            tables = self.get_available_tables()
        
        # 按依赖关系排序表
        tables = self._sort_tables_by_dependency(tables)
        
        # 从数据库初始化计数器
        await self.initialize_counters_from_db()

        total_records = 0
        
        # 计算日期范围
        current_date = start_date
        while current_date <= end_date:
            # 根据日期和时间确定当天的记录数量
            actual_records = self._calculate_actual_records(current_date, records_per_day)
            
            # 为每个表生成数据
            for table_name in tables:
                if table_name in self.table_configs:
                    table_records = await self._generate_table_data(
                        table_name, 
                        actual_records, 
                        current_date
                    )
                    total_records += table_records
            
            # 移动到下一天
            current_date += timedelta(days=1)
        
        return total_records
    
    async def initialize_counters_from_db(self):
        """从数据库中初始化计数器，获取每个表的最大ID值"""
        for table_name, config in self.table_configs.items():
            for field_name, field_config in config['fields'].items():
                if field_config.get('generator') == 'incremental':
                    try:
                        # 查询表中的最大ID值
                        query = f"SELECT MAX({field_name}) FROM {table_name}"
                        result = await database.fetch_val(query=query)
                        counter_key = f"{table_name}_{field_name}"
                        # 如果表中有数据，则使用最大ID值作为计数器初始值，否则使用0
                        self.record_counters[counter_key] = result if result is not None else 0
                        print(f"表 {table_name} 字段 {field_name} 的计数器已初始化为: {self.record_counters[counter_key]}")
                    except Exception as e:
                        # 如果表不存在或查询失败，保持计数器为0
                        counter_key = f"{table_name}_{field_name}"
                        self.record_counters[counter_key] = 0
                        print(f"表 {table_name} 字段 {field_name} 计数器初始化失败: {e}")
    
    def _calculate_actual_records(self, date: datetime.date, base_records: int) -> int:
        """根据日期和时间规律计算实际生成的记录数量"""
        # 检查是否是高峰期日期
        is_peak_day = date.weekday() + 1 in settings.PEAK_DAYS  # weekday()返回0-6，对应周一到周日
        
        # 在高峰期日期，增加10-50%的记录数
        if is_peak_day:
            multiplier = 1.0 + random.uniform(0.1, 0.5)
            return int(base_records * multiplier)
        
        return base_records
    
    async def _generate_table_data(
        self, 
        table_name: str, 
        record_count: int, 
        current_date: datetime.date
    ) -> int:
        """为单个表生成数据并插入数据库"""
        # 确保表存在
        table_exists = await table_manager.ensure_table_exists(table_name)
        if not table_exists:
            print(f"❌ 无法为表 {table_name} 生成数据：表不存在且创建失败")
            return 0
        
        config = self.table_configs[table_name]
        generated_count = 0
        
        # 准备插入语句
        columns = list(config['fields'].keys())
        # 使用PostgreSQL标准的位置参数格式($1, $2, ...)
        placeholders = [f"${i+1}" for i, _ in enumerate(columns)]
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        # 生成记录并批量插入
        batch_size = 1000
        batch = []
        
        for _ in range(record_count):
            # 生成单条记录
            record = self._generate_record(config, table_name, current_date)
            
            # 检查是否满足关联条件
            if not self._check_relationships(record, config):
                continue
            
            batch.append(record)
            generated_count += 1
            
            # 当批次达到一定大小时，执行插入
            if len(batch) >= batch_size:
                try:
                    await database.execute_many(query=insert_query, values=batch)
                    print(f"✅ 成功插入 {len(batch)} 条记录到表 {table_name}")
                except Exception as e:
                    print(f"❌ 插入数据到表 {table_name} 时出错: {e}")
                batch = []
        
        # 插入剩余的记录
        if batch:
            try:
                await database.execute_many(query=insert_query, values=batch)
                print(f"✅ 成功插入 {len(batch)} 条记录到表 {table_name}")
            except Exception as e:
                print(f"❌ 插入数据到表 {table_name} 时出错: {e}")
        
        return generated_count
    
    def _generate_record(self, config: Dict, table_name: str, current_date: datetime.date) -> Dict[str, Any]:
        """生成单条记录"""
        record = {}
        
        # 为每个字段生成值
        for field_name, field_config in config['fields'].items():
            record[field_name] = self._generate_field_value(field_config, table_name, current_date)
        
        # 应用后处理规则
        if 'post_process' in config:
            for rule in config['post_process']:
                record = self._apply_post_process_rule(record, rule)
        
        return record
    
    def _generate_field_value(self, field_config: Dict, table_name: str, current_date: datetime.date) -> Any:
        """根据字段配置生成字段值"""
        field_type = field_config.get('type', 'string')
        field_generator = field_config.get('generator', None)
        
        # 如果有特定的生成器函数，使用它
        if field_generator:
            if field_generator == 'current_timestamp':
                # 生成符合时间规律的时间戳
                return self._generate_timestamp(current_date)
            elif field_generator == 'uuid':
                return str(self.faker.uuid4())
            elif field_generator == 'incremental':
                # 生成递增的ID
                counter_key = f"{table_name}_{field_config.get('name', 'id')}"
                if counter_key not in self.record_counters:
                    self.record_counters[counter_key] = 1
                else:
                    self.record_counters[counter_key] += 1
                return self.record_counters[counter_key]
            elif field_generator.startswith('random_choice:'):
                # 从选项中随机选择
                choices = field_generator[14:].split(',')
                selected_value = random.choice(choices)
                
                # 根据字段类型转换数据类型
                if field_type == 'integer':
                    try:
                        # 先尝试直接转换
                        return int(selected_value)
                    except (ValueError, TypeError):
                        # 如果转换失败，尝试清理字符串中的空格和引号
                        cleaned_value = selected_value.strip().strip('"').strip("'")
                        try:
                            return int(cleaned_value)
                        except (ValueError, TypeError):
                            print(f"⚠️ 警告: 无法将值 '{selected_value}' 转换为整数，使用默认值 0")
                            return 0
                elif field_type == 'decimal':
                    try:
                        return float(selected_value)
                    except (ValueError, TypeError):
                        # 如果转换失败，尝试清理字符串中的空格和引号
                        cleaned_value = selected_value.strip().strip('"').strip("'")
                        try:
                            return float(cleaned_value)
                        except (ValueError, TypeError):
                            print(f"⚠️ 警告: 无法将值 '{selected_value}' 转换为小数，使用默认值 0.0")
                            return 0.0
                elif field_type == 'boolean':
                    # 将字符串转换为布尔值
                    cleaned_value = selected_value.strip().lower()
                    if cleaned_value in ('true', '1', 'yes', 'y', 't'):
                        return True
                    elif cleaned_value in ('false', '0', 'no', 'n', 'f'):
                        return False
                    else:
                        # 尝试转换为整数再判断
                        try:
                            return bool(int(cleaned_value))
                        except (ValueError, TypeError):
                            return bool(selected_value)
                else:
                    return selected_value
            elif field_generator.startswith('reference:'):
                # 处理引用字段，格式为 reference:表名:字段名
                parts = field_generator[10:].split(':')
                if len(parts) >= 2:
                    ref_table, ref_field = parts[0], parts[1]
                    # 这里应该从已生成的记录中获取引用值
                    # 目前我们返回一个占位符，实际应用中需要更复杂的逻辑
                    return f"REF:{ref_table}:{ref_field}"
        
        # 根据字段类型生成值
        if field_type == 'string':
            return self.faker.word()
        elif field_type == 'integer':
            min_val = field_config.get('min', 0)
            max_val = field_config.get('max', 100)
            return random.randint(min_val, max_val)
        elif field_type == 'decimal':
            min_val = field_config.get('min', 0.0)
            max_val = field_config.get('max', 100.0)
            precision = field_config.get('precision', 2)
            return round(random.uniform(min_val, max_val), precision)
        elif field_type == 'boolean':
            return random.choice([True, False])
        elif field_type == 'timestamp':
            # 生成符合时间规律的时间戳
            return self._generate_timestamp(current_date)
        
        return None
    
    def _generate_timestamp(self, current_date: datetime.date) -> datetime:
        """生成符合时间规律的时间戳"""
        # 确定小时
        hour_weights = []
        for hour in range(24):
            # 高峰期时段权重更高
            if hour in settings.PEAK_HOURS:
                hour_weights.append(5)
            else:
                hour_weights.append(1)
        
        # 根据权重随机选择小时
        hour = random.choices(range(24), weights=hour_weights)[0]
        
        # 生成完整的时间戳
        return datetime(
            current_date.year,
            current_date.month,
            current_date.day,
            hour,
            random.randint(0, 59),
            random.randint(0, 59)
        )
    
    def _check_relationships(self, record: Dict, config: Dict) -> bool:
        """检查记录是否满足关联条件"""
        # 如果配置中有关系定义，检查关系是否满足
        if 'relationships' in config:
            for rel_field, rel_config in config['relationships'].items():
                # 检查关联字段是否在记录中存在
                if rel_field not in record:
                    return False
                
                # 获取关联表名和字段名
                related_table = rel_config.get('table')
                related_field = rel_config.get('field', rel_field)
                
                # 如果没有配置关联表，则跳过检查
                if not related_table:
                    continue
                
                # 检查关联表是否在配置中存在
                if related_table not in self.table_configs:
                    # 如果关联表没有配置，我们无法验证关系，暂时返回True
                    continue
                
                # 在实际应用中，这里应该查询数据库验证关联记录是否存在
                # 但在数据生成场景中，我们假设关联的数据将在适当的时候生成
                # 所以这里只做基本的非空检查
                if record[rel_field] is None:
                    return False
        
        return True
    
    def _apply_post_process_rule(self, record: Dict, rule: Dict) -> Dict:
        """应用后处理规则"""
        # 这里可以实现各种后处理逻辑，比如根据其他字段计算值
        if rule.get('type') == 'calculate':
            formula = rule.get('formula', '')
            # 简单的公式解析和计算
            # 这只是一个示例，实际应用中可能需要更复杂的表达式解析
            if formula == 'order_amount - discount_amount':
                if 'order_amount' in record and 'discount_amount' in record:
                    record['pay_amount'] = record['order_amount'] - record['discount_amount']
        
        return record
    
    async def clear_table_data(self, tables: Optional[List[str]] = None):
        """清空表数据"""
        # 如果未指定表，清空所有配置的表
        if not tables:
            tables = self.get_available_tables()
        
        # 清空每个表的数据
        for table_name in tables:
            if table_name in self.table_configs:
                # 使用TRUNCATE语句清空表，同时处理外键约束
                await database.execute(query=f"TRUNCATE TABLE {table_name} CASCADE")

    # 添加按依赖关系排序表的方法
    def _sort_tables_by_dependency(self, tables: List[str]) -> List[str]:
        """按依赖关系排序表，确保被依赖的表先生成"""
        # 构建依赖图
        graph = {}
        for table in tables:
            graph[table] = set()
            if table in self.table_configs and 'relationships' in self.table_configs[table]:
                for rel_field, rel_config in self.table_configs[table]['relationships'].items():
                    if rel_config['table'] in tables:
                        graph[table].add(rel_config['table'])
        
        # 拓扑排序
        visited = set()
        result = []
        
        def dfs(node):
            visited.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor)
            result.append(node)
        
        for node in tables:
            if node not in visited:
                dfs(node)
        
        return result
