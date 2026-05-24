variable "project" {
  type    = string
  default = "civiceye"
}

variable "cloud_provider" {
  type        = string
  description = "aws, gcp, azure, runpod, vast, or lambda-labs"
  default     = "aws"
}

variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "cidr_block" {
  type    = string
  default = "10.42.0.0/16"
}

variable "gpu_instance_type" {
  type    = string
  default = "g5.xlarge"
}

variable "db_engine" {
  type        = string
  description = "rds, cloudsql, supabase, neon, or external"
  default     = "rds"
}

variable "redis_provider" {
  type        = string
  description = "elasticache, upstash, redis-cloud, or external"
  default     = "elasticache"
}

variable "object_storage_provider" {
  type        = string
  description = "s3, r2, supabase, or external"
  default     = "s3"
}
