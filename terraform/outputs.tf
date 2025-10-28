output "raw_bucket_arn" {
  value = aws_s3_bucket.raw_data.arn
}

output "processed_bucket_arn" {
  value = aws_s3_bucket.processed_data.arn
}

output "analytics_bucket_arn" {
  value = aws_s3_bucket.analytics_data.arn
}
