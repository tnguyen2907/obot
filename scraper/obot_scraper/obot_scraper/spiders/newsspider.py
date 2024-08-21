import scrapy
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs

from obot_scraper.items import WebsiteItem

class NewsspiderSpider(scrapy.Spider):
    name = "newsspider"
    allowed_domains = ["oberlin.edu"]
    start_urls = ["https://www.oberlin.edu/news-and-events"]
    visited_urls = set()  
    ignored_extensions = ['.pdf','.img', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.mp3', '.mp4', 'ppt', '.pptx', '.csv']
    ignored_words = ['events', 'blogs', 'bulletins']
    pagination_flags = ['page', 'tag', "program"]

    custom_settings = {
        'FEEDS': {
            'output/news.json': {'format': 'json', 'overwrite': True},
        },
        "LOG_FILE": "logs/news.log",
    }

    def parse(self, response):
        # Yield the website item only if the URL does not have pagination flags
        pagination_in_url = False
        # Include pagination flags for faculty and staff notes
        if not response.url.startswith("https://www.oberlin.edu/news-and-events/faculty-and-staff-notes"):
            for flag in self.pagination_flags:
                if flag in parse_qs(urlparse(response.url).query):
                    pagination_in_url = True
        if not pagination_in_url:
            # Extract the last modified time of the website
            modified_time = response.xpath("//meta[@property='article:modified_time']/@content").get()

            html_content = response.body.decode('utf-8')

            date_happened = response.css('.date-display-single::text').get()

            website_item = WebsiteItem()

            website_item['url'] = response.url
            website_item['type'] = 'news'
            if not response.url.startswith("https://www.oberlin.edu"):
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
            if (cleaned_url.startswith("https://www.oberlin.edu/news-and-events") or cleaned_url.startswith("https://www.oberlin.edu/news")) and cleaned_url not in self.visited_urls:
                self.visited_urls.add(cleaned_url)  
                
                self.logger.debug('Follow URL: %s', cleaned_url)     # NOTE: The yielded URL can be different from the followed URL since the URL may be redirected
                                                                    # The follow URL may be redirected to a different domain or access denied, so the URL may not be yielded
                # Follow the link to scrape more data
                yield scrapy.Request(cleaned_url, callback=self.parse)

