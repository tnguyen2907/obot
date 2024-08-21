resource "google_storage_bucket" "scraper-logs" {
  name = "obot-scraper-logs"
  location = var.REGION
  force_destroy = true
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"
}

resource "google_storage_bucket" "scraper-output" {
  name = "obot-scraper-output"
  location = var.REGION
  force_destroy = true
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"
}

locals {
  spiders = {
    blogspider = {
      schedule = "50 13 * * 4"
    }
    bulletinspider = {
      schedule = "50 13 * * 4"
    }
    catalogspider = {
      schedule = "50 13 * * 4"
    }
    eventspider = {
      schedule = "50 13 * * 4"
    }
    newsspider = {
      schedule = "50 13 * * 4"
    }
    oberlinspider = {
      schedule = "50 13 * * 4"
    }
  }
}

# Get digest of the image
data "google_artifact_registry_docker_image" "scraper-image" {
  repository_id = google_artifact_registry_repository.obot-prod-repo.repository_id
  location = google_artifact_registry_repository.obot-prod-repo.location
  image_name = "scraper:in-use"
}

resource "google_cloud_run_v2_job" "spiders" {
  for_each = local.spiders
  name = each.key
  location = var.REGION
  template {
    template {
      service_account = "obot-scraper@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
      timeout = "7200s"
      containers {
        image = data.google_artifact_registry_docker_image.scraper-image.self_link
        command = [ "python", "run_spiders.py", each.key]
      }
    }
  }

  depends_on = [ data.google_artifact_registry_docker_image.scraper-image ]
}

resource "google_cloud_scheduler_job" "scraper-schedule" {
  for_each = local.spiders
  name = "${each.key}-scheduler"
  schedule = each.value.schedule
  time_zone = "America/New_York"
  retry_config {
    retry_count = 3
  }
  http_target {
    http_method = "POST"
    uri = "https://${var.REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${data.google_project.project.number}/jobs/${google_cloud_run_v2_job.spiders[each.key].name}:run"

    oauth_token {
      service_account_email = "obot-scraper@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
    }
  }
  
  depends_on = [ google_cloud_run_v2_job.spiders ]
}