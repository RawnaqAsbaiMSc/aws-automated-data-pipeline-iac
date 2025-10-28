output "layer_arn" {
  description = "ARN of the created lambda layer version"
  value       = length(aws_lambda_layer_version.this) > 0 ? aws_lambda_layer_version.this[0].arn : ""
}

output "s3_bucket" {
  description = "Artifacts bucket used"
  value       = local.artifacts_bucket
}

output "s3_key" {
  description = "S3 key of uploaded layer"
  value       = length(aws_s3_bucket_object.layer) > 0 ? aws_s3_bucket_object.layer[0].key : ""
}
