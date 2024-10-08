# Obot

**Obot** is a conversational AI chatbot designed to answer questions about Oberlin College. Leveraging the Retrieval-Augmented Generation (RAG) model, the chatbot uses data scraped from the college's website to provide provides accurate and context-specific responses to user queries. The application is hosted on Google Cloud Platform (GCP) and is publicly accessible at https://obiebot.com or http://35.196.25.146:30000/

![Chatbot App Demo](assets/chatbot-app-demo.gif)

This repository contains four major components:
1. Chatbot application using **Langchain** and **Streamlit**
2. Web crawling spiders built with **Scrapy**
3. Infrastructure as Code (IaC) using **Terraform** to manage GCP resources
4. CI/CD pipeline using **GitHub Actions**

## 1. Chatbot App

The chatbot's backend uses **Langchain** for its RAG architecture and conversational capabilities, with **Streamlit** for front end, and **Redis** for database. It retrieves relevant information through vector-retrieval in **Firestore** to provide context-aware responses. The chatbot is deployed on GCP using **Google Kubernetes Engine (GKE)**, ensuring scalability and reliability.

![Chatbot App Workflow](assets/chatbot-workflow.png)

For more details, see the [chatbot README](chatbot/README.md).

## 2. Scraper

A **Scrapy** project that scrapes data from the [Oberlin College website](https://www.oberlin.edu) and [catalog](https://www.catalog.oberlin.edu). The scraper processes all HTML and files, encodes the data, and stores it in **Firestore** for efficient vector-based retrieval by the chatbot. All spiders are deployed on **Cloud Run** and scheduled to run daily with **Cloud Scheduler** to keep the chatbot updated with the latest information.

![Scrapy workflow](assets/scrapy-workflow.png)

For more details, see the [scraper README](scraper/README.md).

## 3. Terraform

Infrastructure as Code (IaC) is managed using **Terraform**. This component automates the provisioning and management of all necessary resources on GCP, including the **Google Kubernetes Engine** cluster, **Firestore** instance, **Google Artifact Registry** repo, **Cloud Run** job and scheduler, **Cloud Storage** buckets, and **VPC** and **Firewall** configurations. Terraform scripts ensure consistent, reproducible, and scalable infrastructure deployment.

![Terraform workflow](assets/terraform-workflow.png)

For more details, see the [Terraform README](terraform/README.md).

## 4. CI/CD Workflow

The **GitHub Actions** CI/CD pipeline automates the entire deployment process. It builds and publishes Docker images, applies Terraform configurations to provision and manage the infrastructure, and deploys the latest version of the chatbot application to GKE. This workflow ensures continuous integration and deployment, allowing for seamless updates and enhancements.

![CI/CD workflow](assets/cicd-workflow.png)

For more details, see the [CI/CD pipeline README](.github/workflows/README.md).

*Note: There are two other significant aspects of the project that is not included in this repo:* 
- **Nginx** load balancer for the chatbot application: Leveraging GCP's free tier of an e2-mirco instance with free public IP, I set up an Nginx load balancer to route traffic to the node port of the chatbot application. SSL certificates renewal was also set up using **certbot (and Let's Encrypt)** to enable **HTTPS**.
 - Authentication for various GCP services using IAM roles, service accounts, and workload identity federation. These configurations were managed through `gcloud` scripts.

