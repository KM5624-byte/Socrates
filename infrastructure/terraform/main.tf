terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

variable "project_id" { type = string }
variable "region" { type = string }
variable "service_name" { type = string }
variable "image" {
  type        = string
  description = "Artifact Registry API image pinned to its sha256 digest."
  validation {
    condition     = can(regex("@sha256:[a-f0-9]{64}$", var.image))
    error_message = "Use an immutable image digest."
  }
}
variable "public_read" {
  type        = bool
  default     = false
  description = "Enable internet access for the aggregate, read-only pilot after authorization."
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_service_account" "api" {
  account_id = var.service_name
}

resource "google_cloud_run_v2_service" "api" {
  name                 = var.service_name
  location             = var.region
  deletion_protection  = true
  invoker_iam_disabled = var.public_read

  template {
    service_account                  = google_service_account.api.email
    timeout                          = "15s"
    max_instance_request_concurrency = 8
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image = var.image
      ports { container_port = 8080 }
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
      startup_probe {
        http_get { path = "/readyz" }
        timeout_seconds   = 5
        period_seconds    = 10
        failure_threshold = 4
      }
      liveness_probe {
        http_get { path = "/healthz" }
        timeout_seconds = 3
        period_seconds  = 15
      }
    }
  }
}

output "api_url" { value = google_cloud_run_v2_service.api.uri }
