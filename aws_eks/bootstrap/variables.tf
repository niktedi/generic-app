variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "project" {
  description = "Project name prefix for resources"
  type        = string
  default     = "generic-app-eks"
}
