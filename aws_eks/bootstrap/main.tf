terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # backend intentionally NOT set — state is local (chicken-and-egg)
}

provider "aws" {
  region = var.region
}

# Current account — used for a unique bucket name
data "aws_caller_identity" "current" {}

locals {
  bucket_name = "${var.project}-tfstate-${data.aws_caller_identity.current.account_id}"
  table_name  = "${var.project}-tflock"
}

# --- S3 bucket for Terraform state ---
resource "aws_s3_bucket" "tfstate" {
  bucket = local.bucket_name

  # protect against accidental destroy of the state bucket itself
  lifecycle {
    prevent_destroy = true
  }
}

# Versioning: keeps state history so you can roll back if it gets corrupted
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Server-side encryption of the state (the state holds secrets!)
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access entirely
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true
  block_public_policy      = true
  ignore_public_acls       = true
  restrict_public_buckets  = true
}

# --- DynamoDB for state locking ---
resource "aws_dynamodb_table" "tflock" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"   # no provisioned capacity — pay per request, pennies for locking
  hash_key     = "LockID"            # Terraform expects exactly this key name

  attribute {
    name = "LockID"
    type = "S"
  }
}
