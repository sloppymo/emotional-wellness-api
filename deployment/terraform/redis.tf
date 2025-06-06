# ElastiCache Redis for session management and caching
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name        = "${var.project_name}-${var.environment}-redis-subnet-group"
  description = "Redis subnet group for ${var.project_name}"
  subnet_ids  = module.vpc.private_subnets

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-subnet-group"
    Compliance = "HIPAA"
  }
}

resource "aws_elasticache_parameter_group" "redis_parameter_group" {
  name        = "${var.project_name}-${var.environment}-redis-params"
  family      = "redis7"
  description = "Parameter group for ${var.project_name} Redis"

  # HIPAA compliance and security parameters
  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"  # Expire keys by approximate LRU algorithm
  }

  parameter {
    name  = "timeout"
    value = "300"  # Client timeout in seconds
  }

  parameter {
    name  = "notify-keyspace-events"
    value = "KEA"  # Key-space notifications for key expiration events
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-params"
    Compliance = "HIPAA"
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.project_name}-${var.environment}"
  description                = "Redis cluster for ${var.project_name}"
  node_type                  = var.redis_node_type
  num_cache_clusters         = var.environment == "production" ? 2 : 1
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis_parameter_group.name
  subnet_group_name          = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids         = [aws_security_group.redis_sg.id]
  automatic_failover_enabled = var.environment == "production"
  multi_az_enabled           = var.environment == "production"
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  apply_immediately          = var.environment != "production"
  auto_minor_version_upgrade = true
  maintenance_window         = "sun:05:00-sun:06:00"
  snapshot_retention_limit   = var.environment == "production" ? 7 : 1
  snapshot_window            = "00:00-01:00"
  final_snapshot_identifier  = var.environment == "production" ? "${var.project_name}-${var.environment}-redis-final" : null
  
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_logs.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_logs.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "engine-log"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-redis"
    Compliance = "HIPAA"
  }
}

# CloudWatch log group for Redis logs
resource "aws_cloudwatch_log_group" "redis_logs" {
  name              = "/aws/elasticache/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_in_days
  kms_key_id        = aws_kms_key.logs_key.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-redis-logs"
    Compliance = "HIPAA"
  }
}

# CloudWatch alarm for high Redis CPU
resource "aws_cloudwatch_metric_alarm" "redis_cpu_high" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "EngineCPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Redis CPU utilization is high"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-redis-cpu-high"
    Compliance = "HIPAA"
  }
}

# CloudWatch alarm for low Redis memory
resource "aws_cloudwatch_metric_alarm" "redis_memory_low" {
  alarm_name          = "${var.project_name}-${var.environment}-redis-memory-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "FreeableMemory"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 104857600  # 100MB
  alarm_description   = "Redis has less than 100MB of freeable memory"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-redis-memory-low"
    Compliance = "HIPAA"
  }
}
