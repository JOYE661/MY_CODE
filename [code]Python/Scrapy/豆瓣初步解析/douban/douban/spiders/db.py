import scrapy

from douban.items import DoubanItem




class DbSpider(scrapy.Spider):
    name = "db"
    allowed_domains = ["movie.douban.com"]
    start_urls = ["https://movie.douban.com/top250"]

    def parse(self, response):
        print(response.url)

        

        li_list=response.xpath('//*[@id="content"]/div/div[1]/ol/li')
        #//*[@id="content"]/div/div[1]/ol/li[1]
        for li in li_list:
            item=DoubanItem()
            num=li.xpath('./div/div[1]/em/text()').get()
            #//*[@id="content"]/div/div[1]/ol/li[1]/div/div[1]/em
            name=li.xpath('./div/div[2]/div[1]/a/span[1]/text()').get()
            #//*[@id="content"]/div/div[1]/ol/li[1]/div/div[2]/div[1]/a/span[1]
            score=li.xpath('./div/div[2]/div[2]/div/span[2]/text()').get()
            #//*[@id="content"]/div/div[1]/ol/li[1]/div/div[2]/div[2]/div/span[2]
            desc=li.xpath('./div/div[2]/div[2]/p[2]/span/text()').get()
            #//*[@id="content"]/div/div[1]/ol/li[1]/div/div[2]/div[2]/p[2]/span
            # print(num, name, score, desc)

            item["num"]=num
            item["name"]=name 
            item["score"]=score
            item["desc"]=desc

            yield item

        #//*[@id="content"]/div/div[1]/div/div/table[1]/tbody/tr

