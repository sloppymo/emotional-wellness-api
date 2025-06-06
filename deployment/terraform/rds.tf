# RDS PostgreSQL database for HIPAA-compliant data storage
resource "aws_db_subnet_group" "db_subnet_group" {
  name        = "${var.project_name}-${var.environment}-db-subnet-group"
  description = "Database subnet group for ${var.project_name}"
  subnet_ids  = module.vpc.private_subnets

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
    Compliance = "HIPAA"
  }
}

resource "aws_db_parameter_group" "db_parameter_group" {
  name        = "${var.project_name}-${var.environment}-db-params"
  family      = "postgres15"
  description = "Parameter group for ${var.project_name} PostgreSQL database"

  # HIPAA compliance parameters
  parameter {
    name  = "log_statement"
    value = "ddl"  # Log all DDL statements (CREATE, ALTER, DROP)
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log statements taking more than 1 second
  }

  parameter {
    name  = "log_connections"
    value = "1"  # Log successful connections
  }

  parameter {
    name  = "log_disconnections"
    value = "1"  # Log session terminations
  }

  parameter {
    name  = "log_lock_waits"
    value = "1"  # Log lock wait events
  }

  parameter {
    name  = "pgaudit.log"
    value = "ddl,write,role,misc_set"  # Set pgAudit log levels
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-db-params"
    Compliance = "HIPAA"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                  = "${var.project_name}-${var.environment}"
  engine                      = "postgres"
  engine_version              = "15.4"
  instance_class              = var.db_instance_class
  allocated_storage           = var.db_allocated_storage
  max_allocated_storage       = var.db_max_allocated_storage
  storage_type                = "gp3"
  storage_encrypted           = true
  kms_key_id                  = aws_kms_key.db_key.arn
  db_name                     = var.db_name
  username                    = var.db_username
  password                    = var.db_password
  db_subnet_group_name        = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids      = [aws_security_group.db_sg.id]
  parameter_group_name        = aws_db_parameter_group.db_parameter_group.name
  backup_retention_period     = var.environment == "production" ? 35 : 7
  backup_window               = "03:00-04:00"
  maintenance_window          = "sun:04:00-sun:05:00"
  multi_az                    = var.environment == "production"
  publicly_accessible         = false
  skip_final_snapshot         = var.environment != "production"
  final_snapshot_identifier   = var.environment == "production" ? "${var.project_name}-${var.environment}-final" : null
  deletion_protection         = var.environment == "production"
  auto_minor_version_upgrade  = true
  copy_tags_to_snapshot       = true
  delete_automated_backups    = var.environment != "production"
  performance_insights_enabled = true
  performance_insights_kms_key_id = aws_kms_key.db_key.arn
  performance_insights_retention_period = var.environment == "production" ? 731 : 7
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval         = 60
  monitoring_role_arn         = aws_iam_role.rds_monitoring_role.arn

  tags = {
    Name = "${var.project_name}-${var.environment}-postgres"
    Compliance = "HIPAA"
  }

  lifecycle {
    prevent_destroy = var.environment == "production"
  }
}

# IAM role for RDS enhanced monitoring
resource "aws_iam_role" "rds_monitoring_role" {
  name = "${var.project_name}-${var.environment}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-rds-monitoring-role"
    Compliance = "HIPAA"
  }
}

# CloudWatch alarm for high database connections
resource "aws_cloudwatch_metric_alarm" "db_connections_high" {
  alarm_name          = "${var.project_name}-${var.environment}-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 100  # Adjust based on your instance size
  alarm_description   = "Database connection count is high"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-db-connections-high"
    Compliance = "HIPAA"
  }
}

# CloudWatch alarm for low storage space
resource "aws_cloudwatch_metric_alarm" "db_low_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-db-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120  # 5 GB in bytes
  alarm_description   = "Database has less than 5GB of storage space left"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-db-low-storage"
    Compliance = "HIPAA"
  }
}

# SNS topic for alarms
resource "aws_sns_topic" "alarms" {
  name              = "${var.project_name}-${var.environment}-alarms"
  kms_master_key_id = aws_kms_key.logs_key.id
  
  tags = {
    Name = "${var.project_name}-${var.environment}-alarms"
    Compliance = "HIPAA"
  }
}
