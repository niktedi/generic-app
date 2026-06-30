output "ecr_repository_url" {
  value = aws_ecr_repository.git_act.repository_url
}

output "iam_role_arn" {
  description = "Role ARN to put in the GitHub Actions workflow"
  value       = aws_iam_role.github_actions_ecr_push.arn
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}