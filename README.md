# Obot

**Obot** is a conversational AI chatbot designed to answer questions about Oberlin College. Leveraging the Retrieval-Augmented Generation (RAG) model, the chatbot uses data scraped from the college's website to provide provides accurate and context-specific responses to user queries. The application is hosted on Google Cloud Platform (GCP) and is publicly accessible at http://34.73.204.69:30000

![Chatbot App Demo](https://github.com/tnguyen2907/obot/tree/master/documentation/chatbot-app-demo.gif)

This repository contains four major components:
1. Chatbot application using **Langchain** and **Streamlit**
2. Web crawling spiders built with **Scrapy**
3. Infrastructure as Code (IaC) using **Terraform** to manage GCP resources
4. CI/CD pipeline using **GitHub Actions**

## 1. Chatbot App

The chatbot's backend uses **Langchain** for its RAG architecture and conversational capabilities, while the frontend is built with **Streamlit**. It retrieves relevant information through vector-retrieval in **Firestore** to provide context-aware responses. The chatbot is deployed on GCP using **Google Kubernetes Engine (GKE)**, ensuring scalability and reliability.

![Chatbot App Workflow](https://github.com/tnguyen2907/obot/tree/master/documentation/chatbot-workflow.png)

## 2. Scraper

A **Scrapy** project that scrapes data from the [Oberlin College website](https://www.oberlin.edu) and [catalog](https://www.catalog.oberlin.edu). The scraper processes all HTML and files, encodes the data, and stores it in **Firestore** for efficient vector-based retrieval by the chatbot. All spiders are deployed on **Cloud Run** and scheduled to run daily with **Cloud Scheduler** to keep the chatbot updated with the latest information.

![Scrapy workflow](https://github.com/tnguyen2907/obot/tree/master/documentation/scrapy-workflow.png)


## 3. Terraform

Infrastructure as Code (IaC) is managed using **Terraform**. This component automates the provisioning and management of all necessary resources on GCP, including the **Google Kubernetes Engine** cluster, **Firestore** instance, **Google Artifact Registry** repo, **Cloud Run** job and scheduler, **Cloud Storage** buckets, and **VPC** and **Firewall** configurations. Terraform scripts ensure consistent, reproducible, and scalable infrastructure deployment.

## 4. CI/CD Workflow

The **GitHub Actions** CI/CD pipeline automates the entire deployment process. It builds and publishes Docker images, applies Terraform configurations to provision and manage the infrastructure, and deploys the latest version of the chatbot application to GKE. This workflow ensures continuous integration and delivery, allowing for seamless updates and enhancements.

![CI/CD workflow](https://github.com/tnguyen2907/obot/tree/master/documentation/cicd-workflow.png)

*Note:* Another significant aspect of this project has been setting up authentication for various GCP services using IAM roles, service accounts, and workload identity federation. These configurations were managed through `gcloud` scripts (but not included in this repository).

