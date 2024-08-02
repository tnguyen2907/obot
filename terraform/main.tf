terraform {
  backend "gcs" {
    bucket  = "obot-tfstate"
  }
}

provider "google-beta" {
  project = var.project_id
}

resource "google_project_service" "firestore" {
  project = var.project_id
  service = "firestore.googleapis.com"
}

resource "google_project_service" "vertex_ai" {
  project = var.project_id
  service = "aiplatform.googleapis.com"
}