resource "google_compute_instance" "prod_chatbot_instance" {
  name         = "prod-chatbot-instance"
  machine_type = "e2-micro"
  zone         = "${var.REGION}-b"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    network    = google_compute_network.my-vpc.id
    subnetwork = google_compute_subnetwork.gke-subnet.id
    access_config {
      network_tier = "STANDARD"
    }
  }

  service_account {
    email  = "obot-chatbot@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }

  allow_stopping_for_update = true

  metadata_startup_script = templatefile(
    "${path.module}/vm_startup.sh",
    {
      gcp_project_id = var.GCP_PROJECT_ID
      region         = var.REGION
      env            = "prod"
    }
  )
}

resource "google_compute_instance" "dev_chatbot_instance" {
  count = var.ENV == "dev" ? 1 : 0

  name         = "dev-chatbot-instance"
  machine_type = "e2-micro"
  zone         = "${var.REGION}-b"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    network    = google_compute_network.my-vpc.id
    subnetwork = google_compute_subnetwork.gke-subnet.id
    access_config {
      network_tier = "STANDARD"
    }
  }

  service_account {
    email  = "obot-chatbot@${var.GCP_PROJECT_ID}.iam.gserviceaccount.com"
    scopes = ["cloud-platform"]
  }

  allow_stopping_for_update = true

  metadata_startup_script = templatefile(
    "${path.module}/vm_startup.sh",
    {
      gcp_project_id = var.GCP_PROJECT_ID
      region         = var.REGION
      env            = "dev"
    }
  )
}
