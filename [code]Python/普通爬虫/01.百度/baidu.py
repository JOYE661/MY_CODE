import requests

url="https://www.baidu.com/"
resp=requests.get(url)
print(resp.text)
date=resp.text
with open("baidu.html","w",encoding="utf-8") as f:
    f.write(date);
