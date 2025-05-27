import requests
url="https://movie.douban.com/top250"
headers={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"}

resp=requests.get(url,headers=headers)
date=resp.text
print(date)
with open('db.html',"w",encoding="utf-8") as f:
    f.write(date)