from selenium import webdriver
import time
from selenium.webdriver.common.by import By
def loginAndCheck(username, password):
        
        # 使用Service对象来指定ChromeDriver（Selenium 4+的要求）
        driver = webdriver.Chrome()

        driver.implicitly_wait(10)

        driver.get('http://127.0.0.1:8000/mgr/sign.html')

        # 使用新的find_element方法替代已弃用的find_element_by_id方法
        if username is not None:
            driver.find_element(By.ID, 'username').send_keys(username)
        if password is not None:
            driver.find_element(By.ID, 'password').send_keys(password)
        
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

        time.sleep(2)

        alterText = driver.switch_to.alert.text

        print(alterText)

        driver.quit()

        return alterText  
      
        