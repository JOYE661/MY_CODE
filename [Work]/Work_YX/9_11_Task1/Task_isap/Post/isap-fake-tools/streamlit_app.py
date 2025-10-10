import streamlit as st
import asyncio
from datetime import datetime, timedelta, date
import os
from app.services.data_generator import DataGenerator
from app.core.database import database
from app.core.config import settings

# 设置中文字体支持
st.set_page_config(
    page_title="数据生成器控制面板",
    page_icon=":bar_chart:",
    layout="wide"
)

# 异步运行器
class AsyncRunner:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def run(self, coro):
        return self.loop.run_until_complete(coro)

# 初始化异步运行器
async_runner = AsyncRunner()

# 初始化数据生成器
@st.cache_resource
def init_data_generator():
    generator = DataGenerator()
    return generator

# 数据库连接管理
@st.cache_resource
def init_database():
    async_runner.run(database.connect())
    return database

# 主应用界面
def main():
    st.title("📊 ISAP 数据生成器控制面板")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置项")
        
        # 数据库连接状态
        db_status = st.empty()
        
        db_status.success(f"✅ 已连接到数据库: {settings.POSTGRES_DB}")
        # 数据生成器
        generator = init_data_generator()
        
        # 显示数据库信息
        st.subheader("数据库信息")
        st.text(f"主机: {settings.POSTGRES_SERVER}")
        st.text(f"端口: {settings.POSTGRES_PORT}")
        st.text(f"用户: {settings.POSTGRES_USER}")
        
        # 可用表选择
        available_tables = generator.get_available_tables()
        
        if not available_tables:
            st.warning("⚠️ 未找到任何表配置文件")
            st.stop()
        
        # 表选择
        st.subheader("选择表")
        selected_tables = st.multiselect(
            "请选择要生成数据的表:",
            available_tables,
            default=available_tables
        )
        
        # 生成参数配置
        st.subheader("数据生成参数")
        
        # 记录数配置
        records_per_day = st.slider(
            "每天生成的记录数:",
            min_value=1, 
            max_value=10000, 
            value=100,
            step=10
        )
        
        # 日期范围选择
        st.subheader("日期范围")
        today = date.today()
        start_date = st.date_input(
            "开始日期:",
            today - timedelta(days=7)
        )
        end_date = st.date_input(
            "结束日期:",
            today
        )
        
        # 操作按钮
        st.subheader("操作")
        generate_btn = st.button("🚀 生成数据", type="primary", use_container_width=True)
        clear_btn = st.button("🧹 清空数据", use_container_width=True)
    
    # 主内容区
    st.divider()
    st.header("📈 数据生成状态")
    
    # 日志显示区域
    log_container = st.container()
    with log_container:
        log_text = st.empty()
        log_messages = []
        
        def log(message):
            log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            log_text.text_area("日志输出", "\n".join(log_messages), height=400)
        
        # 数据生成操作
        if generate_btn:
            if not selected_tables:
                st.error("请至少选择一个表")
            else:
                with st.spinner("正在生成数据..."):
                    try:
                        log(f"开始为表 {', '.join(selected_tables)} 生成数据")
                        log(f"参数: 每天{records_per_day}条记录, 日期范围: {start_date} 至 {end_date}")
                        
                        # 执行数据生成
                        total_records = async_runner.run(
                            generator.generate_data_for_tables(
                                selected_tables,
                                records_per_day,
                                start_date,
                                end_date
                            )
                        )
                        
                        log(f"✅ 数据生成完成! 共生成 {total_records} 条记录")
                        st.success(f"数据生成完成! 共生成 {total_records} 条记录")
                    except Exception as e:
                        log(f"❌ 数据生成失败: {str(e)}")
                        st.error(f"数据生成失败: {str(e)}")
        
        # 清空数据操作
        if clear_btn:
            if not selected_tables:
                st.error("请至少选择一个表")
            else:
                # 二次确认
                if st.button("⚠️ 确认清空数据? 此操作不可恢复!"):
                    with st.spinner("正在清空数据..."):
                        try:
                            log(f"开始清空表 {', '.join(selected_tables)} 的数据")
                            
                            # 执行清空数据
                            async_runner.run(
                                generator.clear_table_data(selected_tables)
                            )
                            
                            log(f"✅ 数据清空完成!")
                            st.success("数据清空完成!")
                        except Exception as e:
                            log(f"❌ 数据清空失败: {str(e)}")
                            st.error(f"数据清空失败: {str(e)}")
    
    # 表结构信息
    st.divider()
    st.header("📋 表结构信息")
    
    if selected_tables:
        for table_name in selected_tables:
            with st.expander(f"表: {table_name}"):
                if table_name in generator.table_configs:
                    config = generator.table_configs[table_name]
                    
                    # 显示字段信息
                    st.subheader("字段列表")
                    fields = config['fields']
                    
                    # 创建字段信息表格
                    field_data = []
                    for field_name, field_config in fields.items():
                        field_type = field_config.get('type', '未知')
                        generator_type = field_config.get('generator', '默认')
                        field_data.append({
                            "字段名": field_name,
                            "类型": field_type,
                            "生成器": generator_type
                        })
                    
                    st.dataframe(field_data, use_container_width=True)
                    
                    # 显示关系信息
                    if 'relationships' in config and config['relationships']:
                        st.subheader("关联关系")
                        rel_data = []
                        for rel_field, rel_config in config['relationships'].items():
                            rel_table = rel_config.get('table', '未知')
                            rel_field_name = rel_config.get('field', '未知')
                            rel_data.append({
                                "字段": rel_field,
                                "关联表": rel_table,
                                "关联字段": rel_field_name
                            })
                        st.dataframe(rel_data, use_container_width=True)
                    
                    # 显示后处理规则
                    if 'post_process' in config and config['post_process']:
                        st.subheader("后处理规则")
                        for rule in config['post_process']:
                            st.text(f"类型: {rule.get('type')}, 公式: {rule.get('formula')}")

# 应用退出时关闭数据库连接
def on_app_close():
    try:
        async_runner.run(database.disconnect())
    except:
        pass

if __name__ == "__main__":
    try:
        main()
    finally:
        on_app_close()