resource "google_compute_network" "my-vpc" {
  name = "my-vpc"
  auto_create_subnetworks = false
  routing_mode = "REGIONAL"
}

resource "google_compute_subnetwork" "gke-subnet" {
  name          = "gke-subnet"
  ip_cidr_range = "10.0.0.0/18"
  network       = google_compute_network.my-vpc.id
  region        = var.REGION
  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.48.0.0/14"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.52.0.0/20"
  }

  depends_on = [ google_compute_network.my-vpc ]
}

# Allow traffic on nodePort
resource "google_compute_firewall" "allow-obot" {
  name    = "allow-obot"
  network = google_compute_network.my-vpc.name

  allow {
    protocol = "tcp"
    ports    = ["30000", "30001"]
  }  

  direction = "INGRESS"
  source_ranges = ["0.0.0.0/0"]
}

# resource "google_compute_router" "my-router" {
#   name    = "my-router"
#   network = google_compute_network.my-vpc.id
#   region = var.REGION
# }

# resource "google_compute_router_nat" "my-nat" {
#   name            = "my-nat"
#   router          = google_compute_router.my-router.name
#   region          = var.REGION

#   source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
#   nat_ip_allocate_option = "AUTO_ONLY"

#   subnetwork {
#     name = google_compute_subnetwork.gke-subnet.id
#     source_ip_ranges_to_nat = [ "ALL_IP_RANGES" ]
#   }
# }

# resource "google_compute_firewall" "allow_outbound" {
#   name    = "allow-outbound"
#   network = google_compute_network.my-vpc.name

#   allow {
#     protocol = "tcp"
#     ports    = ["80", "443"]
#   }

#   direction = "EGRESS"
#   destination_ranges = ["0.0.0.0/0"]
# }