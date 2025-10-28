variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "my-pipeline"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "dev"
}
