variable "project_id" {
  description = "GCloud project ID"
  type        = string
}

variable "region" {
  description = "GCloud region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "postgres_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-custom-1-3840"
}

variable "redis_tier" {
  description = "Memorystore Redis tier (BASIC, STANDARD_HA)"
  type        = string
  default     = "BASIC"
}

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "gke_node_locations" {
  description = "GKE node locations"
  type        = list(string)
  default     = ["us-central1-a", "us-central1-b", "us-central1-c"]
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "langchain_api_key" {
  description = "LangChain API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "credentials_path" {
  description = "Path to GCloud service account JSON key"
  type        = string
  default     = ""
}
