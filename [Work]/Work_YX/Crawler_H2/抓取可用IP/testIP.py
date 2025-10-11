import pytesseract
from PIL import Image, UnidentifiedImageError
import requests
from lxml import etree
import os
import time
import logging
from requests.exceptions import RequestException

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def getImageWithocr(image_url, max_retries=3):
    """
    通过图片URL下载图片，使用OCR识别图片内容
    
    参数:
        image_url (str): 图片URL
        max_retries (int): 最大重试次数
        
    返回:
        str: 识别的文本内容，失败返回空字符串
    """
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }
    
    # 获取脚本所在目录并创建port_image子目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    port_image_dir = os.path.join(script_dir, "port_image")
    os.makedirs(port_image_dir, exist_ok=True)
    
    # 构造完整的文件路径
    file_path = os.path.join(port_image_dir, "background_pic.png")
    
    text = ""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 下载图片
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()  # 检查HTTP错误
            
            # 保存图片
            with open(file_path, "wb") as f:
                f.write(response.content)
                
            # OCR识别
            try:
                image = Image.open(file_path)
                # 对图片进行预处理提高识别率
                image = image.convert('L')  # 转为灰度图
                text = pytesseract.image_to_string(image)
                
                # 清理识别结果
                text = (text.replace(',', '')
                         .replace('B', '8')
                         .replace('O', '0')  # 避免O和0混淆
                         .replace('\n', '')
                         .replace('\x0c', '')
                         .replace(' ', '')
                         .strip())
                
                logging.info(f"成功识别端口: {text}")
                return text
                
            except (UnidentifiedImageError, IOError) as img_err:
                logging.error(f"图片处理失败: {img_err}")
                return ""
                
        except RequestException as req_err:
            logging.warning(f"图片下载失败 (尝试 {retry_count+1}/{max_retries}): {req_err}")
            retry_count += 1
            time.sleep(2 ** retry_count)  # 指数退避等待
            
        except Exception as e:
            logging.error(f"未知错误: {e}")
            break
    
    return ""  # 所有尝试失败后返回空字符串

def getProxyip(urls='https://proxy.mimvp.com/freeopen?proxy=in_hp&sort=&page=1', max_retries=3):
    """
    获取代理IP列表
    
    参数:
        urls (str): 目标URL
        max_retries (int): 最大重试次数
        
    返回:
        list: 代理IP列表
    """
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }
    
    list_ip = []  # 初始化列表
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            responds = requests.get(urls, headers=headers, timeout=15)
            responds.raise_for_status()  # 检查HTTP错误
            
            html_content = etree.HTML(responds.content.decode('utf-8'))
            allips = html_content.xpath("//*[@class='mimvp-tbl free-proxylist-tbl']/tbody/tr")
            
            if not allips:
                logging.warning("页面未找到IP表格，可能是网站结构变化")
                return []
            
            for ip_name_item in allips:
                try:
                    # 获取IP地址
                    ip_name = ip_name_item.xpath('./td[2]/text()')[0].strip()
                    
                    # 获取端口号图片URL
                    img_src = ip_name_item.xpath('./td[3]/img/@src')
                    if not img_src:
                        logging.warning("未找到端口图片URL，跳过此IP")
                        continue
                    
                    image_url = 'https://proxy.mimvp.com' + img_src[0]
                    
                    # 识别端口号
                    port_name = getImageWithocr(image_url)
                    if not port_name:
                        logging.warning(f"端口识别失败，跳过IP: {ip_name}")
                        continue
                    
                    # 拼接完整代理地址
                    proxy = f"{ip_name}:{port_name}"
                    list_ip.append(proxy)
                    logging.info(f"添加代理: {proxy}")
                    
                except IndexError:
                    logging.warning("解析IP条目时发生索引错误，跳过此条目")
                except Exception as e:
                    logging.error(f"处理IP条目时出错: {e}")
            
            return list_ip
            
        except RequestException as req_err:
            logging.warning(f"请求失败 (尝试 {retry_count+1}/{max_retries}): {req_err}")
            retry_count += 1
            time.sleep(5)  # 等待后重试
        except Exception as e:
            logging.error(f"未知错误: {e}")
            break
    
    return []  # 所有尝试失败后返回空列表

if __name__ == '__main__':
    try:
        proxies = getProxyip()
        if proxies:
            print("\n获取到的代理列表:")
            for i, proxy in enumerate(proxies, 1):
                print(f"{i}. {proxy}")
        else:
            print("未获取到有效代理")
    except KeyboardInterrupt:
        print("\n程序被用户中断")