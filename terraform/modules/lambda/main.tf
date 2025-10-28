terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# IAM role for Lambda
resource "aws_iam_role" "this" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Basic policy for CloudWatch Logs and S3 access (scaffold)
data "aws_iam_policy_document" "this" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  dynamic "statement" {
    for_each = var.attach_bucket_arns
    content {
      actions   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
      resources = [statement.value]
    }
  }
}

resource "aws_iam_role_policy" "this" {
  name   = "${var.name}-policy"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.this.json
}

# Create lambda from local zip file (filename) when provided
resource "aws_lambda_function" "from_file" {
  count = var.use_filename ? 1 : 0

  filename         = var.filename
  function_name    = var.name
  role             = aws_iam_role.this.arn
  handler          = var.handler
  runtime          = var.runtime
  source_code_hash = filebase64sha256(var.filename)
  environment {
    variables = var.environment
  }
  layers = var.layers
  memory_size = var.memory_size
  timeout     = var.timeout
}

# Create lambda from S3 object when filename not provided
resource "aws_lambda_function" "from_s3" {
  count = var.use_filename ? 0 : 1

  s3_bucket        = var.function_s3_bucket
  s3_key           = var.function_s3_key
  function_name    = var.name
  role             = aws_iam_role.this.arn
  handler          = var.handler
  runtime          = var.runtime
  environment {
    variables = var.environment
  }
  layers = var.layers
  memory_size = var.memory_size
  timeout     = var.timeout
}

locals {
  lambda_arn = var.use_filename ? aws_lambda_function.from_file[0].arn : aws_lambda_function.from_s3[0].arn
  lambda_name = var.use_filename ? aws_lambda_function.from_file[0].function_name : aws_lambda_function.from_s3[0].function_name
}

# Allow S3 to invoke the Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke${var.name}"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.source_bucket}"
}

# Configure the bucket notification to invoke the lambda for events
resource "aws_s3_bucket_notification" "this" {
  bucket = var.source_bucket

  lambda_function {
    lambda_function_arn = local.lambda_arn
    events              = var.events
    filter_prefix       = var.filter_prefix
    filter_suffix       = var.filter_suffix
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

