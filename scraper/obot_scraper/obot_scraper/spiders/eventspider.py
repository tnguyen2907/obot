import scrapy
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime, timedelta
from obot_scraper.items import WebsiteItem

class EventspiderSpider(scrapy.Spider):
    name = "eventspider"
    allowed_domains = ["oberlin.edu"]
    start_urls = ["https://www.oberlin.edu/events/series"]
    visited_urls = set()
    ignored_extensions = ['.pdf', '.img', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.mp3', '.mp4', 'ppt', '.pptx', '.csv']
    ignored_words = ['news', 'news-and-events', 'blogs', 'bulletins']

    custom_settings = {
        'FEEDS': {
            'output/events.json': {'format': 'json', 'overwrite': True},
        },
        "LOG_FILE": "logs/events.log",
    }

    def __init__(self):
        # Generate start URLs for one year from today
        today = datetime.now()
        for day_offset in range(366):
            date = today + timedelta(days=day_offset)
            year = date.year
            month = date.month
            day = date.day
            url = f"https://www.oberlin.edu/events?date_op=%3D&date%5Bvalue%5D%5Byear%5D={year}&date%5Bvalue%5D%5Bmonth%5D={month}&date%5Bvalue%5D%5Bday%5D={day}"
            self.start_urls.append(url)

    def parse(self, response):
        # Extract the date from the URL
        date_happened = None
        if not response.url.startswith("https://www.oberlin.edu/series"):
            parsed_url = urlparse(response.url)
            query_params = parse_qs(parsed_url.query)
            year = query_params.get('date[value][year]', [None])[0]
            month = query_params.get('date[value][month]', [None])[0]
            day = query_params.get('date[value][day]', [None])[0]
            date_happened = f"{year}-{month}-{day}" if year and month and day else None

        # Extract all event links on the page
        event_links = response.css('h2.listing-item__content__title a::attr(href)').getall()
        if not event_links:
            # self.logger.debug('No event links found on %s', response.url)
            return

        # Filter and normalize links
        for link in event_links:
            # Convert relative URLs to absolute URLs
            absolute_url = urljoin(response.url, link)
            
            # Check for file extensions to ignore
            if any(absolute_url.lower().endswith(ext) for ext in self.ignored_extensions):
                continue

            # Check for ignored words in the URL path
            path_parts = absolute_url.strip('/').split('/')
            if any(part in self.ignored_words for part in path_parts):
                continue
            
            # Filter out already visited URLs and ensure the URL starts with the desired prefix
            if (absolute_url.startswith("https://www.oberlin.edu/events") or absolute_url.startswith("https://www.oberlin.edu/series")) and absolute_url not in self.visited_urls :
                self.visited_urls.add(absolute_url)
                self.logger.debug('Follow URL: %s', absolute_url)

                # Follow the link to scrape more data
                yield scrapy.Request(absolute_url, callback=self.parse_event, cb_kwargs={'date_happened': date_happened})

    def parse_event(self, response, date_happened):
        # Extract the last modified time of the website
        modified_time = response.xpath("//meta[@property='article:modified_time']/@content").get()

        html_content = response.body.decode('utf-8')

        website_item = WebsiteItem()

        website_item['url'] = response.url
        website_item['type'] = 'event'
        if not response.url.startswith("https://www.oberlin.edu"):
            website_item['type'] = 'external'
        website_item['website_last_modified_time'] = modified_time
        website_item['content'] = html_content
        website_item["metadata"] = {"date_happened": date_happened}

        yield website_item

