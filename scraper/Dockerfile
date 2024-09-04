FROM python:3.11.9-slim

ARG GCP_PROJECT_ID

ENV GCP_PROJECT_ID=$GCP_PROJECT_ID

WORKDIR /obot_scraper

COPY ./obot_scraper /obot_scraper

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "run_spiders.py", "eventspider", "--dry-run"]