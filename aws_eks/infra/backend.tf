terraform {
  backend "s3" {
    bucket       = "generic-app-eks-tfstate-802421411869"
    key          = "eks/terraform.tfstate"
    region       = "eu-central-1"
    use_lockfile = true
    encrypt      = true
  }
}
