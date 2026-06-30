variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name"
  type        = string
  default     = "admin"
}

variable "project" {
  description = "Project name prefix"
  type        = string
  default     = "generic-app-eks"
}

variable "public_access_cidrs" {
  description = "CIDRs allowed to access the cluster API"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}