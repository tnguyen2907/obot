resource "google_artifact_registry_repository" "obot-dev-repo" {
  repository_id = "obot-dev"
  project       = var.GCP_PROJECT_ID
  location      = var.REGION
  format = "DOCKER"

  cleanup_policy_dry_run = false
  cleanup_policies {
    id = "keep-in-use"
    action = "KEEP"
    condition {
      tag_state = "TAGGED"
      tag_prefixes = ["in-use"]
    }
  }

  cleanup_policies {
    id = "keep-most-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 3
    }
  }

  cleanup_policies {
    id = "delete-old"
    action = "DELETE"
    condition {
      tag_state = "ANY"
      older_than = "1209600s"
    }
  }
}

resource "google_artifact_registry_repository" "obot-prod-repo" {
  repository_id = "obot-prod"
  project       = var.GCP_PROJECT_ID
  location      = var.REGION
  format = "DOCKER"

  cleanup_policies {
    id = "keep-in-use"
    action = "KEEP"
    condition {
      tag_state = "TAGGED"
      tag_prefixes = ["in-use"]
    }
  }

  cleanup_policies {
    id = "keep-most-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id = "delete-old"
    action = "DELETE"
    condition {
      tag_state = "ANY"
      older_than = "2419200s"
    }
  }
}