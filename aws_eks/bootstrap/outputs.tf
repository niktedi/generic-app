output "state_bucket_name" {
  description = "S3 bucket name for the main project backend"
  value       = aws_s3_bucket.tfstate.id
}


output "region" {
  value = var.region
}
