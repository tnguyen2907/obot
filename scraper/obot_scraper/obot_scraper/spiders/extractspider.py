import scrapy
from obot_scraper.items import WebsiteItem

class ExtractspiderSpider(scrapy.Spider):
    name = "extractspider"
    allowed_domains = ["oberlin.edu"]
    # start_urls = ["https://catalog.oberlin.edu/preview_program.php?catoid=52&poid=9198&print"]
    # start_urls = ["https://catalog.oberlin.edu/preview_course_nopop.php?catoid=52&coid=194265&print"]
    # start_urls = ["https://www.oberlin.edu/financial-aid"] 
    start_urls = ["https://www.oberlin.edu/conservatory/faculty-and-staff"]

    def parse(self, response):
        if response.url.startswith("https://catalog.oberlin.edu"):
            item_type = "catalog"
        else:
            item_type = "official"

        modified_time = response.xpath("//meta[@property='article:modified_time']/@content").get()
        # modified_time = time_to_est(modified_time, WEBSITE_TIME_FORMAT)
        # modified_time = response.headers.get('Last-Modified').decode('utf-8')
        # modified_time = time_to_est(modified_time, CATALOG_TIME_FORMAT)

        # modified_time = None

        html_content = response.body.decode('utf-8')
        
        website_item = WebsiteItem()

        website_item['url'] = response.url
        website_item['type'] = item_type
        website_item['website_last_modified_time'] = modified_time
        website_item['content'] = html_content

        yield website_item
        
