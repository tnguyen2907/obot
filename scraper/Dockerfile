FROM python:3.11.9-slim

WORKDIR /obot_scraper

COPY ./obot_scraper /obot_scraper

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "run_spiders.py", "eventspider", "--logfile", "logs/events.log", "--dryrun"]
