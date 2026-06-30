terraform {
  backend "s3" {
    bucket       = "eks-learning-tfstate-802421411869"
    key          = "ci/terraform.tfstate"
    region       = "eu-central-1"
    profile      = "admin"
    encrypt      = true
    use_lockfile = true
  }
}