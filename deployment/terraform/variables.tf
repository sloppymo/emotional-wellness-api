variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "emotional-wellness-api"
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production"
  }
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "availability_zones" {
  description = "AWS availability zones to use"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "api_port" {
  description = "Port for API service"
  type        = number
  default     = 8000
}

variable "log_retention_in_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 731  # 2 years (HIPAA requires 6 years, but we'll set a shorter period for cost control)
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance in GB"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS instance in GB"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "Username for database"
  type        = string
  default     = "wellness"
  sensitive   = true
}

variable "db_password" {
  description = "Password for database"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Name of database"
  type        = string
  default     = "emotional_wellness"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.small"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "ecr_repository_name" {
  description = "Name of ECR repository"
  type        = string
  default     = "emotional-wellness-api"
}

variable "ecs_service_desired_count" {
  description = "Desired count of ECS service tasks"
  type        = number
  default     = 2
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 1024
}

variable "enable_waf" {
  description = "Enable WAF protection"
  type        = bool
  default     = true
}

variable "allowed_ip_ranges" {
  description = "List of IP CIDR blocks allowed to access the API"
  type        = list(string)
  default     = []
}
