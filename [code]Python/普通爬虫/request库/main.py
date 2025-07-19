import requests
url="https://www.baidu.com/" 
resp=requests.get(url)
if resp.status_code==200:
    text=resp.text
    print(resp.text)