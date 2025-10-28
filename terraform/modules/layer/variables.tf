variable "name" {
  description = "Layer name"
  type        = string
}

variable "filename" {
  description = "Path to local zip file to upload"
  type        = string
  default     = ""
}

variable "create_bucket" {
  description = "Create an S3 bucket for artifacts if true and s3_bucket_name unset"
  type        = bool
  default     = true
}

variable "s3_bucket_name" {
  description = "Use an existing s3 bucket name for artifacts"
  type        = string
  default     = ""
}

variable "s3_key" {
  description = "S3 key to upload the layer zip to"
  type        = string
  default     = ""
}

variable "compatible_runtimes" {
  description = "Compatible runtimes for the layer"
  type        = list(string)
  default     = ["python3.11"]
}
