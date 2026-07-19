output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = module.gke.endpoint
  sensitive   = true
}

output "artifact_registry_repo" {
  description = "Artifact Registry Docker repository"
  value       = google_artifact_registry_repository.hive.name
}

output "artifact_registry_repo_id" {
  description = "Full Artifact Registry repository ID"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.hive.repository_id}"
}

output "postgres_private_ip" {
  description = "Cloud SQL private IP"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "postgres_connection_name" {
  description = "Cloud SQL connection name (for Cloud SQL Proxy)"
  value       = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  description = "Redis host"
  value       = google_redis_instance.redis.host
}

output "redis_port" {
  description = "Redis port"
  value       = google_redis_instance.redis.port
}

output "vpc_network" {
  description = "VPC network name"
  value       = module.vpc.network_name
}

output "kubectl_connect" {
  description = "Command to connect to the cluster"
  value       = "gcloud container clusters get-credentials ${module.gke.name} --region ${var.region} --project ${var.project_id}"
}
