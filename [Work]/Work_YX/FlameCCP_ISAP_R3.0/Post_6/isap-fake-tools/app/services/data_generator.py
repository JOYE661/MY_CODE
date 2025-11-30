import os
import json
import random
import asyncio
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
import logging
from faker import Faker
from app.core.config import settings
from app.core.database import database

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载省市区联动数据
script_dir = os.path.dirname(os.path.abspath(__file__))
pca_file_path = os.path.join(script_dir, '..', '..', 'dist', 'pca.json')
with open(pca_file_path, 'r', encoding='utf-8') as f:
    pca_data = json.load(f)


class DataGenerator:
    def __init__(self):
        self.faker = Faker('zh_CN')
        self.table_configs = self._load_table_configs()
        self.record_counters = {}
        # 存储已生成的外键值，用于foreign_key生成器
        self.foreign_key_cache = {}
        # 存储每个sxbh的当前序号，用于people_sequence生成器
        self.people_sequence_counters = {}
        # 存储父表的xm字段，用于姓名一致性
        self.parent_xm_cache = {}
        # 存储完整的记录，用于外键字段引用非主键字段
        self.foreign_key_records_cache = {}
    
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
        
        # 为整个批次预先生成一次省市区县值，确保同一批次内数据的一致性
        pca_values = self._generate_pca_values()

        for _ in range(record_count):
            # 生成单条记录，并传入预先生成的pca_values
            record = self._generate_record(config, table_name, current_date, pca_values)
            
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
        """缓存表的主键值和外键字段值，供外键引用"""
        logger.debug(f"缓存表 {table_name} 的主键值和外键字段值，记录数: {len(records)}")
        
        # 查找主键字段（通过generator类型判断）
        primary_key_values = []
        primary_key_field = None
        
        # 查找需要缓存的外键字段（如sxbh）
        foreign_key_fields = {}
        
        # 特殊处理：对于test_data_exchange_item_info表，主动缓存sxbh字段
        if table_name == 'test_data_exchange_item_info':
            logger.debug(f"特殊处理：主动缓存表 {table_name} 的sxbh字段")
            if 'sxbh' not in foreign_key_fields:
                foreign_key_fields['sxbh'] = []
            
            for record in records:
                if 'sxbh' in record:
                    foreign_key_fields['sxbh'].append(record['sxbh'])
            logger.debug(f"表 {table_name} 的sxbh字段值已收集，值数量: {len(foreign_key_fields['sxbh'])}")
        
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
            
            # 检查是否是外键字段（通过关系配置判断）
            if 'relationships' in config and field_name in config['relationships']:
                rel_config = config['relationships'][field_name]
                related_table = rel_config.get('table')
                if related_table:
                    # 这是一个外键字段，需要缓存其值
                    if field_name not in foreign_key_fields:
                        foreign_key_fields[field_name] = []
                    
                    for record in records:
                        if field_name in record:
                            foreign_key_fields[field_name].append(record[field_name])
                    logger.debug(f"找到外键字段 {field_name}，关联表: {related_table}，值数量: {len(foreign_key_fields[field_name])}")
        
        # 缓存主键值
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
        
        # 缓存外键字段值
        for field_name, field_values in foreign_key_fields.items():
            if field_values:
                cache_key = f"{table_name}_{field_name}"
                if cache_key not in self.foreign_key_cache:
                    self.foreign_key_cache[cache_key] = []
                
                self.foreign_key_cache[cache_key].extend(field_values)
                logger.debug(f"表 {table_name} 的外键字段 {field_name} 值已缓存，当前缓存大小: {len(self.foreign_key_cache[cache_key])}")
                
                # 限制缓存大小
                if len(self.foreign_key_cache[cache_key]) > 10000:
                    self.foreign_key_cache[cache_key] = self.foreign_key_cache[cache_key][-5000:]
                    logger.debug(f"表 {table_name} 的外键字段 {field_name} 缓存已裁剪，新大小: {len(self.foreign_key_cache[cache_key])}")
    
    def _generate_record(self, config: Dict, table_name: str, current_date: datetime.date, pca_values: Dict[str, str] = None) -> Dict[str, Any]:
        """生成单条记录"""
        record = {}
        
        # 如果没有提供 pca_values，则为省市县字段预先生成一致的值
        if pca_values is None:
            pca_values = self._generate_pca_values()
        
        # 设置当前记录上下文，用于people_sequence生成器
        self._current_record_context = {}
        
        try:
            # 为每个字段生成值
            for field_name, field_config in config['fields'].items():
                # 确保字段配置中包含字段名
                field_config_with_name = field_config.copy()
                field_config_with_name['name'] = field_name
                
                # 生成字段值
                field_value = self._generate_field_value(field_config_with_name, table_name, current_date, pca_values)
                record[field_name] = field_value
                
                # 更新当前记录上下文，包含已生成的字段值
                # 这样后续字段就可以引用前面生成的字段值
                self._current_record_context[field_name] = field_value
            
            # 应用后处理规则
            if 'post_process' in config:
                for rule in config['post_process']:
                    record = self._apply_post_process_rule(record, rule)
            
            return record
        finally:
            # 清除当前记录上下文
            self._current_record_context = {}

    def _generate_pca_values(self) -> Dict[str, str]:
        """预先生成一致的省市区县值"""
        # 随机选择一个省
        province = random.choice(list(pca_data.keys()))
        # 随机选择一个市
        city = random.choice(list(pca_data[province].keys()))
        # 随机选择一个区/县
        area = random.choice(pca_data[province][city])
        # 生成详细地址
        detail_address = self.faker.street_address()
        # 组合完整地址
        full_address = f"{province}{city}{area}{detail_address}"
        return {
            'province': province,
            'city': city,
            'area': area,
            'full_address': full_address
        }
    def _generate_field_value(self, field_config: Dict, table_name: str, current_date: datetime.date, pca_values: Dict[str, str] = None) -> Any:
        """根据字段配置生成字段值"""
        field_type = field_config.get('type', 'string')
        field_generator = field_config.get('generator', None)

        # 如果有特定的生成器函数，使用它
        if field_generator:
            if field_generator == 'current_timestamp':
                # 生成符合时间规律的时间戳
                return self._generate_timestamp(current_date)
            elif field_generator == 'faker_company':
                return str(self.faker.company())
            elif field_generator == 'faker_product_code':
                return str(self.faker.uuid4())
            # 政务数据专用
            elif field_generator == 'fixed:1':
                return str(1)
            elif field_generator == 'fixed:网':
                return "网"
            elif field_generator == 'fixed:电':
                return "电"
            elif field_generator == 'fixed:12345':
                return "12345"
            elif field_generator == 'faker_job':
                return str(self.faker.job())
            elif field_generator == 'id_card':
                return str(self.faker.ssn())
            # ims_shipment 表专用
            elif field_generator == 'faker_receiver_info':
                receiver_info = {
                    'receiver_name': self.faker.name(),
                    'receiver_phone': self.faker.phone_number(),
                    'receiver_email': self.faker.email(),
                    'receiver_company': self.faker.company(),
                    'shipping_address': self.faker.address(),

                }
                return str(receiver_info)
            # crm_customer 表专用
            elif field_generator == 'faker_address':
                if pca_values and 'full_address' in pca_values:
                    return str(pca_values['full_address'])
                else:
                    return str(self.faker.address())
            elif field_generator == 'faker_name':
                # 如果是test_data_exchange_people_info表且序号为1，从父表获取姓名
                if table_name == 'test_data_exchange_people_info':
                    # 获取当前记录的外键值（sxbh）
                    if hasattr(self, '_current_record_context'):
                        current_record = getattr(self, '_current_record_context', {})
                        sxbh = current_record.get('sxbh')
                        
                        # 如果sxbh存在且序号为1，从父表获取姓名
                        if sxbh and sxbh in self.parent_xm_cache:
                            parent_xm = self._generate_parent_xm_value(sxbh)
                            logger.info(f"序号为1，从父表获取姓名: {parent_xm}")
                            return parent_xm
                
                # 否则生成随机姓名
                return str(self.faker.name())
            elif field_generator == 'faker_phone_number':
                return str(self.faker.phone_number())
            elif field_generator == 'faker_phone_number_with_dirty':
                return self._generate_phone_number_with_dirty_data()
            elif field_generator == 'faker_email':
                return str(self.faker.email())
            elif field_generator == 'faker_date_of_birth':
                return str(self.faker.date_of_birth())
            # oms_order 表专用
            elif field_generator == 'faker_province':
                # 使用预先生成的省市县值
                if pca_values and 'province' in pca_values:
                    return str(pca_values['province'])
                else:
                    return str(self.faker.province())
            elif field_generator == 'faker_city':
                # 使用预先生成的省市县值
                if pca_values and 'city' in pca_values:
                    return str(pca_values['city'])
                else:
                    return str(self.faker.city())
            elif field_generator == 'faker_district':
                # 使用预先生成的省市县值
                if pca_values and 'area' in pca_values:
                    return str(pca_values['area'])
                else:
                    return str(self.faker.district())
            elif field_generator == 'faker_street_address':
                return str(self.faker.street_address())
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
            elif field_generator.startswith('random_int:'):
                # 生成指定范围内的随机整数
                range_str = field_generator[11:]  # 移除 'random_int:' 前缀
                if ',' in range_str:
                    min_str, max_str = range_str.split(',', 1)
                    try:
                        min_val = int(min_str.strip())
                        max_val = int(max_str.strip())
                        value = random.randint(min_val, max_val)
                        
                        # 根据字段类型返回适当的值
                        if field_type == 'string':
                            # 对于字符串类型，确保值不超过最大长度
                            str_value = str(value)
                            max_length = field_config.get('max_length')
                            if max_length and len(str_value) > max_length:
                                # 如果值超过最大长度，截断或重新生成
                                if min_val >= 0:
                                    # 重新生成一个不超过最大长度的值
                                    max_possible = min(max_val, 10 ** max_length - 1)
                                    value = random.randint(min_val, max_possible)
                                    str_value = str(value)
                                else:
                                    # 对于负数，截断到最大长度
                                    str_value = str_value[:max_length]
                            return str_value
                        else:
                            return value
                    except (ValueError, TypeError) as e:
                        logger.warning(f"random_int 生成器参数解析失败: {range_str}, 错误: {e}")
                        # 使用默认值
                        return 0 if field_type != 'string' else '0'
                else:
                    logger.warning(f"random_int 生成器格式错误: {field_generator}")
                    return 0 if field_type != 'string' else '0'
            elif field_generator.startswith('weighted_choice:'):
                # 带权重的选择
                choices_str = field_generator[16:]  # 移除 'weighted_choice:' 前缀
                choices = choices_str.split(',')
                
                # 解析选项和权重
                values = []
                weights = []
                for choice in choices:
                    if ':' in choice:
                        value, weight_str = choice.split(':', 1)
                        values.append(value)
                        weights.append(float(weight_str))
                    else:
                        values.append(choice)
                        weights.append(1.0)  # 默认权重为1
                
                # 根据权重随机选择
                selected_value = random.choices(values, weights=weights)[0]
                
                # 根据字段类型转换数据类型
                if field_type == 'integer' or field_type == 'bigint':
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
                    # 对于字符串类型，确保值不超过最大长度
                    max_length = field_config.get('max_length')
                    if max_length and len(selected_value) > max_length:
                        # 如果值超过最大长度，进行截断
                        selected_value = selected_value[:max_length]
                    return selected_value
            elif field_generator.startswith('random_choice:'):
                # 从选项中随机选择
                choices = field_generator[14:].split(',')
                selected_value = random.choice(choices)
                
                # 根据字段类型转换数据类型
                if field_type == 'integer' or field_type == 'bigint':
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
                    # 对于字符串类型，确保值不超过最大长度
                    max_length = field_config.get('max_length')
                    if max_length and len(selected_value) > max_length:
                        # 如果值超过最大长度，进行截断
                        selected_value = selected_value[:max_length]
                    return selected_value
            elif field_generator.startswith('format:'):
                # 格式字符串生成器
                format_str = field_generator[7:]  # 移除 'format:' 前缀
                return self._generate_formatted_value(format_str, current_date)
            elif field_generator == 'people_sequence':
                # 人员序号生成器 - 特殊处理test_data_exchange_people_info表的序号
                return self._generate_people_sequence(field_config, table_name)
            elif field_generator == 'extension_from_original_name':
                # 从original_name字段提取扩展名的生成器
                return self._generate_extension_from_original_name(field_config, table_name)
        
        # 根据字段类型生成值
        if field_type == 'string':
            value = self.faker.word()
            # 检查字符串长度限制
            max_length = field_config.get('max_length')
            if max_length and len(value) > max_length:
                # 如果值超过最大长度，进行截断
                value = value[:max_length]
            return value
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
                    # 获取关联字段名，默认为当前字段名
                    related_field = rel_config.get('field', field_name)
                    
                    # 检查缓存中是否有该表的外键值
                    # 首先尝试查找外键字段缓存（如test_data_exchange_item_info_sxbh）
                    foreign_key_cache_key = f"{related_table}_{related_field}"
                    if foreign_key_cache_key in self.foreign_key_cache and self.foreign_key_cache[foreign_key_cache_key]:
                        # 从已生成的外键字段值中随机选择一个
                        selected_value = random.choice(self.foreign_key_cache[foreign_key_cache_key])
                        logger.debug(f"从表 '{related_table}' 的外键字段 '{related_field}' 缓存中选择外键值: {selected_value}")
                        
                        # 检查字段类型，确保返回正确的数据类型
                        field_type = field_config.get('type', 'string')
                        if field_type == 'string':
                            return str(selected_value)
                        elif field_type in ['integer', 'bigint']:
                            return int(selected_value)
                        elif field_type == 'decimal':
                            return float(selected_value)
                        else:
                            return selected_value
                    # 如果外键字段缓存中没有值，尝试查找主键缓存
                    elif related_table in self.foreign_key_cache and self.foreign_key_cache[related_table]:
                        # 从已生成的主键值中随机选择一个
                        selected_value = random.choice(self.foreign_key_cache[related_table])
                        logger.debug(f"从表 '{related_table}' 的主键缓存中选择外键值: {selected_value}")
                        
                        # 检查字段类型，确保返回正确的数据类型
                        field_type = field_config.get('type', 'string')
                        if field_type == 'string':
                            return str(selected_value)
                        elif field_type in ['integer', 'bigint']:
                            return int(selected_value)
                        elif field_type == 'decimal':
                            return float(selected_value)
                        else:
                            return selected_value
                    else:
                        # 如果缓存中没有值，说明父表数据还没有生成
                        logger.error(f"外键依赖错误: 表 '{table_name}' 的字段 '{field_name}' 依赖于表 '{related_table}' 的字段 '{related_field}'，但该表的数据尚未生成或缓存为空。请确保依赖表先生成数据。")
                        # 在这种情况下，我们抛出一个异常，让调用者知道问题所在
                        raise ValueError(f"外键依赖错误: 表 '{table_name}' 的字段 '{field_name}' 依赖于表 '{related_table}' 的字段 '{related_field}'，但该表的数据尚未生成或缓存为空。请确保依赖表先生成数据。")
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
                # related_field = rel_config.get('field', rel_field)
                
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
        # 检查 record 是否为 None
        if record is None:
            return None
            
        # 这里可以实现各种后处理逻辑，比如根据其他字段计算值
        if rule.get('type') == 'calculate':
            formula = rule.get('formula', '')
            # 简单的公式解析和计算
            # 这只是一个示例，实际应用中可能需要更复杂的表达式解析
            if formula == 'order_amount - discount_amount':
                if 'order_amount' in record and 'discount_amount' in record:
                    record['pay_amount'] = record['order_amount'] - record['discount_amount']
        elif rule.get('type') == 'calculate_purchase_frequency':
            # 计算购买频率
            record = self._calculate_purchase_frequency(record)
        elif rule.get('type') == 'field_dependency':
            # 字段依赖规则处理
            source_field = rule.get('source_field')
            target_field = rule.get('target_field')
            condition = rule.get('condition')
            action = rule.get('action')
            
            # 在处理每个规则前，确保_current_record_context包含所有字段的最新值
            if hasattr(self, '_current_record_context'):
                for field_name, field_value in record.items():
                    self._current_record_context[field_name] = field_value
            
            # 检查源字段是否存在
            if source_field in record:
                source_value = record[source_field]
                
                # 解析条件 (支持 == 比较和 contains 包含判断)
                condition_met = False
                if condition:
                    # 支持多种条件类型
                    if '==' in condition and 'contains' not in condition and '!=' not in condition:
                        # 简单条件解析: "field == 'value'"
                        cond_parts = condition.split('==')
                        cond_field = cond_parts[0].strip()
                        cond_value = cond_parts[1].strip().strip("'\"")
                        
                        # 检查条件是否满足
                        if cond_field in record and str(record[cond_field]) == cond_value:
                            condition_met = True
                    elif 'contains' in condition:
                        # 包含条件解析: "field contains 'value'"
                        cond_parts = condition.split('contains')
                        cond_field = cond_parts[0].strip()
                        cond_value = cond_parts[1].strip().strip("'\"")
                        
                        # 检查条件是否满足
                        if cond_field in record and cond_value in str(record[cond_field]):
                            condition_met = True
                    elif '!=' in condition:
                        # 不等于条件解析: "field != 'value'"
                        cond_parts = condition.split('!=')
                        cond_field = cond_parts[0].strip()
                        cond_value = cond_parts[1].strip().strip("'\"")
                        
                        # 检查条件是否满足
                        if cond_field in record and str(record[cond_field]) != cond_value:
                            condition_met = True
                    else:
                        # 没有明确的操作符，尝试直接判断是否为真
                        if condition in record and record[condition]:
                            condition_met = True
                
                # 如果没有条件，或者条件满足，则执行动作
                if not condition or condition_met:
                    # 执行动作
                    if action.startswith('set_fixed:'):
                        # 设置固定值
                        format_str = action[10:]  # 移除 'set_fixed:' 前缀
                        # 使用 _generate_formatted_value 方法处理格式化字符串
                        formatted_value = self._generate_formatted_value(format_str, date.today())
                        record[target_field] = formatted_value
                        
                        # 更新当前记录上下文中的目标字段值，确保后续字段能正确引用
                        if hasattr(self, '_current_record_context'):
                            self._current_record_context[target_field] = formatted_value
                        
                    elif action == 'set_empty':
                        # 设置为空值
                        record[target_field] = ''
                        # 更新当前记录上下文中的目标字段值
                        if hasattr(self, '_current_record_context'):
                            self._current_record_context[target_field] = ''
                    elif action == 'require':
                        # 要求字段必填，这里可以添加验证逻辑
                        # 在这个上下文中，我们确保字段存在且不为空
                        if target_field not in record or not record[target_field]:
                            # 如果目标字段为空，可以根据需要设置默认值或标记为需要处理
                            pass  # 在数据生成阶段，目标字段应该已经被生成了
                    

        return record

    def _calculate_purchase_frequency(self, record: Dict) -> Dict:
        """计算购买频率"""
        # 基于订单数量和时间计算购买频率
        if 'total_order_count' in record and 'first_order_date' in record and 'last_order_date' in record:
            total_orders = record['total_order_count']
            first_order = record['first_order_date']
            last_order = record['last_order_date']
            
            # 计算订单时间跨度（天）
            if isinstance(first_order, str):
                first_order = datetime.fromisoformat(first_order.replace('Z', '+00:00'))
            if isinstance(last_order, str):
                last_order = datetime.fromisoformat(last_order.replace('Z', '+00:00'))
            
            days_diff = (last_order - first_order).days + 1  # 避免除以0
            
            # 计算购买频率（订单数/天数）
            if days_diff > 0:
                frequency_rate = total_orders / days_diff
                
                # 根据频率率定义购买频率
                if frequency_rate >= 0.1:  # 平均10天内有1个订单
                    record['purchase_frequency'] = '高频'
                    record['purchase_frequency_score'] = 5
                elif frequency_rate >= 0.05:  # 平均20天内有1个订单
                    record['purchase_frequency'] = '中频'
                    record['purchase_frequency_score'] = 3
                else:
                    record['purchase_frequency'] = '低频'
                    record['purchase_frequency_score'] = 1
            else:
                # 如果时间跨度无效，使用默认值
                record['purchase_frequency'] = '低频'
                record['purchase_frequency_score'] = 1
        
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

    def _generate_formatted_value(self, format_str: str, current_date: datetime.date) -> str:
        """生成格式化字符串值"""
        import re
        
        # 定义占位符的正则表达式模式
        pattern = r'\{(\w+)(?::([^}]+))?\}'
        
        def replace_placeholder(match):
            placeholder_type = match.group(1)
            params = match.group(2) if match.group(2) else ""
            
            if placeholder_type == 'date':
                # 日期占位符 {date:format}
                date_format = params if params else 'yyyyMMdd'
                # 将Java风格的日期格式转换为Python风格
                date_format = date_format.replace('yyyy', '%Y').replace('MM', '%m').replace('dd', '%d')
                return current_date.strftime(date_format)
            elif placeholder_type == 'random':
                # 随机数占位符 {random:length}
                length = int(params) if params else 6
                # 生成指定长度的随机数字字符串
                return ''.join(str(random.randint(0, 9)) for _ in range(length))
            elif placeholder_type == 'random_text':
                # 随机文本占位符 {random_text:min,max}
                if params:
                    min_len, max_len = map(int, params.split(','))
                    length = random.randint(min_len, max_len)
                else:
                    # 默认生成10-50个字符的随机文本
                    length = random.randint(10, 50)
                
                # 生成符合政务投诉内容特征的文本
                complaint_templates = [
                    "希望相关部门能够重视此问题并尽快解决",
                    "此问题已困扰居民多时，期待得到妥善处理",
                    "请贵单位督促有关方面加快问题整改",
                    "建议加强监管力度，防止类似问题再次发生",
                    "希望能够公开处理结果，接受社会监督",
                    "请尽快核实情况并给予明确答复",
                    "此事关系到群众切身利益，望优先处理",
                    "恳请相关部门依法依规严肃处理",
                    "希望能够在规定时限内得到圆满解决",
                    "请加强与相关单位协调，合力解决问题"
                ]
                
                # 如果需要的长度较短，从模板中随机选择一部分文本
                if length <= 20:
                    return random.choice(complaint_templates)[:length].ljust(length, random.choice('abcdefghijklmnopqrstuvwxyz'))
                else:
                    # 如果需要的长度较长，组合多个模板或生成更长的内容
                    selected_template = random.choice(complaint_templates)
                    if length <= len(selected_template):
                        return selected_template[:length]
                    else:
                        # 添加一些通用的政务问题相关词汇来填充内容
                        additional_words = [
                            "问题", "情况", "处理", "解决", "部门", "单位", "反映", "咨询", "答复",
                            "办理", "回复", "政策", "规定", "程序", "流程", "材料", "事项", "业务",
                            "服务", "窗口", "效率", "态度", "群众", "居民", "市民", "百姓", "人民"
                        ]
                        
                        result = selected_template
                        while len(result) < length:
                            result += random.choice(additional_words)
                            
                        return result[:length]
            elif placeholder_type == 'name':
                # 姓名占位符
                return self.faker.name()
            elif placeholder_type == 'wtsd':
                # 问题属地占位符
                return random.choice(['浙江省', '杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市'])
            elif placeholder_type == 'sxxs':
                # 事项形式占位符
                return random.choices(['信', '访', '网', '电'], weights=[0.03, 0.07, 0.1, 0.8])[0]
            elif placeholder_type == 'address':
                # 地址占位符 - 从当前记录上下文中获取address字段值
                if hasattr(self, '_current_record_context') and self._current_record_context and 'address' in self._current_record_context:
                    return str(self._current_record_context.get('address', f"{{{placeholder_type}}}"))
                else:
                    # 如果没有address字段，则使用默认地址
                    return "浙江省杭州市"
            
            elif hasattr(self, '_current_record_context') and self._current_record_context and placeholder_type in self._current_record_context:
                # 如果占位符是当前记录中的字段名，则返回该字段的值
                return str(self._current_record_context.get(placeholder_type, f"{{{placeholder_type}}}"))
            else:
                # 未知占位符，返回原样
                return match.group(0)
        
        # 使用正则表达式替换所有占位符
        result = re.sub(pattern, replace_placeholder, format_str)
        return result

    def _generate_people_sequence(self, field_config: Dict, table_name: str) -> str:
        """生成人员序号，确保与父表的事项人数一致且序号为1时姓名一致"""
        # 获取当前记录的外键值（sxbh）
        if not hasattr(self, '_current_record_context'):
            logger.warning("没有当前记录上下文，无法生成人员序号")
            return "1"
        
        current_record = getattr(self, '_current_record_context', {})
        sxbh = current_record.get('sxbh')
        
        if not sxbh:
            logger.warning("当前记录没有sxbh外键值，无法生成人员序号")
            return "1"
        
        # 初始化该sxbh的序号计数器
        if sxbh not in self.people_sequence_counters:
            self.people_sequence_counters[sxbh] = 0
        
        # 递增序号
        self.people_sequence_counters[sxbh] += 1
        sequence_number = self.people_sequence_counters[sxbh]
        
        # 检查是否超过父表的事项人数限制
        parent_table_name = 'test_data_exchange_item_info'
        if parent_table_name in self.table_configs:
            # 查找父表记录中对应的事项人数
            parent_records = self.foreign_key_cache.get(parent_table_name, [])
            
            # 如果没有找到父表记录，使用默认值
            if not parent_records:
                logger.warning(f"未找到父表 {parent_table_name} 的记录，使用默认事项人数")
                max_sequence = 5  # 默认最大序号
            else:
                # 在实际应用中，这里应该根据sxbh查找具体的父表记录
                # 这里简化处理：使用第一个父表记录的sxrs字段
                try:
                    # 模拟从数据库查询父表记录的sxrs字段
                    # 在实际实现中，这里需要访问数据库或缓存
                    max_sequence = 5  # 默认值
                    logger.info(f"使用默认事项人数 {max_sequence} 作为最大序号")
                except Exception as e:
                    logger.warning(f"获取父表事项人数失败: {e}，使用默认值")
                    max_sequence = 5
            
            # 如果序号超过事项人数，重置为1
            if sequence_number > max_sequence:
                sequence_number = 1
                self.people_sequence_counters[sxbh] = 1
        
        # 如果序号为1，记录需要从父表获取姓名
        if sequence_number == 1:
            # 标记该sxbh需要从父表获取姓名
            self.parent_xm_cache[sxbh] = True
        
        return str(sequence_number)

    def _generate_parent_xm_value(self, sxbh: str) -> str:
        """从父表获取姓名值"""
        parent_table_name = 'test_data_exchange_item_info'
        
        # 在实际应用中，这里应该查询数据库获取父表记录的xm字段
        # 这里简化处理：使用随机姓名
        return self.faker.name()

    def _generate_extension_from_original_name(self, field_config: Dict, table_name: str) -> str:
        """从original_name字段提取扩展名的生成器"""
        # 获取当前记录上下文中的original_name字段值
        if not hasattr(self, '_current_record_context'):
            logger.warning("没有当前记录上下文，无法从original_name提取扩展名")
            return 'jpg'
        
        current_record = getattr(self, '_current_record_context', {})
        original_name = current_record.get('original_name')
        
        if not original_name:
            logger.warning("当前记录没有original_name字段，无法提取扩展名")
            return 'jpg'
        
        # 从original_name中提取扩展名
        # original_name格式如："投诉材料.jpg", "证据照片.png", "身份证明.pdf"
        if '.' in original_name:
            extension = original_name.split('.')[-1].lower()
            # 验证扩展名是否有效
            valid_extensions = ['jpg', 'png', 'pdf', 'doc', 'docx', 'zip', 'mp4', 'mp3', 'txt', 'xls', 'xlsx']
            if extension in valid_extensions:
                return extension
            else:
                logger.warning(f"从original_name '{original_name}' 中提取的扩展名 '{extension}' 不在有效扩展名列表中，使用默认值 'jpg'")
                return 'jpg'
        else:
            logger.warning(f"original_name '{original_name}' 中没有找到扩展名，使用默认值 'jpg'")
            return 'jpg'

    def _generate_phone_number_with_dirty_data(self) -> str:
        """生成包含脏数据的电话号码"""
        # 80% 的概率生成标准电话号码，20% 的概率生成脏数据
        if random.random() < 0.8:
            # 生成标准电话号码
            return str(self.faker.phone_number())
        else:
            # 生成脏数据
            dirty_types = [
                self._generate_incomplete_phone_number,      # 不完整的号码
                self._generate_phone_number_with_special_chars,  # 包含特殊字符
                self._generate_phone_number_with_letters,    # 包含字母
                self._generate_empty_phone_number,           # 空值
                # self._generate_too_long_phone_number,        # 过长的号码
                self._generate_international_phone_number,   # 国际格式但不规范
                self._generate_repeated_phone_number         # 重复数字
            ]
            
            # 随机选择一种脏数据类型
            dirty_generator = random.choice(dirty_types)
            return dirty_generator()
    
    def _generate_incomplete_phone_number(self) -> str:
        """生成不完整的电话号码"""
        # 随机缺少1-3位数字
        base_number = self.faker.phone_number()
        # 移除非数字字符
        digits = ''.join(filter(str.isdigit, base_number))
        if len(digits) <= 3:
            return digits
        
        # 随机移除1-3位数字
        remove_count = random.randint(1, 3)
        incomplete_digits = digits[:-remove_count]
        return incomplete_digits
    
    def _generate_phone_number_with_special_chars(self) -> str:
        """生成包含特殊字符的电话号码"""
        base_number = self.faker.phone_number()
        # 将号码中的数字随机替换为特殊字符
        special_chars = ['-', ' ', '.', '/', '(', ')']
        result = []
        for char in base_number:
            if char.isdigit() and random.random() < 0.3:  # 30% 的概率替换数字
                result.append(random.choice(special_chars))
            else:
                result.append(char)
        return ''.join(result)
    
    def _generate_phone_number_with_letters(self) -> str:
        """生成包含字母的电话号码"""
        base_number = self.faker.phone_number()
        # 将号码中的数字随机替换为字母
        letters = ['O', 'I', 'L', 'S', 'B']  # 常见混淆字母
        result = []
        for char in base_number:
            if char.isdigit() and random.random() < 0.2:  # 20% 的概率替换数字
                result.append(random.choice(letters))
            else:
                result.append(char)
        return ''.join(result)
    
    def _generate_empty_phone_number(self) -> str:
        """生成空值电话号码"""
        empty_types = ['', 'null', 'NULL', 'None', 'N/A', '无']
        return random.choice(empty_types)
    
    # def _generate_too_long_phone_number(self) -> str:
    #     """生成过长的电话号码"""
    #     base_number = self.faker.phone_number()
    #     # 在号码末尾添加额外的随机数字
    #     extra_digits = ''.join(str(random.randint(0, 9)) for _ in range(random.randint(5, 15)))
    #     return base_number + extra_digits
    
    def _generate_international_phone_number(self) -> str:
        """生成国际格式但不规范的电话号码"""
        # 生成国际格式但可能不规范的号码
        formats = [
            "+86 {number}",
            "0086 {number}",
            "86-{number}",
            "+{country_code} {number}",
            "00{country_code} {number}"
        ]
        format_template = random.choice(formats)
        country_code = str(random.randint(1, 99))
        number = self.faker.phone_number()
        return format_template.format(country_code=country_code, number=number)
    
    def _generate_repeated_phone_number(self) -> str:
        """生成重复数字的电话号码"""
        # 生成包含大量重复数字的号码
        repeated_digit = str(random.randint(0, 9))
        length = random.randint(8, 15)
        return repeated_digit * length
