terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Example: three S3 buckets for pipeline stages
resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.prefix}-raw-data-${random_id.bucket_suffix.hex}"
  acl    = "private"
  tags = {
    Name = "${var.prefix}-raw-data-${random_id.bucket_suffix.hex}"
    Env  = var.environment
  }
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.prefix}-processed-data-${random_id.bucket_suffix.hex}"
  acl    = "private"
  tags = {
    Name = "${var.prefix}-processed-data-${random_id.bucket_suffix.hex}"
    Env  = var.environment
  }
}

resource "aws_s3_bucket" "analytics_data" {
  bucket = "${var.prefix}-analytics-data-${random_id.bucket_suffix.hex}"
  acl    = "private"
  tags = {
    Name = "${var.prefix}-analytics-data-${random_id.bucket_suffix.hex}"
    Env  = var.environment
  }
}

# Layer module: upload build/layer.zip to artifacts bucket and create a Lambda Layer version
module "db_layer" {
  source = "./modules/layer"
  name   = "${var.prefix}-db-drivers"

  # For local dev build the zip to build/layer.zip and this module will upload it
  filename = abspath("${path.root}/../build/layer.zip")
  # If you prefer an existing bucket, set s3_bucket_name instead of creating one here
  create_bucket = true
  s3_key = "layers/${var.prefix}-db-drivers.zip"
}

# Placeholder: create Lambda resources by using module or additional resources
# Example module usage would be:
module "ingestion_lambda" {
  source = "./modules/lambda"
  name   = "${var.prefix}-ingestion"

  # For development you can build a zip and point filename to the build artifact
  # or upload to S3 and set function_s3_bucket/function_s3_key and use_filename=false
  filename     = abspath("${path.root}/../build/ingestion_function.zip")
  use_filename = true

  handler = "handler.lambda_handler"
  runtime = "python3.11"

  # Give the function access to put objects into the raw-data bucket
  attach_bucket_arns = [aws_s3_bucket.raw_data.arn]
  # Attach the created layer
  layers = module.db_layer.layer_arn != "" ? [module.db_layer.layer_arn] : []

  # Wire S3 notifications for objects created in other buckets to trigger this function
  source_bucket = aws_s3_bucket.raw_data.id
  events        = ["s3:ObjectCreated:*"]
  filter_prefix = ""
  filter_suffix = ".json"
  environment = {
    DB_TYPE      = "sqlite"
    DB_S3_BUCKET = aws_s3_bucket.raw_data.bucket
    DB_S3_KEY    = "db/chinook.db"
    RAW_BUCKET   = aws_s3_bucket.raw_data.bucket
    INGEST_QUERY = "SELECT Track.TrackId AS TrackId, Track.Name AS Name, Album.Title AS Title, Track.Composer AS Composer, Track.Milliseconds AS Milliseconds, Track.UnitPrice AS UnitPrice FROM Track JOIN Album ON Track.AlbumId = Album.AlbumId LIMIT 500"
  }
}

module "processing_lambda" {
  source = "./modules/lambda"
  name   = "${var.prefix}-processing"
  filename     = abspath("${path.root}/../build/processing_function.zip")
  use_filename = true

  handler = "handler.lambda_handler"
  runtime = "python3.11"

  # Will need access to raw and processed buckets during processing
  attach_bucket_arns = [aws_s3_bucket.raw_data.arn, aws_s3_bucket.processed_data.arn]
  layers = module.db_layer.layer_arn != "" ? [module.db_layer.layer_arn] : []

  # Trigger on new raw objects
  source_bucket = aws_s3_bucket.raw_data.id
  events        = ["s3:ObjectCreated:*"]
  filter_prefix = "raw/"
  filter_suffix = ".json"
  environment = {
    RAW_BUCKET = aws_s3_bucket.raw_data.bucket
    PROCESSED_BUCKET = aws_s3_bucket.processed_data.bucket
    ANALYTICS_BUCKET = aws_s3_bucket.analytics_data.bucket
  }
}

module "analytics_lambda" {
  source = "./modules/lambda"
  name   = "${var.prefix}-analytics"
  filename     = abspath("${path.root}/../build/analytics_function.zip")
  use_filename = true

  handler = "handler.lambda_handler"
  runtime = "python3.11"

  attach_bucket_arns = [aws_s3_bucket.processed_data.arn, aws_s3_bucket.analytics_data.arn]
  layers = module.db_layer.layer_arn != "" ? [module.db_layer.layer_arn] : []

  # Trigger on new processed objects
  source_bucket = aws_s3_bucket.processed_data.id
  events        = ["s3:ObjectCreated:*"]
  filter_prefix = "processed/"
  filter_suffix = ".json"
  environment = {
    ANALYTICS_BUCKET = aws_s3_bucket.analytics_data.bucket
  }
}

output "raw_bucket" {
  value = aws_s3_bucket.raw_data.bucket
}

output "processed_bucket" {
  value = aws_s3_bucket.processed_data.bucket
}

output "analytics_bucket" {
  value = aws_s3_bucket.analytics_data.bucket
}
