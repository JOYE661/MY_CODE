import scrapy


class DbSpider(scrapy.Spider):
    name = "db"
    allowed_domains = ["movie.douban.com"]
    start_urls = ["https://movie.douban.com/chart"]

    def parse(self, response):
        print(response.url)
        li_list=response.xpath('*[@id="content"]/div/div[1]/div/div/table[1]/tbody/tr')
        #//*[@id="content"]/div/div[1]/div/div/table[1]
        for li in li_list:
            num=li.xpath('./td[2]/div/a/text()').get()
         
            #//*[@id="content"]/div/div[1]/div/div/table[1]/tbody/tr/td[2]/div/a/text()
            print(num)

        #//*[@id="content"]/div/div[1]/div/div/table[1]/tbody/tr

