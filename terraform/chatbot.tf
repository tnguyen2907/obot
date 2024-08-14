

# resource "google_service_account" "chatbot-sa" {
#   account_id   = "chatbot"
#   display_name = "Obot Chatbot Service Account"
#   description  = "Service account for Obot Chatbot that can read from Firestore"
# }

# resource "google_project_iam_member" "chatbot-sa-iam" {
#   project = var.project_id
#   role    = "roles/datastore.user"
#   member  = "serviceAccount:${google_service_account.chatbot-sa.email}"
# }
