resource "google_storage_bucket" "scraper-logs" {
  name = "obot-scraper-logs"
  location = "us-east4"
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"
}
