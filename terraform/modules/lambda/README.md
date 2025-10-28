Module: lambda

This directory is a placeholder for a reusable Lambda module.

Recommended inputs:
- name: Name/prefix for resources
- s3_bucket: S3 bucket to watch (for event triggers)
- handler_s3_key: S3 key for lambda zip (or use local build + upload step)
- role_arn: IAM role ARN for the Lambda
- runtime: "python3.11" etc.

Recommended outputs:
- lambda_arn
- lambda_name

Note: implement this module with `aws_iam_role`, `aws_lambda_function`, `aws_s3_bucket_notification`, and `aws_lambda_permission` to allow S3 to invoke the Lambda.
