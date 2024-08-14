import scrapy   
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import argparse
import os

from obot_scraper.pipelines import EncodingAndStoringPipeline

def main():
    parser = argparse.ArgumentParser(description="Run specified Scrapy spiders")
    parser.add_argument('spiders', nargs='+', choices=['blogspider', 'bulletinspider', 'catalogspider', 'eventspider', 'newsspider', 'oberlinspider', "debugspider"], help="Names of the spiders to run")
    parser.add_argument('-ll', '--loglevel', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Log level")
    parser.add_argument('-lf', '--logfile', default='logs/spiders.log', help="Log file path")
    parser.add_argument('--dryrun', action='store_true', help="Run spiders without adding items to Firestore (disables EncodingAndStoringPipeline)")

    args = parser.parse_args()

    settings = get_project_settings()
    settings.set("LOG_LEVEL", args.loglevel)
    settings.set("LOG_FILE", args.logfile)

    if args.dryrun:
        settings.set("ITEM_PIPELINES", {
            "obot_scraper.pipelines.CleaningAndChunkingPipeline": 300
        })

    #create output and logs directories if they don't exist
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    process = CrawlerProcess(settings)

    # Run multiple spiders in one process
    for spider in args.spiders:
        process.crawl(spider)

    process.start()

    # Print new URL and encoding stats
    EncodingAndStoringPipeline().print_stats()

if __name__ == "__main__":
    main()
