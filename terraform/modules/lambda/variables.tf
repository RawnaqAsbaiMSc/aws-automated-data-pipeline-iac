variable "name" {
  type = string
}

variable "role_name" {
  type    = string
  default = null
}

variable "runtime" {
  type    = string
  default = "python3.11"
}

variable "handler" {
  type    = string
  default = "handler.lambda_handler"
}

variable "environment" {
  type    = map(string)
  default = {}
}

variable "layers" {
  type    = list(string)
  default = []
}

variable "function_s3_bucket" {
  type    = string
  default = ""
}

variable "function_s3_key" {
  type    = string
  default = ""
}

variable "filename" {
  type    = string
  default = ""
}

variable "use_filename" {
  type    = bool
  default = false
}

variable "source_bucket" {
  type    = string
  default = ""
}

variable "events" {
  type    = list(string)
  default = ["s3:ObjectCreated:*"]
}

variable "filter_prefix" {
  type    = string
  default = ""
}

variable "filter_suffix" {
  type    = string
  default = ""
}

variable "attach_bucket_arns" {
  type    = list(string)
  default = []
}

variable "memory_size" {
  type    = number
  default = 256
}

variable "timeout" {
  type    = number
  default = 30
}
