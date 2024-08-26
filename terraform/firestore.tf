resource "google_firestore_database" "database" {
  provider    = google-beta
  name        = "(default)"
  location_id = var.REGION
  type        = "FIRESTORE_NATIVE"
  deletion_policy = "ABANDON"

  depends_on = [google_project_service.firestore]
}


resource "google_firestore_index" "vector-index" {
  provider = google-beta
  database = google_firestore_database.database.name
  collection = "vector_index"
  query_scope = "COLLECTION"

  fields {
    field_path = "__name__"
    order = "ASCENDING"
  }

  fields {
    field_path = "embedding"
    vector_config {
      dimension = 768
      flat {}
    }
  }

  depends_on = [google_firestore_database.database]
}