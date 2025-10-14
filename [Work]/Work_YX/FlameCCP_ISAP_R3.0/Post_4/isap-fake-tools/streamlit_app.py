import streamlit as st
import asyncio
import subprocess
import os
import signal
import psutil
import json
import uuid
import re
from datetime import datetime, timedelta, date
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

# 初始化多任务管理器
@st.cache_resource
def init_multi_task_manager():
    return MultiTaskManager()

class BackgroundServiceManager:
    @staticmethod
    def is_service_running():
        """检查后台服务是否正在运行"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'background_generator.py' in ' '.join(proc.info['cmdline']) and 'continuous' in proc.info['cmdline']:
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False, None
    
    @staticmethod
    def start_service(interval_seconds=1, records_per_batch=1, selected_tables=None):
        """启动后台服务"""
        try:
            # 构造表参数
            if selected_tables is None or len(selected_tables) == 0:
                table_param = "all"
            else:
                table_param = ",".join(selected_tables)
            
            # 使用nohup启动后台服务
            cmd = [
                'nohup', 'python3', 'background_generator.py', 
                'continuous', str(interval_seconds), str(records_per_batch), table_param
            ]
            process = subprocess.Popen(
                cmd,
                stdout=open('background_service.log', 'a'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            return True, process.pid
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def stop_service():
        """停止后台服务"""
        is_running, pid = BackgroundServiceManager.is_service_running()
        if is_running and pid:
            try:
                # 终止进程组
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                time.sleep(2)  # 等待进程终止
                return True, "后台服务已停止"
            except Exception as e:
                return False, f"停止服务时出错: {str(e)}"
        return False, "后台服务未运行"

class MultiTaskManager:
    def __init__(self):
        self.tasks_file = 'logs/background_tasks.json'
        self.load_tasks()
    
    def load_tasks(self):
        """从文件加载任务列表"""
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            else:
                self.tasks = []
        except Exception:
            self.tasks = []
    
    def save_tasks(self):
        """保存任务列表到文件"""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务列表失败: {e}")
    
    def get_running_tasks(self):
        """获取所有运行中的任务"""
        running_tasks = []
        current_pids = set()
        
        # 更新任务状态
        for task in self.tasks:
            if task.get('status') == 'running':
                pid = task.get('pid')
                if pid and self.is_process_running(pid):
                    task['status'] = 'running'
                    current_pids.add(pid)
                    running_tasks.append(task)
                else:
                    task['status'] = 'stopped'
        
        # 检查是否有新的进程在运行
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.info['cmdline'] and 
                    'background_generator.py' in ' '.join(proc.info['cmdline']) and 
                    'continuous' in proc.info['cmdline'] and
                    proc.info['pid'] not in current_pids):
                    
                    # 提取任务信息
                    cmdline = ' '.join(proc.info['cmdline'])
                    task_id_match = re.search(r'task_id=([a-f0-9-]+)', cmdline)
                    task_id = task_id_match.group(1) if task_id_match else str(uuid.uuid4())[:8]
                    
                    # 提取参数
                    interval_match = re.search(r'continuous\s+(\d+)', cmdline)
                    records_match = re.search(r'continuous\s+\d+\s+(\d+)', cmdline)
                    tables_match = re.search(r'continuous\s+\d+\s+\d+\s+([^\s]+)', cmdline)
                    
                    new_task = {
                        'task_id': task_id,
                        'pid': proc.info['pid'],
                        'status': 'running',
                        'interval_seconds': int(interval_match.group(1)) if interval_match else 30,
                        'records_per_batch': int(records_match.group(1)) if records_match else 10,
                        'tables': tables_match.group(1).split(',') if tables_match and tables_match.group(1) != 'all' else [],
                        'start_time': datetime.now().isoformat()
                    }
                    
                    running_tasks.append(new_task)
                    self.tasks.append(new_task)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        self.save_tasks()
        return running_tasks
    
    def is_process_running(self, pid):
        """检查进程是否在运行"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    def start_task(self, interval_seconds=30, records_per_batch=10, selected_tables=None):
        """启动一个新的后台任务"""
        try:
            # 生成唯一任务ID
            task_id = str(uuid.uuid4())[:8]
            
            # 构造表参数
            if selected_tables is None or len(selected_tables) == 0:
                table_param = "all"
            else:
                table_param = ",".join(selected_tables)
            
            # 使用nohup启动后台服务，传递任务ID
            cmd = [
                'nohup', 'python3', 'background_generator.py', 
                'continuous', str(interval_seconds), str(records_per_batch), table_param, task_id
            ]
            process = subprocess.Popen(
                cmd,
                stdout=open(f'logs/background_service_{task_id}.log', 'a'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )
            
            # 记录任务信息
            task_info = {
                'task_id': task_id,
                'pid': process.pid,
                'status': 'running',
                'interval_seconds': interval_seconds,
                'records_per_batch': records_per_batch,
                'tables': selected_tables or [],
                'start_time': datetime.now().isoformat(),
                'log_file': f'logs/background_service_{task_id}.log'
            }
            
            self.tasks.append(task_info)
            self.save_tasks()
            
            return True, task_id, process.pid
        except Exception as e:
            return False, str(e), None
    
    def stop_task(self, task_id):
        """停止指定的后台任务"""
        try:
            task_to_stop = None
            for task in self.tasks:
                if task.get('task_id') == task_id and task.get('status') == 'running':
                    task_to_stop = task
                    break
            
            if task_to_stop and task_to_stop.get('pid'):
                pid = task_to_stop['pid']
                try:
                    # 终止进程组
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    time.sleep(2)  # 等待进程终止
                    
                    # 更新任务状态
                    task_to_stop['status'] = 'stopped'
                    task_to_stop['end_time'] = datetime.now().isoformat()
                    self.save_tasks()
                    
                    return True, f"任务 {task_id} 已停止"
                except Exception as e:
                    return False, f"停止任务 {task_id} 时出错: {str(e)}"
            
            return False, f"未找到运行中的任务 {task_id}"
        except Exception as e:
            return False, f"停止任务时出错: {str(e)}"
    
    def stop_all_tasks(self):
        """停止所有运行中的任务"""
        running_tasks = self.get_running_tasks()
        results = []
        
        for task in running_tasks:
            success, message = self.stop_task(task['task_id'])
            results.append({
                'task_id': task['task_id'],
                'success': success,
                'message': message
            })
        
        return results
    
    def get_task_logs(self, task_id, lines=50):
        """获取任务的日志内容"""
        try:
            log_file = f'background_service_{task_id}.log'
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                    return ''.join(log_lines[-lines:])
            return "暂无日志"
        except Exception as e:
            return f"读取日志失败: {str(e)}"

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
        continuous_mode = st.checkbox("启用页面内持续生成")
        # 设置默认值
        interval_seconds = 1
        records_per_batch = 1
        if continuous_mode:
            interval_seconds = st.number_input("生成间隔(秒)", min_value=1, value=30)
            records_per_batch = st.number_input("每次生成记录数", min_value=1, value=10)
        
        # 多任务后台服务控制
        st.subheader("多任务后台服务")
        task_manager = init_multi_task_manager()
        
        # 显示运行中的任务
        running_tasks = task_manager.get_running_tasks()
        
        if running_tasks:
            st.success(f"✅ 当前有 {len(running_tasks)} 个任务正在运行")
            
            # 显示每个运行中的任务
            for task in running_tasks:
                with st.expander(f"任务 {task['task_id']}", expanded=True):
                    # 计算运行时长
                    start_time = datetime.fromisoformat(task['start_time'])
                    duration = datetime.now() - start_time
                    hours, remainder = divmod(duration.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    st.write(f"**任务ID:** {task['task_id']}")
                    st.write(f"**PID:** {task['pid']}")
                    st.write(f"**运行时长:** {int(hours)}时{int(minutes)}分{int(seconds)}秒")
                    st.write(f"**间隔:** {task['interval_seconds']}秒")
                    st.write(f"**每批记录数:** {task['records_per_batch']}")
                    st.write(f"**表:** {', '.join(task['tables']) if task['tables'] else '所有表'}")
                    
                    # 停止按钮
                    if st.button(f"⏹️ 停止任务 {task['task_id']}", key=f"stop_{task['task_id']}"):
                        success, message = task_manager.stop_task(task['task_id'])
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                        time.sleep(1)
                        st.rerun()
        else:
            st.warning("⚠️ 没有运行中的后台任务")
        
        # 启动新任务
        st.write("启动新任务:")
        new_task_interval = st.number_input("生成间隔(秒)", min_value=1, value=30, key="new_task_interval")
        new_task_records = st.number_input("每次生成记录数", min_value=1, value=10, key="new_task_records")
        
        if st.button("▶️ 启动新后台任务"):
            success, task_id, pid = task_manager.start_task(
                new_task_interval, new_task_records, selected_tables
            )
            if success:
                st.success(f"后台任务已启动 (任务ID: {task_id}, PID: {pid})")
            else:
                st.error(f"启动任务失败: {task_id}")
            time.sleep(1)
            st.rerun()
        
        # 停止所有任务按钮
        if running_tasks:
            if st.button("🛑 停止所有任务", type="secondary", use_container_width=True):
                results = task_manager.stop_all_tasks()
                for result in results:
                    if result['success']:
                        st.success(result['message'])
                    else:
                        st.error(result['message'])
                time.sleep(1)
                st.rerun()
        
        # 操作按钮
        st.subheader("操作")
        generate_btn = st.button("🚀 生成数据", type="primary", use_container_width=True)
        # generate_everyday_btn = st.button("📅 每天生成数据", use_container_width=True)
        clear_btn = st.button("🧹 清空数据", use_container_width=True)

    
    # 主内容区
    st.divider()
    st.header("📈 数据生成状态")
    
    # 显示后台服务状态
    is_running, pid = BackgroundServiceManager.is_service_running()
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        if is_running:
            st.success("✅ 后台服务正在运行")
        else:
            st.warning("⚠️ 后台服务未运行")
    with status_col2:
        if os.path.exists('logs/background_service.log'):
            log_size = os.path.getsize('logs/background_service.log')
            st.info(f"日志文件大小: {log_size} 字节")
    
    # 初始化会话状态
    if 'clear_confirmed' not in st.session_state:
        st.session_state.clear_confirmed = False
    if 'clear_in_progress' not in st.session_state:
        st.session_state.clear_in_progress = False
    if 'continuous_generation_active' in st.session_state:
        del st.session_state.continuous_generation_active  # 移除旧的状态
    if 'continuous_generation_count' in st.session_state:
        del st.session_state.continuous_generation_count  # 移除旧的状态

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
        
        # 持续生成数据操作 (保留给页面内的临时生成)
        if continuous_mode and selected_tables:
            start_continuous_btn = st.button("开始持续生成(页面内)", type="primary", use_container_width=True)
            stop_continuous_btn = st.button("停止持续生成(页面内)", use_container_width=True)
            
            if start_continuous_btn:
                st.session_state.temp_continuous_active = True
                st.session_state.temp_continuous_count = 0
                st.rerun()
            
            if stop_continuous_btn:
                st.session_state.temp_continuous_active = False
                st.rerun()
            
            # 持续生成逻辑
            if st.session_state.get('temp_continuous_active', False):
                log(f"开始页面内持续生成数据，间隔 {interval_seconds} 秒，每次生成 {records_per_batch} 条记录")
                st.info(f"页面内持续生成进行中... 间隔 {interval_seconds} 秒，每次生成 {records_per_batch} 条记录")
                
                # 创建一个空容器用于显示批次数量和生成结果，避免页面闪烁
                if 'temp_continuous_status_container' not in st.session_state:
                    st.session_state.temp_continuous_status_container = st.empty()
                
                # 初始化上次生成时间
                if 'temp_last_generation_time' not in st.session_state:
                    st.session_state.temp_last_generation_time = time.time()
                
                # 在容器中显示已生成的批次数量
                status_container = st.session_state.temp_continuous_status_container
                count = st.session_state.get('temp_continuous_count', 0)
                status_container.write(f"已生成批次数量: {count}")
                
                # 检查是否到了生成时间
                current_time = time.time()
                if current_time - st.session_state.temp_last_generation_time >= interval_seconds:
                    try:
                        # 为今天生成一批数据
                        today = date.today()
                        log(f"正在生成批次 #{count + 1}...")
                        
                        # 执行数据生成（仅为今天生成records_per_batch条记录）
                        total_records = async_runner.run(
                            generator.generate_data_for_tables(
                                selected_tables,
                                records_per_batch,  # 使用每批次的记录数而不是每天的记录数
                                today,
                                today
                            )
                        )
                        
                        st.session_state.temp_continuous_count = count + 1
                        st.session_state.temp_last_generation_time = current_time
                        # 更新容器中的信息
                        status_container.write(f"已生成批次数量: {st.session_state.temp_continuous_count}")
                        log(f"✅ 批次 #{st.session_state.temp_continuous_count} 生成完成! 生成了 {total_records} 条记录")
                        
                    except Exception as e:
                        log(f"❌ 持续生成失败: {str(e)}")
                        st.error(f"持续生成失败: {str(e)}")
                
                # 使用time.sleep等待下次生成，而不是刷新整个页面
                # 这样可以避免页面闪烁，同时保持持续生成的效果
                time.sleep(1)
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
