import scrapy
from obot_scraper.items import WebsiteItem
from datetime import datetime, timezone, timedelta

EVENT_DATE_HAPPENED_TIME_FORMAT = "%A, %B %d, %Y"
NEWS_DATE_HAPPENED_TIME_FORMAT = "%B %d, %Y"
BULLETIN_DATE_HAPPENED_TIME_FORMAT = "%B %d, %Y %I:%M %p"
BLOG_DATE_HAPPENED_TIME_FORMAT = "%B %d, %Y"

EDT_timezone = timezone(timedelta(hours=-4), 'EDT')

class DebugspiderSpider(scrapy.Spider):
    name = "debugspider"
    allowed_domains = ["oberlin.edu"]
    # start_urls = ["https://catalog.oberlin.edu/preview_program.php?catoid=52&poid=9198&print"]
    start_urls = ["https://catalog.oberlin.edu/preview_program.php?catoid=52&poid=9186"]
    # start_urls = ["https://www.oberlin.edu/financial-aid"] 
    # start_urls = ["https://www.oberlin.edu/events/supc-presents-sidney-gish"]

    custom_settings = {
        'FEEDS': {
            'output/debug.json': {'format': 'json', 'overwrite': True},
        }
    }

    def parse(self, response):
        if response.url.startswith("https://catalog.oberlin.edu"):
            item_type = "catalog"
        else:
            item_type = "blog"

        modified_time = response.xpath("//meta[@property='article:modified_time']/@content").get()
        # modified_time = time_to_est(modified_time, WEBSITE_TIME_FORMAT)
        # modified_time = response.headers.get('Last-Modified').decode('utf-8')
        # modified_time = time_to_est(modified_time, CATALOG_TIME_FORMAT)

        # modified_time = None

        html_content = response.body.decode('utf-8')

        date_happened = response.css('.date-display-single::text').get()
        if date_happened is None or len(date_happened) < 15:       # If the date is not in the format "Day, Month DD, YYYY"
            date_happened = response.css('.date-display-start::text').get()

        # print("date_happened: ",date_happened)

        # print(datetime.strptime(date_happened, EVENT_DATE_HAPPENED_TIME_FORMAT).replace(tzinfo=EDT_timezone))
        
        website_item = WebsiteItem()

        website_item['url'] = response.url
        website_item['type'] = item_type
        website_item['website_last_modified_time'] = modified_time
        website_item['content'] = html_content
        website_item["metadata"] = {"date_happened": date_happened}

        yield website_item
        
