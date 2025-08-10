import random
import pandas as pd
import time
from playwright.sync_api import sync_playwright, TimeoutError # 修正导入

def scrape_douyin_comments(video_url):
    comments = []
    with sync_playwright() as p:
        # 启动浏览器（添加反爬参数）
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        
        # 创建上下文（模拟移动设备）
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            viewport={"width": 375, "height": 812}
        )
        page = context.new_page()
        
        try:
            # 导航到目标视频
            page.goto(video_url, timeout=60000)
            print("页面加载成功，等待元素...")
            
            # 处理登录（优化等待逻辑）
            try:
                page.wait_for_selector('div.login-btn', state="visible", timeout=15000)
                page.click('div.login-btn')
                print("请扫码登录抖音账号...")
                page.wait_for_selector('div.qrcode-container', state="visible", timeout=30000)
                input("扫码完成后按回车继续 >>> ")
            except TimeoutError:
                print("已检测到登录状态，继续执行")
            
            # 关闭可能的弹窗（关键优化）
            try:
                close_btn = page.locator('img[src*="close"]').first
                if close_btn.is_visible():
                    close_btn.click(timeout=5000)
                    print("已关闭弹窗")
                    time.sleep(1)
            except:
                pass
            
            # 滚动到评论区并加载（动态调整）
            print("开始加载评论...")
            comment_section = page.locator('div.comment-container')
            for _ in range(8):  # 增加滚动次数
                comment_section.scroll_into_view_if_needed()
                page.mouse.wheel(0, random.randint(800, 1200))
                page.wait_for_timeout(random.randint(1500, 3000))  # 随机等待
                
                # 检测"加载更多"按钮
                more_btn = page.locator('text=展开更多回复').first
                if more_btn.is_visible():
                    more_btn.click()
                    print("点击展开更多回复")
                    page.wait_for_timeout(2000)
            
            # 提取评论数据（改进选择器）
            comment_items = page.query_selector_all('div[data-e2e="comment-item"]')
            print(f"共找到{len(comment_items)}条评论")
            
            for item in comment_items:
                try:
                    author = item.query_selector('span.author-name').inner_text().strip()
                    content = item.query_selector('p.comment-content').inner_text().strip()
                    
                    # 获取点赞数和时间（新增字段）
                    like_count = item.query_selector('span.like-count').inner_text().strip() or "0"
                    timestamp = item.query_selector('span.time-tag').inner_text().strip() or ""
                    
                    comments.append({
                        "author": author,
                        "content": content,
                        "likes": like_count,
                        "time": timestamp
                    })
                except Exception as e:
                    print(f"提取评论时出错: {str(e)}")
        
        finally:
            # 确保浏览器关闭
            browser.close()
    
    # 数据清洗与导出
    df = pd.DataFrame(comments)
    
    # 去重并过滤空评论
    df = df.drop_duplicates(subset=["content"])
    df = df[df["content"].str.len() > 0]
    
    # 导出Excel
    df.to_excel("douyin_comments.xlsx", 
                index=False, 
                columns=["author", "content", "likes", "time"])
    print(f"成功导出{len(df)}条评论到douyin_comments.xlsx")

if __name__ == "__main__":
    target_url = "https://www.douyin.com/search/银耳鲜炖?aid=9cd7a607-d3e7-4123-8258-d7a549174d6b&modal_id=7211811100269038888&type=general"
    scrape_douyin_comments(target_url)