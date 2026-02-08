# =============================================================================
# Cold Chain Digital Twin - EKS Outputs (Phase 2)
# =============================================================================

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_certificate_authority" {
  description = "EKS cluster CA certificate"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "eks_node_security_group_id" {
  description = "Security group ID for EKS nodes"
  value       = aws_security_group.eks_nodes.id
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for bridge image"
  value       = aws_ecr_repository.bridge.repository_url
}

output "ecr_ingestion_url" {
  description = "ECR repository URL for ingestion image"
  value       = aws_ecr_repository.ingestion.repository_url
}

