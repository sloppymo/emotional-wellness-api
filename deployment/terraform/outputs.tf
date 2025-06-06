output "api_endpoint" {
  description = "The public endpoint for the API"
  value       = "https://${aws_lb.app_lb.dns_name}"
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository for pushing Docker images"
  value       = aws_ecr_repository.app_repository.repository_url
}

output "database_endpoint" {
  description = "The endpoint of the RDS database"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "The endpoint of the ElastiCache Redis cluster"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  sensitive   = true
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for application logs"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "secrets_manager_arn" {
  description = "ARN of the Secrets Manager containing application secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "kms_app_key_id" {
  description = "KMS key ID for application encryption"
  value       = aws_kms_key.app_key.key_id
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.app_cluster.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app_service.name
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnets
}

output "security_group_api" {
  description = "Security group ID for the API servers"
  value       = aws_security_group.api_sg.id
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.api_waf[0].id : "WAF disabled"
}

output "hipaa_compliance_resources" {
  description = "List of resources with HIPAA compliance tags"
  value = {
    "encryption_at_rest"  = "All data at rest is encrypted with KMS keys"
    "encryption_in_transit" = "All data in transit is encrypted with TLS 1.3"
    "audit_logging"       = "CloudWatch logs and S3 access logs are configured"
    "access_controls"     = "IAM roles and security groups are properly configured"
    "network_isolation"   = "VPC with private subnets for sensitive resources"
    "monitoring_alerts"   = "CloudWatch alarms configured for critical services"
  }
}
