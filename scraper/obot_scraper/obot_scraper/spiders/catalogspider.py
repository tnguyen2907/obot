import scrapy
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse, urlencode

from obot_scraper.items import WebsiteItem

CATALOG_ID = '52'

class CatalogspiderSpider(scrapy.Spider):
    name = "catalogspider"
    allowed_domains = ["catalog.oberlin.edu"]
    start_urls = ["https://catalog.oberlin.edu/"]
    visited_urls = set()  
    ignored_extensions = ['.pdf','.img', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.mp3', '.mp4', 'ppt', '.pptx', '.csv']

    custom_settings = {
        'FEEDS': {
            'output/catalog.json': {'format': 'json', 'overwrite': True},
        },
        "LOG_FILE": "logs/catalog.log",
    }


    def parse(self, response):
        # Only yield the website item if the URL does not have the 'print' flag and the 'navoid=5080' flag
        if '&print' not in response.url and 'navoid=5080' not in response.url:
            modified_time = None

            html_content = response.body.decode('utf-8')

            date_happened = None

            website_item = WebsiteItem()

            website_item['url'] = response.url
            website_item['type'] = 'catalog'
            if not response.url.startswith("https://catalog.oberlin.edu"):
                website_item['type'] = 'external'
            website_item['website_last_modified_time'] = modified_time
            website_item['content'] = html_content
            website_item["metadata"] = {"date_happened": date_happened}

            yield website_item

        # Extract all links on the page
        links = response.css('a::attr(href)').getall()
        
        # Filter and normalize links
        for link in links:
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(response.url, link)
            
            # Parse the URL
            parsed_url = urlparse(absolute_url)
            query_params = parse_qs(parsed_url.query)

            # Check for file extensions to ignore
            if any(absolute_url.lower().endswith(ext) for ext in self.ignored_extensions):
                continue

            # Remove the 'print' flag if present and the fragment
            cleaned_query_params = parsed_url.query#.replace('&print', '').replace('print', '')
            cleaned_url = urlunparse(parsed_url._replace(query=cleaned_query_params, fragment=''))

            # Check if 'catoid' is 52
            query_params = parse_qs(cleaned_query_params)
            if 'catoid' in query_params and query_params['catoid'][0] == CATALOG_ID:
                # Filter out already visited URLs and ensure the URL starts with the desired prefix
                if cleaned_url.startswith("https://catalog.oberlin.edu/") and cleaned_url not in self.visited_urls:
                    self.visited_urls.add(cleaned_url) 

                    self.logger.debug('Follow URL: %s', cleaned_url)     # NOTE: The yielded URL can be different from the followed URL since the URL may be redirected
                                                                        # The follow URL may be redirected to a different domain or access denied, so the URL may not be yielded
                    # Follow the link to scrape more data
                    yield scrapy.Request(cleaned_url, callback=self.parse)
