provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "EmotionalWellnessAPI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Enable versioning for state file
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # These values must be provided via CLI or environment variables
    # bucket         = "terraform-state-bucket"
    # key            = "emotional-wellness-api/terraform.tfstate"
    # region         = "us-west-2"
    # dynamodb_table = "terraform-locks"
    # encrypt        = true
  }
}

# VPC for HIPAA-compliant networking
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "${var.project_name}-${var.environment}"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  one_nat_gateway_per_az = var.environment == "production"
  
  enable_vpn_gateway = var.environment == "production"
  
  # Enable VPC flow logs for compliance
  enable_flow_log                      = true
  flow_log_destination_type            = "cloud-watch-logs"
  flow_log_destination_arn             = aws_cloudwatch_log_group.vpc_flow_logs.arn
  flow_log_cloudwatch_iam_role_arn     = aws_iam_role.vpc_flow_log_role.arn
  flow_log_traffic_type                = "ALL"
  flow_log_max_aggregation_interval    = 60

  # DNS settings
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Default security group - ingress/egress rules cleared to deny all
  manage_default_security_group  = true
  default_security_group_ingress = []
  default_security_group_egress  = []

  tags = {
    Compliance = "HIPAA"
  }
}

# CloudWatch log group for VPC flow logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${var.project_name}-${var.environment}/flow-logs"
  retention_in_days = var.log_retention_in_days
  kms_key_id        = aws_kms_key.logs_key.arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs"
    Compliance  = "HIPAA"
  }
}

# IAM role for VPC flow logs
resource "aws_iam_role" "vpc_flow_log_role" {
  name = "${var.project_name}-${var.environment}-vpc-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc-flow-log-role"
    Compliance = "HIPAA"
  }
}

# IAM policy for VPC flow logs
resource "aws_iam_role_policy" "vpc_flow_log_policy" {
  name = "${var.project_name}-${var.environment}-vpc-flow-log-policy"
  role = aws_iam_role.vpc_flow_log_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "${aws_cloudwatch_log_group.vpc_flow_logs.arn}:*"
      }
    ]
  })
}

# KMS key for CloudWatch logs encryption
resource "aws_kms_key" "logs_key" {
  description             = "${var.project_name}-${var.environment}-logs-key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*"
        ]
        Resource = "*"
        Condition = {
          ArnEquals = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/vpc/${var.project_name}-${var.environment}/flow-logs"
          }
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-logs-key"
    Compliance = "HIPAA"
  }
}

# Get current account ID
data "aws_caller_identity" "current" {}

# Security group for API servers
resource "aws_security_group" "api_sg" {
  name        = "${var.project_name}-${var.environment}-api-sg"
  description = "Security group for API servers"
  vpc_id      = module.vpc.vpc_id

  # HTTPS inbound
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS inbound"
  }

  # API port inbound (internal)
  ingress {
    from_port   = var.api_port
    to_port     = var.api_port
    protocol    = "tcp"
    cidr_blocks = concat(var.private_subnets, var.public_subnets)
    description = "API port inbound (internal)"
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-sg"
    Compliance = "HIPAA"
  }
}

# Security group for database
resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-${var.environment}-db-sg"
  description = "Security group for database"
  vpc_id      = module.vpc.vpc_id

  # Database port inbound (from API servers only)
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
    description     = "PostgreSQL from API servers"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-sg"
    Compliance = "HIPAA"
  }
}

# Security group for Redis
resource "aws_security_group" "redis_sg" {
  name        = "${var.project_name}-${var.environment}-redis-sg"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id

  # Redis port inbound (from API servers only)
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.api_sg.id]
    description     = "Redis from API servers"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-sg"
    Compliance = "HIPAA"
  }
}

# KMS key for database encryption
resource "aws_kms_key" "db_key" {
  description             = "${var.project_name}-${var.environment}-db-key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name = "${var.project_name}-${var.environment}-db-key"
    Compliance = "HIPAA"
  }
}

# KMS key alias
resource "aws_kms_alias" "db_key_alias" {
  name          = "alias/${var.project_name}-${var.environment}-db-key"
  target_key_id = aws_kms_key.db_key.key_id
}
