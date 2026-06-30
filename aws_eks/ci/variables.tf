variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "github_repo" {
  description = "GitHub repo in owner/name form, used in OIDC trust condition"
  type        = string
  default     = "niktedi/git-act"
}

variable "ecr_repo_name" {
  description = "ECR repository name"
  type        = string
  default     = "git-act"
}