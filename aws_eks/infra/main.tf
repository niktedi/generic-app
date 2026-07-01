data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  source = "./modules/vpc"

  project              = var.project
  cluster_name         = "${var.project}-cluster"
  vpc_cidr             = "10.0.0.0/16"
  azs                  = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnet_cidrs  = ["10.0.0.0/24", "10.0.1.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
}

module "eks" {
  source = "./modules/eks"

  cluster_name        = "${var.project}-cluster"
  kubernetes_version  = "1.33"
  subnet_ids          = concat(module.vpc.public_subnet_ids, module.vpc.private_subnet_ids)
  private_subnet_ids  = module.vpc.private_subnet_ids   # ← added
  public_access_cidrs = var.public_access_cidrs
}






