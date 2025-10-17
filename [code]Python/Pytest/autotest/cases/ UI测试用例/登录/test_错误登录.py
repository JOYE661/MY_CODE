import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from lib.webUI import loginAndCheck


class Test_错误登录:
    @pytest.mark.parametrize('username, password, expectedalert', [
        (None, '88888888', '请输入用户名'),
        ('byhy', None, '请输入密码'),
        ('byh', '88888888', '登录失败 : 用户名或者密码错误'),
        ('byhy', '8888888', '登录失败 : 用户名或者密码错误'),
        ('byhy', '888888888', '登录失败 : 用户名或者密码错误'),
    ]
                             )
    def test_UI_0001_0005(self, username, password, expectedalert):
        alertText = loginAndCheck(username, password)
        assert alertText == expectedalert


    # def test_UI_0001(self):
    #     print('\n用例UI_0001')
    #     alertText = loginAndCheck(None, '88888888')
    #     assert alertText == "请输入用户名"

    #     # # 使用Service对象来指定ChromeDriver（Selenium 4+的要求）
    #     # driver = webdriver.Chrome()

    #     # driver.implicitly_wait(10)

    #     # driver.get('http://127.0.0.1:8000/mgr/sign.html')

    #     # # 使用新的find_element方法替代已弃用的find_element_by_id方法
    #     # # driver.find_element('username').send_keys('')

    #     # driver.find_element(By.ID, 'password').send_keys('88888888')

    #     # driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    #     # time.sleep(2)

    #     # alterText = driver.switch_to.alert.text

    #     # print(alterText)

    #     # assert alterText == "请输入用户名"
        
    #     # driver.quit()

    # def test_UI_0002(self):
    #     print('\n用例UI_0002')
    #     alertText = loginAndCheck('byhy', None)
    #     assert alertText == "请输入密码"
    #     # # 使用Service对象来指定ChromeDriver（Selenium 4+的要求）
    #     # driver = webdriver.Chrome()

    #     # driver.implicitly_wait(10)

    #     # driver.get('http://127.0.0.1:8000/mgr/sign.html')

    #     # # 使用新的find_element方法替代已弃用的find_element_by_id方法
    #     # driver.find_element(By.ID, 'username').send_keys('byhy')

    #     # # driver.find_element(By.ID, 'password').send_keys('88888888')

    #     # driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    #     # time.sleep(2)

    #     # alterText = driver.switch_to.alert.text

    #     # print(alterText)

    #     # assert alterText == "请输入密码"
        
    #     # driver.quit()

    # def test_UI_0003(self):
    #     print('\n用例UI_0003')
    #     alertText = loginAndCheck('byh', '88888888')
    #     assert alertText == "登录失败 : 用户名或者密码错误"

    #     # # 使用Service对象来指定ChromeDriver（Selenium 4+的要求）
    #     # driver = webdriver.Chrome()

    #     # driver.implicitly_wait(10)

    #     # driver.get('http://127.0.0.1:8000/mgr/sign.html')

    #     # # 使用新的find_element方法替代已弃用的find_element_by_id方法
    #     # driver.find_element(By.ID, 'username').send_keys('byh')

    #     # driver.find_element(By.ID, 'password').send_keys('88888888')

    #     # driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    #     # time.sleep(2)

    #     # alterText = driver.switch_to.alert.text

    #     # print(alterText)

    #     # assert alterText == "登录失败 : 用户名或者密码错误"
        
    #     # driver.quit()