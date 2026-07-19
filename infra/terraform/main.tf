locals {
  name_prefix = "hive-${var.environment}"
  db_password = random_password.postgres.result
}

# ---------------------------------------------------------------------------
# Artifact Registry — Docker image storage
# ---------------------------------------------------------------------------
resource "google_artifact_registry_repository" "hive" {
  location      = var.region
  repository_id = "${local.name_prefix}-images"
  description   = "Docker images for The Hive"
  format        = "DOCKER"
  labels        = { environment = var.environment }
}

# ---------------------------------------------------------------------------
# Cloud SQL — PostgreSQL
# ---------------------------------------------------------------------------
resource "random_password" "postgres" {
  length  = 24
  special = false
}

resource "google_sql_database_instance" "postgres" {
  name             = "${local.name_prefix}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.postgres_tier
    disk_type         = "PD_SSD"
    disk_size         = 10
    disk_autoresize   = true
    availability_type = "ZONAL"

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = module.vpc.network_id
    }
  }

  deletion_protection = false

  depends_on = [google_service_networking_connection.private_service_access]
}

resource "google_sql_database" "hive" {
  name     = "the_hive"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "hive" {
  name     = "hive_user"
  instance = google_sql_database_instance.postgres.name
  password = local.db_password
}

# ---------------------------------------------------------------------------
# Memorystore — Redis
# ---------------------------------------------------------------------------
resource "google_redis_instance" "redis" {
  name                = "${local.name_prefix}-redis"
  tier                = var.redis_tier
  memory_size_gb      = var.redis_memory_size_gb
  region              = var.region
  connect_mode        = "PRIVATE_SERVICE_ACCESS"
  authorized_network  = module.vpc.network_id
  display_name        = "The Hive Redis"
  labels              = { environment = var.environment }

  depends_on = [google_service_networking_connection.private_service_access]
}

# ---------------------------------------------------------------------------
# VPC
# ---------------------------------------------------------------------------
module "vpc" {
  source       = "terraform-google-modules/network/google"
  version      = "~> 8.0"
  project_id   = var.project_id
  network_name = "${local.name_prefix}-vpc"
  routing_mode = "REGIONAL"

  subnets = [
    {
      subnet_name           = "${local.name_prefix}-subnet"
      subnet_ip             = "10.0.0.0/20"
      subnet_region         = var.region
      subnet_private_access = true
    }
  ]

  secondary_ranges = {
    "${local.name_prefix}-subnet" = [
      { range_name = "pods", ip_cidr_range = "10.1.0.0/16" },
      { range_name = "services", ip_cidr_range = "10.2.0.0/20" },
    ]
  }
}

# Private service access for Cloud SQL + Memorystore
resource "google_compute_global_address" "private_service_access" {
  name          = "${local.name_prefix}-private-sa"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = module.vpc.network_id
}

resource "google_service_networking_connection" "private_service_access" {
  network                 = module.vpc.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access.name]
}

# ---------------------------------------------------------------------------
# GKE Autopilot
# ---------------------------------------------------------------------------
module "gke" {
  source                   = "terraform-google-modules/kubernetes-engine/google//modules/beta-autopilot-public-cluster"
  version                  = "~> 30.0"
  project_id               = var.project_id
  name                     = "${local.name_prefix}-cluster"
  regional                 = true
  region                   = var.region
  network                  = module.vpc.network_name
  subnetwork               = module.vpc.subnets_names[0]
  ip_range_pods            = "pods"
  ip_range_services        = "services"
  release_channel          = "REGULAR"
  create_service_account   = true
  grant_registry_access    = true
}

# ---------------------------------------------------------------------------
# Kubernetes resources (applied via Terraform)
# ---------------------------------------------------------------------------
resource "kubernetes_namespace" "hive" {
  metadata { name = "hive" }
}

resource "kubernetes_config_map" "hive_config" {
  metadata {
    name      = "hive-config"
    namespace = kubernetes_namespace.hive.metadata[0].name
  }

  data = {
    # App
    API_HOST                            = "0.0.0.0"
    API_PORT                            = "8000"
    LLM_PROVIDER                        = "openai"
    MODEL_TEMPERATURE                   = "0.7"
    MAX_TOKENS                          = "4096"
    # Postgres
    POSTGRES_HOST                       = google_sql_database_instance.postgres.private_ip_address
    POSTGRES_PORT                       = "5432"
    POSTGRES_DB                         = google_sql_database.hive.name
    POSTGRES_USER                       = google_sql_user.hive.name
    # Redis
    REDIS_HOST                          = google_redis_instance.redis.host
    REDIS_PORT                          = "6379"
    # Vector store
    VECTOR_STORE_TYPE                   = "chroma"
    CHROMA_HOST                         = "chroma-service.hive.svc.cluster.local"
    CHROMA_PORT                         = "8000"
    CHROMA_PERSIST_DIR                   = "/data/chroma"
    # Observability
    LANGCHAIN_TRACING_V2                = "true"
    LANGCHAIN_PROJECT                   = "hive-${var.environment}"
    # Sandbox
    SANDBOX_TYPE                        = "docker"
    DOCKER_NETWORK                      = "none"
    # Security
    RATE_LIMIT_ENABLED                  = "true"
    RATE_LIMIT_REQUESTS_PER_MINUTE      = "100"
  }
}

resource "kubernetes_secret" "hive_secrets" {
  metadata {
    name      = "hive-secrets"
    namespace = kubernetes_namespace.hive.metadata[0].name
  }

  data = {
    postgres-password  = local.db_password
    openai-api-key     = var.openai_api_key
    anthropic-api-key  = var.anthropic_api_key
    langchain-api-key  = var.langchain_api_key
  }
}
