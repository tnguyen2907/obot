terraform {
  backend "gcs" {
    bucket  = "obot-tfstate"
  }
}

provider "google-beta" {
  project = var.GCP_PROJECT_ID
  region = var.REGION
}

provider "google" {
  project = var.GCP_PROJECT_ID
  region = var.REGION
}

data "google_project" "project" {
}

resource "google_project_service" "firestore" {
  project = var.GCP_PROJECT_ID
  service = "firestore.googleapis.com"
}

resource "google_project_service" "vertex_ai" {
  project = var.GCP_PROJECT_ID
  service = "aiplatform.googleapis.com"
}

# resource "google_project_service" "artifact_registry" {
#   project = var.GCP_PROJECT_ID
#   service = "artifactregistry.googleapis.com"
# }

resource "google_project_service" "compute" {
  project = var.GCP_PROJECT_ID
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  project = var.GCP_PROJECT_ID
  service = "container.googleapis.com"
}

resource "google_project_service" "cloud_scheduler" {
  project = var.GCP_PROJECT_ID
  service = "cloudscheduler.googleapis.com"
}