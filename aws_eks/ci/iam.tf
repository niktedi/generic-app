# Trust policy: who can assume the role
data "aws_iam_policy_document" "trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_actions_ecr_push" {
  name               = "github-actions-ecr-push"
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

# Permissions: what the role can do
data "aws_iam_policy_document" "ecr_push" {
  statement {
    sid       = "GetAuthToken"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid    = "PushToGenericAppRepo"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [aws_ecr_repository.generic_app.arn]
  }
}

resource "aws_iam_role_policy" "ecr_push" {
  name   = "ecr-push-generic-app"
  role   = aws_iam_role.github_actions_ecr_push.id
  policy = data.aws_iam_policy_document.ecr_push.json
}