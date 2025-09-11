from selenium import webdriver
from selenium.webdriver.common.by import By

wd = webdriver.Chrome()
wd.implicitly_wait(10)

wd.get('https://www.byhy.net/cdn2/files/selenium/sample3.html')

# 点击打开新窗口的链接
link = wd.find_element(By.TAG_NAME, "a")
link.click()

# wd.title属性是当前窗口的标题栏 文本
print(wd.title)