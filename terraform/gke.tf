resource "google_container_cluster" "primary" {
  name     = "primary"
  location = "${var.REGION}-b"
  deletion_protection = false
  remove_default_node_pool = true
  initial_node_count = 1
  network = google_compute_network.my-vpc.self_link
  subnetwork = google_compute_subnetwork.gke-subnet.self_link
#   logging_service = "logging.googleapis.com/kubernetes"
  networking_mode = "VPC_NATIVE"

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
  }

  release_channel {
    channel = "UNSPECIFIED"
  }

  workload_identity_config {
    workload_pool = "${var.GCP_PROJECT_ID}.svc.id.goog"
  }

  ip_allocation_policy {
    cluster_secondary_range_name = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  private_cluster_config {
    enable_private_endpoint = false
    enable_private_nodes = true
    master_ipv4_cidr_block = "172.16.0.0/28"
  }
}

resource "google_container_node_pool" "prod-node-pool" {
  name = "prod-node-pool"
  location = "${var.REGION}-b"
  cluster = google_container_cluster.primary.id

  management {
    auto_repair = true
    auto_upgrade = true
  }

  autoscaling {
    total_min_node_count = 0
    total_max_node_count = 1
  }

  node_config {
    preemptible = true
    machine_type = "e2-small"
    disk_type = "pd-standard"
    disk_size_gb = 10

    labels = {
      env = "prod"
    }

    # taint {
    #   key = "env"
    #   value = "prod"
    #   effect = "NO_SCHEDULE"
    # }

    taint {
      key = "env"
      value = "prod"
      effect = "PREFER_NO_SCHEDULE"
    }

    service_account = "obot-chatbot@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      "https://www.googleapis.com/auth/devstorage.read_only"
    ]
  }

  depends_on = [ google_container_cluster.primary ]
}

resource "google_container_node_pool" "dev-node-pool" {
  name = "dev-node-pool"
  location = "${var.REGION}-b"
  cluster = google_container_cluster.primary.id

  management {
    auto_repair = true
    auto_upgrade = true
  }

  autoscaling {
    total_min_node_count = 0
    total_max_node_count = 1
  }

  node_config {
    preemptible = true
    machine_type = "e2-small"
    disk_type = "pd-standard"
    disk_size_gb = 10

    labels = {
      env = "dev"
    }

    taint {
      key = "env"
      value = "dev"
      effect = "NO_SCHEDULE"
    }

    service_account = "obot-chatbot@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      "https://www.googleapis.com/auth/devstorage.read_only"
    ]
  }

  depends_on = [ google_container_cluster.primary ]
}

resource "google_container_node_pool" "free-tier-node-pool" {
  name = "free-tier-node-pool"
  location = "${var.REGION}-b"
  cluster = google_container_cluster.primary.id

  management {
    auto_repair = true
    auto_upgrade = true
  }

  node_count = 1

  node_config {
    machine_type = "e2-micro"
    disk_type = "pd-standard"
    disk_size_gb = 10

    service_account = "obot-chatbot@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
      "https://www.googleapis.com/auth/devstorage.read_only"
    ]
  }

  depends_on = [ google_container_cluster.primary ]
}
  
