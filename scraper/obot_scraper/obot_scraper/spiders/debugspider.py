import scrapy
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs

from obot_scraper.items import WebsiteItem

class DebugspiderSpider(scrapy.Spider):
    name = "debugspider"
    allowed_domains = ["oberlin.edu", "drive.google.com", "drive.usercontent.google.com"]
    start_urls = ["https://www.oberlin.edu"]
    visited_urls = set()  
    ignored_extensions =['doc', 'xls', 'ppt', '.img', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.mp3', '.mp4',  '.csv', '.txt'] # Accpeted: ['.pdf', '.docx', '.xlsx', '.pptx']
    ignored_words = ['news', 'events', 'news-and-events', 'blogs', 'bulletins']
    pagination_flags = ['page', 'tag', "program", "audience", "department"]

    custom_settings = {
        'FEEDS': {
            'output/debug.json': {'format': 'json', 'overwrite': True},
        },
        "LOG_FILE": "logs/debug.log",
    }

    def parse(self, response):
        if response.url.endswith(('.pdf', '.docx', '.pptx', '.xlsx')) or response.url.startswith(("https://drive.google.com", "https://drive.usercontent.google.com")):
            if response.url.startswith("https://drive.google.com"):
                yield scrapy.Request("https://drive.google.com/uc?export=download&id=" + response.url.split('/')[5], callback=self.parse, meta={'url': response.url})
            else:
                original_url = response.meta.get('url', response.url)
                yield WebsiteItem(
                    url=original_url,
                    type="official",
                    website_last_modified_time=None,
                    content=response.body,
                    metadata={"date_happened": None}
                )
        else:
        # Yield the website item only if the URL does not have pagination flags
            pagination_in_url = False
            for flag in self.pagination_flags:
                if flag in parse_qs(urlparse(response.url).query):
                    pagination_in_url = True
            if not pagination_in_url:

                website_item = WebsiteItem()

                website_item['url'] = response.url

                website_item['type'] = 'official'
                if not response.url.startswith("https://www.oberlin.edu"):
                    website_item['type'] = 'external'

                # Extract the last modified time of the website
                website_item['website_last_modified_time'] = response.xpath("//meta[@property='article:modified_time']/@content").get()

                website_item['content'] = response.body.decode('utf-8')

                website_item["metadata"] = {"date_happened": None}

                yield website_item

            # Extract all links on the page
            links = response.css('a::attr(href)').getall()
            
            # Filter and normalize links
            for link in links:
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(response.url, link)
                
                # Parse the URL and remove the fragment
                parsed_url = urlparse(absolute_url)
                cleaned_url = urlunparse(parsed_url._replace(fragment=''))
                
                # Check for file extensions to ignore
                if any(cleaned_url.lower().endswith(ext) for ext in self.ignored_extensions):
                    continue

                # Check for ignored words in the URL path
                path_parts = parsed_url.path.strip('/').split('/')
                if any(part in self.ignored_words for part in path_parts):
                    continue
                
                # Filter out already visited URLs and ensure the URL starts with the desired prefix
                if cleaned_url.startswith("https://www.oberlin.edu") and cleaned_url not in self.visited_urls:
                    self.visited_urls.add(cleaned_url)  
                    
                    self.logger.debug('Follow URL: %s', cleaned_url)     # NOTE: The yielded URL can be different from the followed URL since the URL may be redirected
                                                                        # The follow URL may be redirected to a different domain or access denied, so the URL may not be yielded
                    # Follow the link to scrape more data
                    yield scrapy.Request(cleaned_url, callback=self.parse)



# ==================================================================


# import scrapy
# from obot_scraper.items import WebsiteItem
# from datetime import datetime, timezone, timedelta

# EDT_timezone = timezone(timedelta(hours=-4), 'EDT')

# class DebugspiderSpider(scrapy.Spider):
#     name = "debugspider"
#     allowed_domains = ["oberlin.edu", "drive.google.com", "drive.usercontent.google.com"]
#     # start_urls = ["https://catalog.oberlin.edu/preview_program.php?catoid=52&poid=9198&print"]
#     # start_urls = ["https://catalog.oberlin.edu/preview_program.php?catoid=52&poid=9186"]
#     # start_urls = ["https://www.oberlin.edu/financial-aid"] 
#     start_urls = ["https://www.oberlin.edu/academic-calendar"]

#     custom_settings = {
#         'FEEDS': {
#             'output/debug.json': {'format': 'json', 'overwrite': True},
#         },
#         'LOG_FILE': 'logs/debug.log',
#     }

#     def parse(self, response):
#         # print("URL: ", response.url)    
#         if response.url.endswith(('.pdf', '.docx', '.pptx', '.xlsx')) or response.url.startswith(("https://drive.google.com", "https://drive.usercontent.google.com")):
#             if response.url.startswith("https://drive.google.com"):
#                 yield scrapy.Request("https://drive.google.com/uc?export=download&id=" + response.url.split('/')[5], callback=self.parse, meta={'url': response.url})
#             else:
#                 original_url = response.meta.get('url', response.url)
#                 yield WebsiteItem(
#                     url=original_url,
#                     type="oberlin",
#                     website_last_modified_time=None,
#                     content=response.body,
#                     metadata={"date_happened": None}
#                 )
#         else:
#             if response.url.startswith("https://catalog.oberlin.edu"):
#                 item_type = "catalog"
#             else:
#                 item_type = "blog"

#             # modified_time = response.xpath("//meta[@property='article:modified_time']/@content").get()

#             modified_time = None

#             # html_content = response.body.decode('utf-8')
#             html_content = None

#             # date_happened = response.css('.date-display-single::text').get()
#             # if date_happened is None or len(date_happened) < 15:       # If the date is not in the format "Day, Month DD, YYYY"
#             #     date_happened = response.css('.date-display-start::text').get()
#             date_happened = None
#             # print("date_happened: ",date_happened)
            
#             website_item = WebsiteItem()

#             website_item['url'] = response.url
#             website_item['type'] = item_type
#             website_item['website_last_modified_time'] = modified_time
#             website_item['content'] = html_content
#             website_item["metadata"] = {"date_happened": date_happened}

#             yield website_item
        

# ==================================================================


