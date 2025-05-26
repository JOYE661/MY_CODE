import scrapy

#  爬虫类，继承了Spider基类
class BdSpider(scrapy.Spider):
    name = "bd1"
    #爬虫名称
    allowed_domains = ["www.baidu.com","movie.douban.com"]
    #允许爬取的域名
    start_urls = ["https://www.baidu.com"]
    #起始URL
    #重写start_requests方法
    def start_requests(self):
        yield scrapy.Request(self.start_urls[0],callback=self.parse2)
    #解析函数，回调函数，发送请求之后回来调用的方法
    def parse(self, response):
        print("hello scrapy")
        print(response.url)
        url="https://movie.douban.com/top250"
        yield scrapy.Request(url,callback=self.parse2) #请求get

    
    def parse2(self, response):
        print("hello scrapy2")
        print(response.url)