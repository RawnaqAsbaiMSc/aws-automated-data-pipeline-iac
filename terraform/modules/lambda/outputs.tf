output "lambda_arn" {
  value = length(aws_lambda_function.from_file) > 0 ? aws_lambda_function.from_file[0].arn : aws_lambda_function.from_s3[0].arn
}

output "lambda_name" {
  value = length(aws_lambda_function.from_file) > 0 ? aws_lambda_function.from_file[0].function_name : aws_lambda_function.from_s3[0].function_name
}

output "role_arn" {
  value = aws_iam_role.this.arn
}
