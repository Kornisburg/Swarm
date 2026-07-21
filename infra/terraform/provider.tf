provider "google" {
  project     = var.project_id
  region      = var.region
  credentials = var.credentials_path
}

provider "google-beta" {
  project     = var.project_id
  region      = var.region
  credentials = var.credentials_path
}

data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${module.gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.ca_certificate)
}
