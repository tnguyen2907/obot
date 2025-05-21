FROM python:3.11.9-slim

ARG GCP_PROJECT_ID
ARG GOOGLE_API_KEY
ARG LANGCHAIN_API_KEY
ARG PORT=8501

ENV GCP_PROJECT_ID=$GCP_PROJECT_ID
ENV GOOGLE_API_KEY=$GOOGLE_API_KEY
ENV LANGCHAIN_API_KEY=$LANGCHAIN_API_KEY
ENV PORT=$PORT

WORKDIR /app

COPY ./app /app/

# RUN pip install -U pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}

ENTRYPOINT streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0
