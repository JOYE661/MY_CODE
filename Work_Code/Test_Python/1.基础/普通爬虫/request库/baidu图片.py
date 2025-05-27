import requests
url="https://www.baidu.com/img/flexible/logo/pc/result.png" 
resp=requests.get(url)
if resp.status_code==200:
    download=resp.content
    with open("baidu.png","wb") as f:
        f.write(download)
    