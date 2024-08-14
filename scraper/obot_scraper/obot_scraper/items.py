# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class WebsiteItem(scrapy.Item):
    url = scrapy.Field()
    type = scrapy.Field()
    website_last_modified_time = scrapy.Field()
    scraped_time = scrapy.Field()
    hash_value = scrapy.Field()
    content = scrapy.Field()    #HTML then list of text chunks
    metadata = scrapy.Field()
