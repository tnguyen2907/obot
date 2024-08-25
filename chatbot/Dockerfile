FROM python:3.11.9-slim

ARG GCP_PROJECT_ID
ARG GOOGLE_API_KEY
ARG LANGCHAIN_API_KEY

ENV GCP_PROJECT_ID=$GCP_PROJECT_ID
ENV GOOGLE_API_KEY=$GOOGLE_API_KEY
ENV LANGCHAIN_API_KEY=$LANGCHAIN_API_KEY

WORKDIR /app

COPY ./app /app/

# RUN pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health 

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--global.developmentMode=false", "--client.toolbarMode=viewer"]
