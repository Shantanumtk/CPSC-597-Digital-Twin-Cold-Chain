# =============================================================================
# Cold Chain Digital Twin - ECR Repository (Phase 2)
# =============================================================================

resource "aws_ecr_repository" "bridge" {
  name                 = "${var.project_name}-bridge"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-bridge"
  }
}

resource "aws_ecr_lifecycle_policy" "bridge" {
  repository = aws_ecr_repository.bridge.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}