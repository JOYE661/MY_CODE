import streamlit as st
import asyncio
from datetime import datetime, timedelta, date
import os
import time
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
        
        # 持续生成配置
        st.subheader("持续生成配置")
        continuous_mode = st.checkbox("启用持续生成模式")
        if continuous_mode:
            interval_seconds = st.number_input("生成间隔(秒)", min_value=1, value=30)
            records_per_batch = st.number_input("每次生成记录数", min_value=1, value=10)
        
        # 操作按钮
        st.subheader("操作")
        generate_btn = st.button("🚀 生成数据", type="primary", use_container_width=True)
        # generate_everyday_btn = st.button("📅 每天生成数据", use_container_width=True)
        clear_btn = st.button("🧹 清空数据", use_container_width=True)

    
    # 主内容区
    st.divider()
    st.header("📈 数据生成状态")
    
    # 初始化会话状态
    if 'clear_confirmed' not in st.session_state:
        st.session_state.clear_confirmed = False
    if 'clear_in_progress' not in st.session_state:
        st.session_state.clear_in_progress = False
    if 'continuous_generation_active' not in st.session_state:
        st.session_state.continuous_generation_active = False
    if 'continuous_generation_count' not in st.session_state:
        st.session_state.continuous_generation_count = 0
    
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
        
        # 持续生成数据操作
        if continuous_mode and selected_tables:
            start_continuous_btn = st.button("开始持续生成", type="primary", use_container_width=True)
            stop_continuous_btn = st.button("停止持续生成", use_container_width=True)
            
            if start_continuous_btn:
                st.session_state.continuous_generation_active = True
                st.session_state.continuous_generation_count = 0
                st.rerun()
            
            if stop_continuous_btn:
                st.session_state.continuous_generation_active = False
                st.rerun()
            
            # 持续生成逻辑
            if st.session_state.continuous_generation_active:
                log(f"开始持续生成数据，间隔 {interval_seconds} 秒，每次生成 {records_per_batch} 条记录")
                st.info(f"持续生成进行中... 间隔 {interval_seconds} 秒，每次生成 {records_per_batch} 条记录")
                
                # 创建一个空容器用于显示批次数量和生成结果，避免页面闪烁
                if 'continuous_status_container' not in st.session_state:
                    st.session_state.continuous_status_container = st.empty()
                
                # 初始化上次生成时间
                if 'last_generation_time' not in st.session_state:
                    st.session_state.last_generation_time = time.time()
                
                # 在容器中显示已生成的批次数量
                status_container = st.session_state.continuous_status_container
                status_container.write(f"已生成批次数量: {st.session_state.continuous_generation_count}")
                
                # 检查是否到了生成时间
                current_time = time.time()
                if current_time - st.session_state.last_generation_time >= interval_seconds:
                    try:
                        # 为今天生成一批数据
                        today = date.today()
                        log(f"正在生成批次 #{st.session_state.continuous_generation_count + 1}...")
                        
                        # 执行数据生成（仅为今天生成records_per_batch条记录）
                        total_records = async_runner.run(
                            generator.generate_data_for_tables(
                                selected_tables,
                                records_per_batch,  # 使用每批次的记录数而不是每天的记录数
                                today,
                                today
                            )
                        )
                        
                        st.session_state.continuous_generation_count += 1
                        st.session_state.last_generation_time = current_time
                        # 更新容器中的信息
                        status_container.write(f"已生成批次数量: {st.session_state.continuous_generation_count}")
                        log(f"✅ 批次 #{st.session_state.continuous_generation_count} 生成完成! 生成了 {total_records} 条记录")
                        
                    except Exception as e:
                        log(f"❌ 持续生成失败: {str(e)}")
                        st.error(f"持续生成失败: {str(e)}")
                
                # 使用time.sleep等待下次生成，而不是刷新整个页面
                # 这样可以避免页面闪烁，同时保持持续生成的效果
                time.sleep(interval_seconds)
                st.rerun()
        
        # 清空数据操作 - 使用会话状态管理确认流程
        if clear_btn and not st.session_state.clear_confirmed:
            st.session_state.clear_confirmed = True
            st.session_state.clear_in_progress = False
        
        if st.session_state.clear_confirmed and not st.session_state.clear_in_progress:
            st.warning("⚠️ 确认要清空数据吗？此操作不可恢复！")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认清空", type="primary", use_container_width=True):
                    st.session_state.clear_in_progress = True
            with col2:
                if st.button("❌ 取消", use_container_width=True):
                    st.session_state.clear_confirmed = False
                    st.session_state.clear_in_progress = False
                    st.rerun()
        
        if st.session_state.clear_in_progress:
            if not selected_tables:
                st.error("请至少选择一个表")
                st.session_state.clear_in_progress = False
                st.session_state.clear_confirmed = False
            else:
                with st.spinner("正在清空数据..."):
                    try:
                        log(f"开始清空表 {', '.join(selected_tables)} 的数据")
                        
                        # 执行清空数据
                        log("调用数据生成器的clear_table_data方法")
                        async_runner.run(
                            generator.clear_table_data(selected_tables)
                        )
                        log("clear_table_data方法执行完成")
                        
                        log(f"✅ 数据清空完成!")
                        st.success("数据清空完成!")
                        
                        # 重置状态
                        st.session_state.clear_confirmed = False
                        st.session_state.clear_in_progress = False
                        st.session_state.continuous_generation_active = False
                        st.session_state.continuous_generation_count = 0
                        
                    except Exception as e:
                        log(f"❌ 数据清空失败: {str(e)}")
                        import traceback
                        log(f"❌ 错误详情: {traceback.format_exc()}")
                        st.error(f"数据清空失败: {str(e)}")
                        
                        # 重置状态
                        st.session_state.clear_confirmed = False
                        st.session_state.clear_in_progress = False
    
    # 表结构信息n
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