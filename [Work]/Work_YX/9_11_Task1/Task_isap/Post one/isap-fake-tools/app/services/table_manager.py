import os
import re
from typing import Dict, List, Optional
from app.core.database import database
from app.core.config import settings

class TableManager:
    """表结构管理类，负责检查、创建和更新数据库表结构"""
    
    def __init__(self):
        self.sql_file_path = "demo.sql"
        self.table_creation_cache = {}  # 缓存已检查的表
    
    async def ensure_table_exists(self, table_name: str) -> bool:
        """确保表存在，如果不存在则创建"""
        # 检查缓存
        if table_name in self.table_creation_cache:
            return self.table_creation_cache[table_name]
        
        # 检查表是否存在
        table_exists = await self._check_table_exists(table_name)
        
        if table_exists:
            self.table_creation_cache[table_name] = True
            return True
        
        # 表不存在，尝试创建
        success = await self._create_table(table_name)
        self.table_creation_cache[table_name] = success
        
        if success:
            print(f"✅ 表 {table_name} 创建成功")
        else:
            print(f"❌ 表 {table_name} 创建失败")
        
        return success
    
    async def _check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            # PostgreSQL 检查表是否存在
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                );
            """
            result = await database.fetchall(query, table_name)
            exists = result[0]['exists'] if result else False
            return exists
        except Exception as e:
            print(f"检查表 {table_name} 是否存在时出错: {e}")
            return False
    
    async def _create_table(self, table_name: str) -> bool:
        """创建表"""
        try:
            # 从 demo.sql 中提取建表语句
            create_table_sql = self._extract_create_table_sql(table_name)
            
            if not create_table_sql:
                print(f"❌ 未找到表 {table_name} 的建表语句")
                return False
            
            # 执行建表语句
            await database.execute(create_table_sql)
            print(f"✅ 成功执行表 {table_name} 的建表语句")
            return True
            
        except Exception as e:
            print(f"❌ 创建表 {table_name} 时出错: {e}")
            return False
    
    def _extract_create_table_sql(self, table_name: str) -> Optional[str]:
        """从 demo.sql 中提取指定表的建表语句"""
        try:
            if not os.path.exists(self.sql_file_path):
                print(f"❌ SQL 文件不存在: {self.sql_file_path}")
                return None
            
            with open(self.sql_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用正则表达式匹配 CREATE TABLE 语句
            # 匹配模式：CREATE TABLE table_name ( ... );
            pattern = rf'CREATE TABLE {table_name}\s*\([^;]+\);'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            
            if match:
                create_table_sql = match.group(0)
                
                # 检查是否有外键约束，如果有，先创建没有外键约束的版本
                if 'REFERENCES' in create_table_sql:
                    print(f"⚠️  表 {table_name} 包含外键约束，尝试创建简化版本")
                    # 移除外键约束，先创建表结构
                    simplified_sql = re.sub(r',\s*[^,]*REFERENCES[^,)]*', '', create_table_sql)
                    create_table_sql = simplified_sql
                
                # 查找相关的 COMMENT 语句
                comment_pattern = rf'COMMENT ON TABLE {table_name}[^;]+;'
                comment_matches = re.findall(comment_pattern, content, re.IGNORECASE | re.DOTALL)
                
                # 组合 CREATE TABLE 和 COMMENT 语句
                full_sql = create_table_sql
                for comment_sql in comment_matches:
                    full_sql += '\n' + comment_sql
                
                return full_sql
            else:
                print(f"❌ 在 demo.sql 中未找到表 {table_name} 的建表语句")
                return None
                
        except Exception as e:
            print(f"❌ 解析 SQL 文件时出错: {e}")
            return None
    
    async def initialize_all_tables(self) -> Dict[str, bool]:
        """初始化所有在 configs 目录中有配置文件的表"""
        config_dir = settings.CONFIG_FILE_PATH
        results = {}
        
        if not os.path.exists(config_dir):
            print(f"❌ 配置目录不存在: {config_dir}")
            return results
        
        # 获取所有配置文件对应的表名
        table_names = []
        for filename in os.listdir(config_dir):
            if filename.endswith('.json'):
                table_name = filename[:-5]  # 移除 .json 后缀
                table_names.append(table_name)
        
        print(f"🔍 发现 {len(table_names)} 个需要初始化的表: {', '.join(table_names)}")
        
        # 按依赖关系排序表
        sorted_tables = self._sort_tables_by_dependency(table_names)
        print(f"📋 按依赖关系排序后的表: {', '.join(sorted_tables)}")
        
        # 初始化每个表
        for table_name in sorted_tables:
            success = await self.ensure_table_exists(table_name)
            results[table_name] = success
        
        return results
    
    def _sort_tables_by_dependency(self, table_names: List[str]) -> List[str]:
        """按依赖关系排序表，确保被依赖的表先生成"""
        # 构建依赖图
        dependency_graph = {}
        
        for table_name in table_names:
            dependency_graph[table_name] = set()
            
            # 从SQL文件中提取该表的依赖关系
            create_sql = self._extract_create_table_sql(table_name)
            if create_sql and 'REFERENCES' in create_sql:
                # 查找所有被引用的表
                references = re.findall(r'REFERENCES\s+(\w+)', create_sql)
                for ref_table in references:
                    if ref_table in table_names:
                        dependency_graph[table_name].add(ref_table)
        
        # 拓扑排序
        visited = set()
        result = []
        
        def dfs(node):
            visited.add(node)
            for neighbor in dependency_graph[node]:
                if neighbor not in visited:
                    dfs(neighbor)
            result.append(node)
        
        for node in table_names:
            if node not in visited:
                dfs(node)
        
        return result
    
    async def get_table_status(self) -> Dict[str, Dict]:
        """获取所有表的当前状态"""
        config_dir = settings.CONFIG_FILE_PATH
        status = {}
        
        if not os.path.exists(config_dir):
            return status
        
        # 获取所有配置文件对应的表名
        table_names = []
        for filename in os.listdir(config_dir):
            if filename.endswith('.json'):
                table_name = filename[:-5]
                table_names.append(table_name)
        
        # 检查每个表的状态
        for table_name in table_names:
            exists = await self._check_table_exists(table_name)
            status[table_name] = {
                'exists': exists,
                'config_file': f"{table_name}.json",
                'message': '表已存在' if exists else '表不存在'
            }
        
        return status

# 创建全局实例
table_manager = TableManager()
