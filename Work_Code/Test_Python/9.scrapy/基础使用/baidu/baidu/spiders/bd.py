import scrapy

#  爬虫类，继承了Spider基类
class BdSpider(scrapy.Spider):
    name = "bd"
    #爬虫名称
    allowed_domains = ["www.baidu.com"]
    #允许爬取的域名
    start_urls = ["https://www.baidu.com"]
    #起始URL

    #解析函数，回调函数，发送请求之后回来调用的方法
    def parse(self, response):
        print("hello scrapy")
        print(response.url)
        pass
