import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from faker import Faker
from app.core.config import settings
from app.core.database import database

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataGenerator:
    def __init__(self):
        self.faker = Faker('zh_CN')
        self.table_configs = self._load_table_configs()
        self.record_counters = {}
        # 存储已生成的外键值，用于foreign_key生成器
        self.foreign_key_cache = {}
    
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
                    except Exception as e:
                        # 如果表不存在或查询失败，保持计数器为0
                        counter_key = f"{table_name}_{field_name}"
                        self.record_counters[counter_key] = 0
    
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
        """为指定的表生成数据 - 使用分阶段生成确保外键依赖正确"""
        logger.info("开始 generate_data_for_tables 方法")
        try:
            # 如果未指定表，生成所有配置的表的数据
            if not tables:
                tables = self.get_available_tables()
            
            # 分离独立表和依赖表
            independent_tables, dependent_tables = self._separate_tables_by_dependency(tables)
            logger.info(f"独立表（阶段1）: {independent_tables}")
            logger.info(f"依赖表（阶段2）: {dependent_tables}")
            
            # 从数据库初始化计数器
            logger.info("初始化数据库计数器")
            await self.initialize_counters_from_db()
            logger.info(f"计数器初始化完成: {self.record_counters}")

            total_records = 0
            
            # 计算日期范围
            current_date = start_date
            while current_date <= end_date:
                logger.info(f"开始处理日期: {current_date}")
                # 根据日期和时间确定当天的记录数量
                actual_records = self._calculate_actual_records(current_date, records_per_day)
                logger.info(f"当天计划生成记录数: {actual_records}")
                
                # 清空外键缓存，确保每次生成都是全新的
                self.foreign_key_cache.clear()
                logger.info("已清空外键缓存")
                
                # 阶段1：生成独立表（没有外键依赖的表）
                logger.info("=== 阶段1：生成独立表 ===")
                for table_name in independent_tables:
                    if table_name in self.table_configs:
                        logger.info(f"开始为独立表 {table_name} 生成数据")
                        table_records = await self._generate_table_data(
                            table_name, 
                            actual_records, 
                            current_date
                        )
                        total_records += table_records
                        logger.info(f"独立表 {table_name} 生成完成，记录数: {table_records}")
                
                # 阶段2：生成依赖表（有外键依赖的表）
                logger.info("=== 阶段2：生成依赖表 ===")
                # 按依赖关系排序依赖表
                sorted_dependent_tables = self._sort_tables_by_dependency(dependent_tables)
                logger.info(f"排序后的依赖表: {sorted_dependent_tables}")
                for table_name in sorted_dependent_tables:
                    if table_name in self.table_configs:
                        logger.info(f"开始为依赖表 {table_name} 生成数据")
                        table_records = await self._generate_table_data(
                            table_name, 
                            actual_records, 
                            current_date
                        )
                        total_records += table_records
                        logger.info(f"依赖表 {table_name} 生成完成，记录数: {table_records}")
                
                # 移动到下一天
                current_date += timedelta(days=1)
            
            logger.info(f"数据生成完成，总记录数: {total_records}")
            return total_records
        except Exception as e:
            logger.error(f"generate_data_for_tables 方法执行失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise e
        finally:
            logger.info("退出 generate_data_for_tables 方法")
    
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
            
            # 当批次达到一定大小时，执行插入并立即缓存
            if len(batch) >= batch_size:
                await database.execute_many(query=insert_query, values=batch)
                # 插入成功后，立即缓存主键值，确保子表可以引用
                self._cache_primary_key_values(table_name, batch, config)
                batch = []
                logger.info(f"表 {table_name} 已插入 {batch_size} 条记录并缓存主键值")
        
        # 插入剩余的记录
        if batch:
            await database.execute_many(query=insert_query, values=batch)
            # 插入成功后，立即缓存主键值
            self._cache_primary_key_values(table_name, batch, config)
            logger.info(f"表 {table_name} 已插入剩余 {len(batch)} 条记录并缓存主键值")
        
        return generated_count
    
    def _cache_primary_key_values(self, table_name: str, records: List[Dict], config: Dict):
        """缓存表的主键值，供外键引用"""
        logger.debug(f"缓存表 {table_name} 的主键值，记录数: {len(records)}")
        
        # 查找主键字段（通过generator类型判断）
        primary_key_values = []
        primary_key_field = None
        
        for field_name, field_config in config['fields'].items():
            # 检查是否是主键字段（通过generator类型判断）
            generator_type = field_config.get('generator')
            if generator_type in ['uuid', 'incremental']:
                primary_key_field = field_name
                # 收集所有记录的主键值
                for record in records:
                    if field_name in record:
                        primary_key_values.append(record[field_name])
                logger.debug(f"找到主键字段 {field_name}，类型: {generator_type}，值数量: {len(primary_key_values)}")
                break
        
        # 如果找到了主键字段，将其值缓存起来
        if primary_key_field and primary_key_values:
            # 确保该表在缓存中有条目
            if table_name not in self.foreign_key_cache:
                self.foreign_key_cache[table_name] = []
            
            # 将所有记录的主键值添加到外键缓存中
            self.foreign_key_cache[table_name].extend(primary_key_values)
            logger.debug(f"表 {table_name} 的主键值已缓存，当前缓存大小: {len(self.foreign_key_cache[table_name])}")
            
            # 限制缓存大小，避免内存占用过大
            if len(self.foreign_key_cache[table_name]) > 10000:
                self.foreign_key_cache[table_name] = self.foreign_key_cache[table_name][-5000:]
                logger.debug(f"表 {table_name} 的主键缓存已裁剪，新大小: {len(self.foreign_key_cache[table_name])}")
        else:
            logger.debug(f"表 {table_name} 没有找到主键字段或没有主键值")
    
    def _generate_record(self, config: Dict, table_name: str, current_date: datetime.date) -> Dict[str, Any]:
        """生成单条记录"""
        record = {}
        
        # 为每个字段生成值
        for field_name, field_config in config['fields'].items():
            # 确保字段配置中包含字段名
            field_config_with_name = field_config.copy()
            field_config_with_name['name'] = field_name
            record[field_name] = self._generate_field_value(field_config_with_name, table_name, current_date)
        
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
            elif field_generator == 'foreign_key':
                # 生成外键值 - 从已生成的父表记录中选择
                return self._generate_foreign_key_value(field_config, table_name)
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
    
    def _generate_foreign_key_value(self, field_config: Dict, table_name: str) -> Any:
        """生成外键字段的值"""
        # 查找该表的配置中是否有外键关系定义
        field_name = field_config.get('name')
        if not field_name:
            # 如果没有字段名，返回默认UUID
            logger.warning(f"外键字段没有指定字段名，生成默认UUID")
            return str(self.faker.uuid4())
            
        if table_name in self.table_configs:
            table_config = self.table_configs[table_name]
            if 'relationships' in table_config:
                # 查找当前字段的外键关系
                if field_name in table_config['relationships']:
                    rel_config = table_config['relationships'][field_name]
                    # 获取关联表名
                    related_table = rel_config.get('table')
                    # 检查缓存中是否有该表的外键值
                    if related_table in self.foreign_key_cache and self.foreign_key_cache[related_table]:
                        # 从已生成的外键值中随机选择一个
                        selected_value = random.choice(self.foreign_key_cache[related_table])
                        logger.debug(f"从表 '{related_table}' 的缓存中选择外键值: {selected_value}")
                        return selected_value
                    else:
                        # 如果缓存中没有值，说明父表数据还没有生成
                        logger.error(f"外键依赖错误: 表 '{table_name}' 的字段 '{field_name}' 依赖于表 '{related_table}'，但该表的数据尚未生成或缓存为空。请确保依赖表先生成数据。")
                        # 在这种情况下，我们抛出一个异常，让调用者知道问题所在
                        raise ValueError(f"外键依赖错误: 表 '{table_name}' 的字段 '{field_name}' 依赖于表 '{related_table}'，但该表的数据尚未生成或缓存为空。请确保依赖表先生成数据。")
                else:
                    logger.warning(f"字段 '{field_name}' 在表 '{table_name}' 的关系配置中未找到")
            else:
                logger.warning(f"表 '{table_name}' 没有关系配置")
        else:
            logger.warning(f"表 '{table_name}' 不在配置中")
        
        # 如果没有找到外键关系定义，返回一个默认的UUID
        logger.warning(f"未找到外键关系定义，生成默认UUID")
        return str(self.faker.uuid4())
    
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
        logger.info("进入 clear_table_data 方法")
        try:
            logger.info("开始清空表数据")
            # 如果未指定表，清空所有配置的表
            if not tables:
                tables = self.get_available_tables()
            
            # 按依赖关系反向排序表（先清除子表，再清除父表）
            tables = self._sort_tables_by_dependency(tables)
            tables.reverse()
            
            logger.info(f"准备清除以下表的数据: {tables}")
            
            # 清空每个表的数据
            cleared_tables = []
            failed_tables = []
            
            for table_name in tables:
                if table_name in self.table_configs:
                    success = False
                    try:
                        logger.info(f"尝试使用 TRUNCATE 清除表 {table_name}...")
                        # 使用TRUNCATE语句清空表，同时处理外键约束
                        await database.execute(query=f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
                        logger.info(f"TRUNCATE 表 {table_name} 成功")
                        success = True
                    except Exception as e:
                        logger.warning(f"TRUNCATE {table_name} 失败: {e}")
                        try:
                            logger.info(f"尝试使用 DELETE 清除表 {table_name}...")
                            # 如果TRUNCATE失败，尝试使用DELETE
                            await database.execute(query=f"DELETE FROM {table_name}")
                            logger.info(f"DELETE 表 {table_name} 成功")
                            # 尝试重置自增序列
                            try:
                                sequence_reset_query = f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1"
                                await database.execute(query=sequence_reset_query)
                                logger.info(f"重置序列 {table_name}_id_seq 成功")
                            except Exception as seq_error:
                                logger.warning(f"重置序列 {table_name}_id_seq 失败: {seq_error}")
                                # 尝试另一种方式查找并重置序列
                                try:
                                    find_seq_query = """
                                        SELECT pg_get_serial_sequence($1, 'id')
                                    """
                                    seq_name = await database.fetch_val(query=find_seq_query, values=[table_name])
                                    if seq_name:
                                        await database.execute(query=f"ALTER SEQUENCE {seq_name} RESTART WITH 1")
                                        logger.info(f"通过查询找到序列 {seq_name} 并重置成功")
                                    else:
                                        logger.info("未找到相关序列")
                                except Exception as find_seq_error:
                                    logger.warning(f"查找并重置序列失败: {find_seq_error}")
                            success = True
                        except Exception as delete_error:
                            logger.error(f"DELETE {table_name} 也失败了: {delete_error}")
                            failed_tables.append((table_name, str(delete_error)))
                    
                    if success:
                        cleared_tables.append(table_name)
                else:
                    logger.warning(f"表 {table_name} 不在配置中，跳过")
            
            logger.info(f"成功清除 {len(cleared_tables)} 个表: {cleared_tables}")
            if failed_tables:
                logger.error(f"清除失败的表 {len(failed_tables)} 个:")
                for table_name, error in failed_tables:
                    logger.error(f"  - {table_name}: {error}")
                # 如果有任何表清除失败，抛出异常
                raise Exception(f"清除表数据失败: {failed_tables}")
            logger.info("表数据清空完成")
        except Exception as e:
            logger.error(f"clear_table_data 方法执行失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise e
        finally:
            logger.info("退出 clear_table_data 方法")

    # 添加按依赖关系排序表的方法
    def _sort_tables_by_dependency(self, tables: List[str]) -> List[str]:
        """按依赖关系排序表，确保被依赖的表先生成"""
        # 构建依赖图
        graph = {table: set() for table in tables}
        in_degree = {table: 0 for table in tables}
        
        # 分析表之间的依赖关系
        for table in tables:
            if table in self.table_configs and 'relationships' in self.table_configs[table]:
                for rel_field, rel_config in self.table_configs[table]['relationships'].items():
                    related_table = rel_config.get('table')
                    # 如果依赖的表也在待处理表列表中，则建立依赖关系
                    if related_table in tables:
                        graph[related_table].add(table)  # related_table -> table (related_table依赖于table)
                        in_degree[table] += 1
        
        # 拓扑排序 (Kahn算法)
        # 找到所有入度为0的节点（没有依赖的表）
        queue = [table for table in tables if in_degree[table] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # 对于当前节点的每个依赖项，减少其入度
            for dependent in graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # 检查是否存在循环依赖
        if len(result) != len(tables):
            # 存在循环依赖或依赖表不在当前处理列表中，记录警告信息
            missing_deps = set(tables) - set(result)
            if missing_deps:
                logger.warning(f"检测到循环依赖或缺少依赖表: {missing_deps}")
            # 返回原始顺序
            return tables
            
        logger.info(f"表依赖排序结果: {result}")
        return result

    def _separate_tables_by_dependency(self, tables: List[str]) -> tuple[List[str], List[str]]:
        """将表分为独立表（无外键依赖）和依赖表（有外键依赖）"""
        independent_tables = []
        dependent_tables = []
        
        for table in tables:
            if table in self.table_configs:
                config = self.table_configs[table]
                # 检查表是否定义了外键关系
                if 'relationships' in config and config['relationships']:
                    dependent_tables.append(table)
                else:
                    independent_tables.append(table)
            else:
                # 如果表不在配置中，默认认为是独立表
                independent_tables.append(table)
        
        return independent_tables, dependent_tables

    async def _verify_stage1_data(self, independent_tables: List[str]):
        """验证阶段1数据已正确插入数据库"""
        logger.info("验证阶段1数据插入情况...")
        
        for table_name in independent_tables:
            if table_name in self.table_configs:
                try:
                    # 查询表中是否有数据
                    query = f"SELECT COUNT(*) FROM {table_name}"
                    count = await database.fetch_val(query=query)
                    logger.info(f"表 {table_name} 数据验证: 存在 {count} 条记录")
                    
                    if count == 0:
                        logger.warning(f"表 {table_name} 没有数据，但应该已经在阶段1生成")
                    
                    # 验证主键值是否已缓存
                    if table_name in self.foreign_key_cache:
                        logger.info(f"表 {table_name} 主键缓存: {len(self.foreign_key_cache[table_name])} 个值")
                    else:
                        logger.warning(f"表 {table_name} 主键缓存为空")
                        
                except Exception as e:
                    logger.error(f"验证表 {table_name} 数据失败: {e}")
        
        logger.info("阶段1数据验证完成")
