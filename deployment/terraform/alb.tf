# Application Load Balancer with HIPAA-compliant security configuration

# Security Group for ALB
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-${var.environment}-alb-sg"
  description = "Security group for ALB"
  vpc_id      = module.vpc.vpc_id

  # HTTPS inbound from specified IPs or anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = length(var.allowed_ip_ranges) > 0 ? var.allowed_ip_ranges : ["0.0.0.0/0"]
    description = "HTTPS inbound"
  }

  # Allow all outbound traffic to API
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
    Compliance = "HIPAA"
  }
}

# Application Load Balancer
resource "aws_lb" "app_lb" {
  name                       = "${var.project_name}-${var.environment}-alb"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb_sg.id]
  subnets                    = module.vpc.public_subnets
  enable_deletion_protection = var.environment == "production"
  drop_invalid_header_fields = true
  idle_timeout               = 60

  # Access logs with encryption
  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
    Compliance = "HIPAA"
  }
}

# S3 bucket for ALB access logs
resource "aws_s3_bucket" "alb_logs" {
  bucket = "${var.project_name}-${var.environment}-alb-logs-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "${var.project_name}-${var.environment}-alb-logs"
    Compliance = "HIPAA"
  }
}

# S3 bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# S3 bucket ACL for ALB access
resource "aws_s3_bucket_acl" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  acl    = "private"
  depends_on = [aws_s3_bucket_ownership_controls.alb_logs]
}

# S3 bucket policy for ALB access logs
resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${lookup(local.elb_account_ids, var.aws_region, "127311923021")}:root"
        }
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.alb_logs.arn}/alb-logs/AWSLogs/${data.aws_caller_identity.current.account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs.arn
      }
    ]
  })
}

# Server-side encryption for S3 bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.logs_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

# Lifecycle configuration for S3 bucket
resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id      = "log-expiration"
    status  = "Enabled"

    expiration {
      days = var.environment == "production" ? 2190 : 90  # 6 years for production (HIPAA), 90 days for other envs
    }
  }
}

# Block public access for S3 bucket
resource "aws_s3_bucket_public_access_block" "alb_logs" {
  bucket                  = aws_s3_bucket.alb_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# HTTPS listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.cert.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-https-listener"
    Compliance = "HIPAA"
  }
}

# HTTP listener - redirect to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-http-redirect"
    Compliance = "HIPAA"
  }
}

# Target Group
resource "aws_lb_target_group" "app_tg" {
  name                 = "${var.project_name}-${var.environment}-tg"
  port                 = var.api_port
  protocol             = "HTTP"
  vpc_id               = module.vpc.vpc_id
  target_type          = "ip"
  deregistration_delay = 60

  health_check {
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-tg"
    Compliance = "HIPAA"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ACM Certificate placeholder - in real deployment, this would be imported or managed separately
resource "aws_acm_certificate" "cert" {
  domain_name       = "${var.environment}.api.example.com"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cert"
    Compliance = "HIPAA"
  }
}

# WAF WebACL for HIPAA-compliant API protection
resource "aws_wafv2_web_acl" "api_waf" {
  count = var.enable_waf ? 1 : 0
  
  name        = "${var.project_name}-${var.environment}-waf"
  description = "WAF rules for ${var.project_name} API"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 1000
        aggregate_key_type = "IP"
        scope_down_statement {
          byte_match_statement {
            field_to_match {
              uri_path {}
            }
            positional_constraint = "CONTAINS"
            search_string         = "/api/"
            text_transformation {
              priority = 0
              type     = "NONE"
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - SQL injection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesSQLiRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - Core rule set
  rule {
    name     = "AWSManagedRulesCoreRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCoreRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCoreRuleSet"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules - IP Reputation list
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesAmazonIpReputationList"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.project_name}-${var.environment}-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-waf"
    Compliance = "HIPAA"
  }
}

# Associate WAF with ALB
resource "aws_wafv2_web_acl_association" "waf_alb_association" {
  count = var.enable_waf ? 1 : 0
  
  resource_arn = aws_lb.app_lb.arn
  web_acl_arn  = aws_wafv2_web_acl.api_waf[0].arn
}

# CloudWatch metric for blocked requests
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  count = var.enable_waf ? 1 : 0
  
  alarm_name          = "${var.project_name}-${var.environment}-waf-blocked-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "This metric monitors blocked requests by WAF"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  
  dimensions = {
    WebACL = "${var.project_name}-${var.environment}-waf"
    Region = var.aws_region
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-waf-blocked-requests"
    Compliance = "HIPAA"
  }
}

# ELB Account ID mapping for S3 access logging
locals {
  elb_account_ids = {
    "us-east-1"      = "127311923021"
    "us-east-2"      = "033677994240"
    "us-west-1"      = "027434742980"
    "us-west-2"      = "797873946194"
    "af-south-1"     = "098369216593"
    "ca-central-1"   = "985666609251"
    "eu-central-1"   = "054676820928"
    "eu-west-1"      = "156460612806"
    "eu-west-2"      = "652711504416"
    "eu-west-3"      = "009996457667"
    "eu-north-1"     = "897822967062"
    "eu-south-1"     = "635631232127"
    "ap-east-1"      = "754344448648"
    "ap-northeast-1" = "582318560864"
    "ap-northeast-2" = "600734575887"
    "ap-northeast-3" = "383597477331"
    "ap-southeast-1" = "114774131450"
    "ap-southeast-2" = "783225319266"
    "ap-southeast-3" = "589379963580"
    "ap-south-1"     = "718504428378"
    "me-south-1"     = "076674570225"
    "sa-east-1"      = "507241528517"
  }
}
