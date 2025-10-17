# import pytest
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from time import sleep
# from lib.webAPI import APIMgr

# class Test_AddCustomer:
#     """
#     测试用例：添加客户 UI_0102
#     """

#     def setup_method(self):
#         self.wd = webdriver.Chrome()
#         self.wd.implicitly_wait(10)

#     def teardown_method(self):
#         self.wd.quit()

#     def test_add_customer(self):

#         self.setup_method()
#         api = APIMgr()
#         api.mgr_login()
#         api.customer_list()

#         # """步骤1: 登录网站"""
#         # self.wd.get('http://127.0.0.1:8000/mgr/sign.html')
#         # self.wd.find_element(By.ID, 'username').send_keys('byhy')
#         # self.wd.find_element(By.ID, 'password').send_keys('88888888')
#         # self.wd.find_element(By.TAG_NAME, 'button').click()
#         # sleep(1)  # 等待页面跳转

#         # """步骤2: 点击左侧客户菜单"""
#         # sidebar_menu = self.wd.find_element(By.CLASS_NAME, 'sidebar-menu')
#         # menu_spans = sidebar_menu.find_elements(By.TAG_NAME, 'span')
#         # menu_spans[0].click()  # 点击“客户”菜单
#         # sleep(1)

#         # """步骤3: 添加客户"""
#         # self.wd.find_element(By.CLASS_NAME, 'glyphicon-plus').click()

#         # # 修正拼写错误: form-contorl -> form-control
#         # inputs = self.wd.find_elements(By.CSS_SELECTOR, '.add-one-area .form-control')
#         # assert len(inputs) >= 3, "输入框数量不足"

#         # inputs[0].send_keys('南京中医院')         # 客户姓名
#         # inputs[1].send_keys('2551867858')       # 联系电话
#         # inputs[2].send_keys('江苏省-南京市-秦淮区-汉中路-16栋504')  # 地址

#         # # 点击创建按钮
#         # self.wd.find_element(By.CSS_SELECTOR, '.add-one-area .btn-xs').click()
#         # sleep(1)

#         # """步骤4: 检查添加结果"""
#         # items = self.wd.find_elements(By.CLASS_NAME, 'search-result-item')
#         # assert len(items) > 0, "未找到客户列表项"

#         # first_item = items[0]
#         # spans = first_item.find_elements(By.TAG_NAME, 'span')[:6]
#         # actual_texts = [span.text for span in spans]
#         # print("实际获取文本:", actual_texts)  # 替代 INFO

#         # expected_texts = [
#         #     '客户名：',
#         #     '南京中医院',
#         #     '联系电话：',
#         #     '2551867858',
#         #     '地址：',
#         #     '江苏省-南京市-秦淮区-汉中路-16栋504'
#         # ]

#         # assert actual_texts == expected_texts, \
#         #     f"客户信息不一致！期望: {expected_texts}, 实际: {actual_texts}"