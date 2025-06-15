import scrapy
from .demo1 import run_1688
import concurrent.futures

class Ksher1688Spider(scrapy.Spider):
    name = "1688spider"
    allowed_domains = ["1688.com"]
    start_urls = ["https://air.1688.com/app/1688-global/main-site-channel/inner-rank.html"]

    def parse(self, response):
        # 用线程池运行同步的 run_1688
        def get_data():
            run_exec = run_1688(
                type1_class=".type_class",
                type_name="马来西亚",
                type_categories="童装",
                start=0,
                count=30,
                interval=10*1000,
                headless=True
            )
            next(run_exec)
            return next(run_exec)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(get_data)
            ret_data = future.result()
            for item in ret_data:
                yield item