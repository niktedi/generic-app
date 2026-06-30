variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes control plane version"
  type        = string
  default     = "1.31"
}

variable "subnet_ids" {
  description = "Subnet IDs for the control plane (private + public, at least 2 AZs)"
  type        = list(string)
}

variable "public_access_cidrs" {
  description = "CIDR blocks allowed to reach the Kubernetes API endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]   # override in tfvars with your /32
}

variable "private_subnet_ids" {
  description = "Private subnets for the worker nodes"
  type        = list(string)
}

variable "node_instance_types" {
  description = "Instance types for the nodes"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes"
  type        = number
  default     = 3
}

variable "node_capacity_type" {
  description = "ON_DEMAND or SPOT"
  type        = string
  default     = "SPOT"
}