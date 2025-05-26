import scrapy

from douban.items import DoubanItem




class DbSpider(scrapy.Spider):
    name = "mdb"
    allowed_domains = ["movie.douban.com"]
    start_urls = ["https://movie.douban.com/top250?start=0&filter="]
    main_url = "https://movie.douban.com/top250"
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
            print(num, name, score, desc)

            item["num"]=num
            item["name"]=name 
            item["score"]=score
            item["desc"]=desc

            yield item

        next_page = response.xpath('//span[@class="next"]/a/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        #//span[@class="next"]/a/@href'
        #//*[@id="content"]/div/div[1]/div[2]/a/@href
        # next_url=response.xpath('//*[@id="content"]/div/div[1]/div[2]/a/@href').get()
        # if next_url is not None:
        #     next_url=self.main_url+response.xpath('//*[@id="content"]/div/div[1]/div[2]/a/@href').get()
        #     print(next_url)
        #     yield scrapy.Request(next_url, callback=self.parse)
        # else:
        #     print("没有下一页")


        # next_url=self.main_url+response.xpath('//*[@id="content"]/div/div[1]/div[2]/a/@href').get()

        #//*[@id="content"]/div/div[1]/div/div/table[1]/tbody/tr

        #//*[@id="content"]/div/div[1]/div[2]/a[1]
    

        #https://movie.douban.com/top250?start=0&filter=
        #https://movie.douban.com/top250?start=25&filter=
        #//*[@id="content"]/div/div[1]/div[2]/a[2]