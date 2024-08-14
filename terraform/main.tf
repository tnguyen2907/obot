terraform {
  backend "gcs" {
    bucket  = "obot-tfstate"
  }
}

provider "google-beta" {
  project = var.project_id
}

provider "google" {
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

# resource "google_project_service" "artifact_registry" {
#   project = var.project_id
#   service = "artifactregistry.googleapis.com"
# }

resource "google_project_service" "compute" {
  project = var.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  project = var.project_id
  service = "container.googleapis.com"
}


resource "google_artifact_registry_repository" "obot-repo" {
  repository_id = "obot"
  project       = var.project_id
  location      = "us-east4"
  format = "DOCKER"
}