output "state_bucket_name" {
  description = "S3 bucket name for the main project backend"
  value       = aws_s3_bucket.tfstate.id
}

output "lock_table_name" {
  description = "DynamoDB table name for state locking"
  value       = aws_dynamodb_table.tflock.name
}

output "region" {
  value = var.region
}
