import scrapy   
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import argparse
import os
from google.cloud import storage
import datetime
import logging

from obot_scraper.pipelines import EncodingAndStoringPipeline

os.environ["GOOGLE_CLOUD_PROJECT"] = os.environ.get("GCP_PROJECT_ID")

def upload_to_gcs(local_path, bucket_name, gcs_path):
    client = storage.Client(project=os.environ.get("GCP_PROJECT_ID"))
    bucket = client.bucket(bucket_name)

    for root, dirs, files in os.walk(local_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_file_path, local_path)

            if local_path == "logs":
                filename, file_extension = os.path.splitext(file)
                # Create a new filename with the timestamp
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                new_filename = f"{filename}-{timestamp}{file_extension}"
                # Update the relative path with the new filename
                relative_path = os.path.join(os.path.dirname(relative_path), new_filename)
                
            blob = bucket.blob(os.path.join(gcs_path, relative_path))
            blob.upload_from_filename(local_file_path)
            print(f"Uploaded {local_file_path} to gs://{bucket_name}/{gcs_path}/{relative_path}")

def main():
    parser = argparse.ArgumentParser(description="Run specified Scrapy spiders")
    parser.add_argument('spiders', nargs='+', choices=['blogspider', 'bulletinspider', 'catalogspider', 'eventspider', 'newsspider', 'oberlinspider', "debugspider"], help="Names of the spiders to run")
    parser.add_argument('-ll', '--loglevel', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Log level")
    parser.add_argument('-lf', '--logfile', default='logs/spiders.log', help="Log file path")
    parser.add_argument('--dry-run', action='store_true', help="Run spiders without adding items to Firestore (disables EncodingAndStoringPipeline)")

    args = parser.parse_args()

    settings = get_project_settings()
    settings.set("LOG_LEVEL", args.loglevel)
    if len(args.spiders) > 1:
        settings.set("LOG_FILE", args.logfile)

    if not args.dry_run:
        settings.set("ITEM_PIPELINES", {
            "obot_scraper.pipelines.CleaningAndChunkingPipeline": 300,
            "obot_scraper.pipelines.EncodingAndStoringPipeline": 400,
        })

    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    process = CrawlerProcess(settings)

    for spider in args.spiders:
        process.crawl(spider)

    print(f"Running {args.spiders} spiders")

    process.start()

    print("All spiders have finished")

    if not args.dry_run:
        # Print new URL and encoding stats
        EncodingAndStoringPipeline().print_stats()

        # Upload output and log files to GCS
        upload_to_gcs("output", "obot-scraper-output", "")

        cur_timestamp = datetime.datetime.now().strftime("%Y%m%d")
        upload_to_gcs("logs", "obot-scraper-logs", f"logs-{cur_timestamp}")
    else:
        logging.info("This is a dry run. No items were added to Firestore.")


if __name__ == "__main__":
    main()
