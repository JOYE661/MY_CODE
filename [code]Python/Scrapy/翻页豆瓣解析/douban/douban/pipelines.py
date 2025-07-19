# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class DoubanPipeline:

    def open_items(self, spider):
        pass 
    def process_item(self, item, spider):
        # print("process_item")
        print(f"item:{item}")
        return item
    def close_items(self, spider):
        pass

        
