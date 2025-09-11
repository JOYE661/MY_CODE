from selenium import webdriver

wd = webdriver.Edge() # 指定 Edge 浏览器，会自动下载驱动

wd.get('https://www.byhy.net/cdn2/files/selenium/stock1.html')

element=wd.find_element('id','kw') #使用了 WebDriver 对象 的方法 find_element ，

element.send_keys('通讯\n')

# import time

# time.sleep(2)
wd.implicitly_wait(10)
element=wd.find_element('id','1')
print(element.get_attribute('class'))
print(element.text)

input("回车键")

#wd.input('中兴')

#wd.quit()