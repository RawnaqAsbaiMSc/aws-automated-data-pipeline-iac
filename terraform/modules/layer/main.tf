 

resource "aws_s3_bucket" "artifacts" {
  count  = var.create_bucket && var.s3_bucket_name == "" ? 1 : 0
  bucket = "${var.name}-artifacts-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.name}-artifacts"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  artifacts_bucket = var.s3_bucket_name != "" ? var.s3_bucket_name : length(aws_s3_bucket.artifacts) > 0 ? aws_s3_bucket.artifacts[0].id : ""
}

resource "aws_s3_bucket_object" "layer" {
  count  = var.filename != "" ? 1 : 0
  bucket = local.artifacts_bucket
  key    = var.s3_key
  source = var.filename
  etag   = filemd5(var.filename)
}

resource "aws_lambda_layer_version" "this" {
  count               = var.filename != "" ? 1 : 0
  layer_name          = var.name
  s3_bucket           = local.artifacts_bucket
  s3_key              = aws_s3_bucket_object.layer[0].key
  compatible_runtimes = var.compatible_runtimes
  lifecycle {
    create_before_destroy = true
  }
}


