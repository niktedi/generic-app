variable "project" {
  description = "Project name — prefix for Name tags"
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name (needed for the kubernetes.io/cluster/<name> tag)"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "List of Availability Zones (at least 2 for EKS)"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDRs of the public subnets (one per AZ)"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDRs of the private subnets (one per AZ)"
  type        = list(string)
}
