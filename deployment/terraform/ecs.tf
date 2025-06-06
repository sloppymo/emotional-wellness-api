# ECS Fargate resources for HIPAA-compliant application deployment

# ECR repository for container images
resource "aws_ecr_repository" "app_repository" {
  name                 = "${var.ecr_repository_name}-${var.environment}"
  image_tag_mutability = "IMMUTABLE"  # HIPAA compliance - enforce immutable tags

  image_scanning_configuration {
    scan_on_push = true  # Security scanning on image push
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.app_key.arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-ecr"
    Compliance = "HIPAA"
  }
}

# KMS key for application encryption
resource "aws_kms_key" "app_key" {
  description             = "${var.project_name}-${var.environment}-app-key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  
  tags = {
    Name = "${var.project_name}-${var.environment}-app-key"
    Compliance = "HIPAA"
  }
}

# ECR lifecycle policy for image management
resource "aws_ecr_lifecycle_policy" "app_lifecycle_policy" {
  repository = aws_ecr_repository.app_repository.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 production images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["prod-"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 5 staging images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["staging-"]
          countType     = "imageCountMoreThan"
          countNumber   = 5
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Keep last 3 dev images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["dev-"]
          countType     = "imageCountMoreThan"
          countNumber   = 3
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 4
        description  = "Expire untagged images after 1 day"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 1
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECS Cluster
resource "aws_ecs_cluster" "app_cluster" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  configuration {
    execute_command_configuration {
      kms_key_id = aws_kms_key.app_key.arn
      logging    = "OVERRIDE"
      
      log_configuration {
        cloud_watch_encryption_enabled = true
        cloud_watch_log_group_name     = aws_cloudwatch_log_group.ecs_exec_logs.name
      }
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cluster"
    Compliance = "HIPAA"
  }
}

# CloudWatch log group for ECS exec
resource "aws_cloudwatch_log_group" "ecs_exec_logs" {
  name              = "/aws/ecs/${var.project_name}-${var.environment}/exec"
  retention_in_days = var.log_retention_in_days
  kms_key_id        = aws_kms_key.logs_key.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-ecs-exec-logs"
    Compliance = "HIPAA"
  }
}

# CloudWatch log group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ecs/${var.project_name}-${var.environment}/app"
  retention_in_days = var.log_retention_in_days
  kms_key_id        = aws_kms_key.logs_key.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-app-logs"
    Compliance = "HIPAA"
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_name}-${var.environment}-task-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-task-execution-role"
    Compliance = "HIPAA"
  }
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-${var.environment}-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-task-role"
    Compliance = "HIPAA"
  }
}

# IAM Policy for accessing Secrets Manager
resource "aws_iam_policy" "secrets_access" {
  name        = "${var.project_name}-${var.environment}-secrets-access"
  description = "Policy for accessing secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "kms:Decrypt"
        ]
        Resource = [
          aws_secretsmanager_secret.app_secrets.arn,
          aws_kms_key.app_key.arn
        ]
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# Secrets Manager for application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${var.project_name}/${var.environment}/app-secrets"
  description             = "Application secrets for ${var.project_name} ${var.environment}"
  kms_key_id              = aws_kms_key.app_key.arn
  recovery_window_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-app-secrets"
    Compliance = "HIPAA"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app_task" {
  family                   = "${var.project_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  # Enable container insights and ECS Exec for debugging
  enable_execute_command = var.environment != "production"

  container_definitions = jsonencode([
    {
      name         = "app"
      image        = "${aws_ecr_repository.app_repository.repository_url}:latest"
      essential    = true
      portMappings = [
        {
          containerPort = var.api_port
          hostPort      = var.api_port
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "POSTGRES_HOST"
          value = aws_db_instance.postgres.address
        },
        {
          name  = "POSTGRES_PORT"
          value = tostring(aws_db_instance.postgres.port)
        },
        {
          name  = "POSTGRES_DB"
          value = aws_db_instance.postgres.db_name
        },
        {
          name  = "REDIS_HOST"
          value = aws_elasticache_replication_group.redis.primary_endpoint_address
        },
        {
          name  = "REDIS_PORT"
          value = tostring(aws_elasticache_replication_group.redis.port)
        },
        {
          name  = "AUDIT_LOGGING_ENABLED"
          value = "true"
        }
      ]
      
      # Secrets from AWS Secrets Manager
      secrets = [
        {
          name      = "POSTGRES_USER"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:POSTGRES_USER::"
        },
        {
          name      = "POSTGRES_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:POSTGRES_PASSWORD::"
        },
        {
          name      = "API_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:API_KEY::"
        },
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:JWT_SECRET_KEY::"
        },
        {
          name      = "PHI_ENCRYPTION_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:PHI_ENCRYPTION_KEY::"
        },
        {
          name      = "ANTHROPIC_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.app_secrets.arn}:ANTHROPIC_API_KEY::"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app_logs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.api_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  # Ephemeral storage configuration
  ephemeral_storage {
    size_in_gib = 25
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-task"
    Compliance = "HIPAA"
  }
}

# ECS Service
resource "aws_ecs_service" "app_service" {
  name                              = "${var.project_name}-${var.environment}-service"
  cluster                           = aws_ecs_cluster.app_cluster.id
  task_definition                   = aws_ecs_task_definition.app_task.arn
  desired_count                     = var.ecs_service_desired_count
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  health_check_grace_period_seconds = 120
  propagate_tags                    = "SERVICE"
  enable_execute_command            = var.environment != "production"
  
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.api_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app_tg.arn
    container_name   = "app"
    container_port   = var.api_port
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-service"
    Compliance = "HIPAA"
  }
  
  depends_on = [aws_lb_listener.https]
}

# Auto Scaling for ECS
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = var.environment == "production" ? 10 : 4
  min_capacity       = var.environment == "production" ? 2 : 1
  resource_id        = "service/${aws_ecs_cluster.app_cluster.name}/${aws_ecs_service.app_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Auto Scaling Policy - CPU
resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  name               = "${var.project_name}-${var.environment}-cpu-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Auto Scaling Policy - Memory
resource "aws_appautoscaling_policy" "ecs_memory_policy" {
  name               = "${var.project_name}-${var.environment}-memory-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 80.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
