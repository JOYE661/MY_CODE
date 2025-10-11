import requests
import threading
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import testIP   # 确保test_csd模块可用

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 创建线程安全的会话对象
def create_session():
    session = requests.Session()
    # 设置连接池大小
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 全局会话对象
session = create_session()

def get_log_files(directory='.'):
    """获取当前目录下所有的.log文件"""
    try:
        return [f for f in os.listdir(directory) if f.endswith('.log')]
    except Exception as e:
        logger.error(f"获取日志文件列表失败: {str(e)}")
        return []

def validate_proxy(proxy_ip):
    """验证代理是否可用"""
    proxies = {'https': f'https://{proxy_ip}'}
    url = 'https://www.baidu.com'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Connection': 'close'  # 每次请求后关闭连接
    }
    
    try:
        # 使用全局会话对象
        response = session.get(
            url, 
            proxies=proxies, 
            headers=headers, 
            timeout=10,  # 总超时10秒
            verify=False  # 忽略SSL证书验证
        )
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"代理验证失败: {proxy_ip} - {type(e).__name__}")
        return False

def execute_task(proxy_ip):
    """执行后台任务"""
    # 生成日志文件名
    log_filename = proxy_ip.replace('.', '_').replace(':', '_') + '.log'
    log_path = os.path.join(os.getcwd(), log_filename)
    
    # 检查日志文件是否已存在
    if os.path.exists(log_path):
        logger.info(f"跳过已执行任务: {proxy_ip} (日志文件存在)")
        return
    
    # 构建执行命令
    command = f"nohup python3 -u csdn_request3.py {proxy_ip} > {log_filename} 2>&1 &"
    
    try:
        # 执行命令
        exit_code = os.system(command)
        if exit_code == 0:
            logger.info(f"任务启动成功: {proxy_ip}")
        else:
            logger.warning(f"任务启动失败 (退出码: {exit_code}): {proxy_ip}")
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")

def process_proxy(proxy_ip):
    """处理单个代理IP"""
    try:
        # 验证代理
        if validate_proxy(proxy_ip):
            logger.info(f"代理可用: {proxy_ip}")
            # 执行任务
            execute_task(proxy_ip)
        else:
            logger.info(f"代理不可用: {proxy_ip}")
    except Exception as e:
        logger.error(f"处理代理时出错: {proxy_ip} - {str(e)}")

def main():
    """主函数"""
    try:
        # 获取代理列表
        proxy_list = testIP.getProxyip()
        logger.info(f"获取到 {len(proxy_list)} 个代理IP")
    except Exception as e:
        logger.error(f"获取代理列表失败: {str(e)}")
        return
    
    # 使用线程池控制并发数量
    max_workers = min(20, len(proxy_list))  # 最大20个线程
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        futures = [executor.submit(process_proxy, proxy) for proxy in proxy_list]
        
        # 等待所有任务完成
        for future in futures:
            try:
                future.result(timeout=60)  # 每个任务最多等待60秒
            except Exception as e:
                logger.error(f"任务执行超时或出错: {str(e)}")
    
    logger.info("所有代理处理完成")

if __name__ == '__main__':
    # 设置更安全的线程启动方式
    threading.Thread(target=main, name="MainThread", daemon=True).start()
    
    # 主线程等待所有工作线程完成
    while threading.active_count() > 1:
        time.sleep(1)
    
    logger.info("程序执行完毕")