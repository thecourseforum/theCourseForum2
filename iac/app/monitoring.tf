locals {
  gunicorn_threads_per_task = 12

  alb_dims = {
    LoadBalancer = aws_lb.main.arn_suffix
  }
  target_group_dims = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.ecs.arn_suffix
  }
  ecs_service_dims = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.django.name
  }
  rds_dims = {
    DBInstanceIdentifier = aws_db_instance.postgres.identifier
  }
  waf_dims = {
    WebACL = local.waf_acl_name
    Rule   = "ALL"
  }

  regional_alarms = {
    "tcf_5XX_Error" = {
      description = "ALB target (app) 5xx >= 1 in 5 min"
      namespace   = "AWS/ApplicationELB"
      metric      = "HTTPCode_Target_5XX_Count"
      dims        = local.alb_dims
      stat        = "Sum"
      comparison  = "GreaterThanOrEqualToThreshold"
      threshold   = 1
      period      = 300
      evals       = 1
      datapoints  = 1
    }
    "tcf-elb-5xx" = {
      description = "ALB-generated 5xx (502/503/504) >= 10 in 5 min"
      namespace   = "AWS/ApplicationELB"
      metric      = "HTTPCode_ELB_5XX_Count"
      dims        = local.alb_dims
      stat        = "Sum"
      comparison  = "GreaterThanOrEqualToThreshold"
      threshold   = 10
      period      = 300
      evals       = 1
      datapoints  = 1
    }
    "tcf-no-healthy-targets" = {
      description = "ALB target group has 0 healthy tasks (origin down)"
      namespace   = "AWS/ApplicationELB"
      metric      = "HealthyHostCount"
      dims        = local.target_group_dims
      stat        = "Minimum"
      comparison  = "LessThanThreshold"
      threshold   = 1
      period      = 60
      evals       = 2
      datapoints  = 2
      missing     = "breaching"
    }
    "tcf-unhealthy-target" = {
      description = "At least one ECS task failing ALB health checks"
      namespace   = "AWS/ApplicationELB"
      metric      = "UnHealthyHostCount"
      dims        = local.target_group_dims
      stat        = "Maximum"
      comparison  = "GreaterThanOrEqualToThreshold"
      threshold   = 1
      period      = 60
      evals       = 2
      datapoints  = 2
    }
    "tcf-p50-latency-high" = {
      description = "ALB target p50 > 500ms for 5 minutes (site-wide slowness)"
      namespace   = "AWS/ApplicationELB"
      metric      = "TargetResponseTime"
      dims        = local.alb_dims
      stat        = "p50"
      comparison  = "GreaterThanThreshold"
      threshold   = 0.5
      period      = 60
      evals       = 5
      datapoints  = 5
    }
    "tcf-p99-latency-high" = {
      description = "ALB target p99 > 3s in 3 of 5 minutes"
      namespace   = "AWS/ApplicationELB"
      metric      = "TargetResponseTime"
      dims        = local.alb_dims
      stat        = "p99"
      comparison  = "GreaterThanThreshold"
      threshold   = 3
      period      = 60
      evals       = 5
      datapoints  = 3
    }
    "tcf-ecs-cpu-saturated" = {
      description = "ECS service CPU > 85% for 10 min"
      namespace   = "AWS/ECS"
      metric      = "CPUUtilization"
      dims        = local.ecs_service_dims
      stat        = "Average"
      comparison  = "GreaterThanThreshold"
      threshold   = 85
      period      = 60
      evals       = 10
      datapoints  = 10
    }
    "tcf-rds-cpu-high" = {
      description = "RDS CPU > 80% for 10 min"
      namespace   = "AWS/RDS"
      metric      = "CPUUtilization"
      dims        = local.rds_dims
      stat        = "Average"
      comparison  = "GreaterThanThreshold"
      threshold   = 80
      period      = 60
      evals       = 10
      datapoints  = 10
    }
    "tcf-rds-cpu-credits-low" = {
      description = "RDS burstable CPU credit balance < 20 for 15 min (unlimited mode bills surplus credits)"
      namespace   = "AWS/RDS"
      metric      = "CPUCreditBalance"
      dims        = local.rds_dims
      stat        = "Minimum"
      comparison  = "LessThanThreshold"
      threshold   = 20
      period      = 300
      evals       = 3
      datapoints  = 3
    }
    "tcf-rds-storage-low" = {
      description = "RDS free storage < 2 GiB"
      namespace   = "AWS/RDS"
      metric      = "FreeStorageSpace"
      dims        = local.rds_dims
      stat        = "Minimum"
      comparison  = "LessThanThreshold"
      threshold   = 2 * 1024 * 1024 * 1024
      period      = 300
      evals       = 1
      datapoints  = 1
    }
    "tcf-rds-memory-low" = {
      description = "RDS freeable memory < 32 MiB for 15 min"
      namespace   = "AWS/RDS"
      metric      = "FreeableMemory"
      dims        = local.rds_dims
      stat        = "Minimum"
      comparison  = "LessThanThreshold"
      threshold   = 32 * 1024 * 1024
      period      = 300
      evals       = 3
      datapoints  = 3
    }
    "tcf-rds-connections-high" = {
      description = "RDS connections >= 80 for 5 min (db.t3.micro max_connections is roughly 80-110)"
      namespace   = "AWS/RDS"
      metric      = "DatabaseConnections"
      dims        = local.rds_dims
      stat        = "Maximum"
      comparison  = "GreaterThanOrEqualToThreshold"
      threshold   = 80
      period      = 60
      evals       = 5
      datapoints  = 5
    }
    "RDS Utilization Low" = {
      description = "## RDS Activity Low\nLow RDS Utilization suggests nothing is using the database. CHECK SITE STATUS IMMEDIATELY."
      namespace   = "AWS/RDS"
      metric      = "CPUUtilization"
      dims        = local.rds_dims
      stat        = "Average"
      comparison  = "LessThanOrEqualToThreshold"
      threshold   = 1
      period      = 300
      evals       = 3
      datapoints  = 3
      missing     = "missing"
      ok_actions  = false
    }
    "tcf-site-down-external" = {
      description = "Synthetics canary ${aws_synthetics_canary.heartbeat.name} failed 2 runs in a row"
      namespace   = "CloudWatchSynthetics"
      metric      = "SuccessPercent"
      dims        = { CanaryName = aws_synthetics_canary.heartbeat.name }
      stat        = "Average"
      comparison  = "LessThanThreshold"
      threshold   = 100
      period      = 300
      evals       = 2
      datapoints  = 2
      missing     = "missing"
    }
  }

  edge_alarms = {
    "tcf-waf-blocked-spike" = {
      description = "WAF blocked >= 500 requests in 5 min (check for false positives)"
      metric      = "BlockedRequests"
      threshold   = 500
    }
    "tcf-waf-captcha-spike" = {
      description = "WAF served >= 200 CAPTCHAs in 5 min (check for false positives)"
      metric      = "CaptchaRequests"
      threshold   = 200
    }
  }
}

resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"

  tags = {
    Name = "${local.name_prefix}-alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "jackr@thecourseforum.com"
}

resource "aws_cloudwatch_metric_alarm" "regional" {
  for_each = local.regional_alarms

  alarm_name          = each.key
  alarm_description   = each.value.description
  namespace           = each.value.namespace
  metric_name         = each.value.metric
  dimensions          = each.value.dims
  statistic           = startswith(each.value.stat, "p") ? null : each.value.stat
  extended_statistic  = startswith(each.value.stat, "p") ? each.value.stat : null
  comparison_operator = each.value.comparison
  threshold           = each.value.threshold
  period              = each.value.period
  evaluation_periods  = each.value.evals
  datapoints_to_alarm = each.value.datapoints
  treat_missing_data  = lookup(each.value, "missing", "notBreaching")
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = lookup(each.value, "ok_actions", true) ? [aws_sns_topic.alerts.arn] : []
}

resource "aws_cloudwatch_metric_alarm" "edge" {
  provider = aws.us_east_1
  for_each = local.waf_enabled ? local.edge_alarms : {}

  alarm_name          = each.key
  alarm_description   = each.value.description
  namespace           = "AWS/WAFV2"
  metric_name         = each.value.metric
  dimensions          = local.waf_dims
  statistic           = "Sum"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = each.value.threshold
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "cloudfront_5xx_rate" {
  provider = aws.us_east_1

  alarm_name          = "tcf-cloudfront-5xx-rate"
  alarm_description   = "CloudFront 5xx rate > 5% over 5 min (only when >= 50 requests)"
  comparison_operator = "GreaterThanThreshold"
  threshold           = 5
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  metric_query {
    id = "rate"

    metric {
      namespace   = "AWS/CloudFront"
      metric_name = "5xxErrorRate"
      period      = 300
      stat        = "Average"
      dimensions = {
        DistributionId = aws_cloudfront_distribution.main.id
        Region         = "Global"
      }
    }
  }

  metric_query {
    id = "reqs"

    metric {
      namespace   = "AWS/CloudFront"
      metric_name = "Requests"
      period      = 300
      stat        = "Sum"
      dimensions = {
        DistributionId = aws_cloudfront_distribution.main.id
        Region         = "Global"
      }
    }
  }

  metric_query {
    id          = "gated"
    expression  = "IF(reqs >= 50, rate, 0)"
    label       = "5xx rate when >= 50 requests"
    return_data = true
  }
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type       = "text"
        x          = 0
        y          = 0
        width      = 24
        height     = 1
        properties = { markdown = "# 📊 Executive Summary (Current State)\n*At-a-glance health and capacity metrics.*" }
      },
      {
        type   = "metric"
        x      = 0
        y      = 1
        width  = 6
        height = 4
        properties = {
          region  = var.aws_region
          title   = "Current ECS Tasks"
          view    = "timeSeries"
          period  = 60
          stacked = false
          metrics = [
            ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.django.name, { stat = "Maximum", color = "#2ca02c" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 1
        width  = 6
        height = 4
        properties = {
          region  = var.aws_region
          title   = "RDS CPU credit balance"
          view    = "timeSeries"
          period  = 300
          stacked = false
          metrics = [
            ["AWS/RDS", "CPUCreditBalance", "DBInstanceIdentifier", aws_db_instance.postgres.identifier, { stat = "Minimum", color = "#ff7f0e" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 1
        width  = 6
        height = 4
        properties = {
          region  = var.aws_region
          title   = "ALB Traffic / min"
          view    = "singleValue"
          period  = 60
          stat    = "Sum"
          stacked = false
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix, { color = "#1f77b4" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 1
        width  = 6
        height = 4
        properties = {
          region = var.aws_region
          title  = "App Errors 5xx"
          view   = "singleValue"
          period = 60
          stat   = "Sum"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.main.arn_suffix, { color = "#d62728" }],
          ]
        }
      },
      {
        type   = "text"
        x      = 0
        y      = 5
        width  = 24
        height = 1
        properties = {
          markdown = "# Capacity & Saturation\n*Busy threads = total target response time ÷ period. Above capacity means requests are queuing in gunicorn. Capacity assumes ${local.gunicorn_threads_per_task} threads per task (3 workers × 4 threads).*"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 8
        height = 6
        properties = {
          region  = var.aws_region
          title   = "Gunicorn threads: busy vs capacity"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0 } }
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Sum", id = "rt", visible = false }],
            ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.django.name, { stat = "Average", id = "tasks", visible = false }],
            [{ expression = "rt/PERIOD(rt)", label = "Busy threads (avg)", id = "busy", color = "#1f77b4" }],
            [{ expression = "tasks*${local.gunicorn_threads_per_task}", label = "Thread capacity", id = "cap", color = "#d62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 6
        width  = 8
        height = 6
        properties = {
          region  = var.aws_region
          title   = "Thread utilization %"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0 } }
          annotations = {
            horizontal = [
              { value = 70, label = "Getting tight", color = "#ff7f0e" },
              { value = 100, label = "Queuing", color = "#d62728" },
            ]
          }
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Sum", id = "rt", visible = false }],
            ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.django.name, { stat = "Average", id = "tasks", visible = false }],
            [{ expression = "100*(rt/PERIOD(rt))/(tasks*${local.gunicorn_threads_per_task})", label = "Utilization %", id = "util", color = "#ff7f0e" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 6
        width  = 8
        height = 6
        properties = {
          region  = var.aws_region
          title   = "Autoscaling: tasks vs service CPU"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0 }, right = { min = 0, max = 100 } }
          annotations = {
            horizontal = [
              { value = var.ecs_cpu_target, label = "Scale-out target ${var.ecs_cpu_target}%", yAxis = "right", color = "#d62728" },
            ]
          }
          metrics = [
            ["ECS/ContainerInsights", "DesiredTaskCount", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.django.name, { stat = "Maximum", label = "Desired tasks", color = "#9467bd" }],
            [".", "RunningTaskCount", ".", ".", ".", ".", { stat = "Maximum", label = "Running tasks", color = "#2ca02c" }],
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.main.name, "ServiceName", aws_ecs_service.django.name, { stat = "Average", label = "Service CPU % (scaling metric)", yAxis = "right", color = "#1f77b4" }],
          ]
        }
      },
      {
        type       = "text"
        x          = 0
        y          = 12
        width      = 24
        height     = 1
        properties = { markdown = "# Edge & Security (CloudFront + WAF)" }
      },
      {
        type   = "metric"
        x      = 0
        y      = 13
        width  = 6
        height = 6
        properties = {
          region  = "us-east-1"
          title   = "WAF actions (totals)"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0 }, right = { min = 0 } }
          metrics = [
            ["AWS/WAFV2", "AllowedRequests", "WebACL", local.waf_acl_name, "Rule", "ALL", { stat = "Sum", label = "Allowed", color = "#2ca02c", yAxis = "right" }],
            [".", "BlockedRequests", ".", ".", ".", ".", { stat = "Sum", label = "Blocked (all rules)", color = "#d62728" }],
            [".", "CaptchaRequests", ".", ".", ".", ".", { stat = "Sum", label = "CAPTCHA (all rules)", color = "#ff7f0e" }],
            [".", "ChallengeRequests", ".", ".", ".", ".", { stat = "Sum", label = "Challenge (all rules)", color = "#9467bd" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 13
        width  = 6
        height = 6
        properties = {
          region  = "us-east-1"
          title   = "CloudFront requests & error rates"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0 }, right = { min = 0 } }
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", aws_cloudfront_distribution.main.id, "Region", "Global", { stat = "Sum", label = "Requests", color = "#1f77b4" }],
            [".", "4xxErrorRate", ".", ".", ".", ".", { stat = "Average", label = "4xx %", yAxis = "right", color = "#ff7f0e" }],
            [".", "5xxErrorRate", ".", ".", ".", ".", { stat = "Average", label = "5xx %", yAxis = "right", color = "#d62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 13
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ALB-generated errors"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0 } }
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_ELB_502_Count", "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Sum", label = "502 (target closed conn)", color = "#d62728" }],
            [".", "HTTPCode_ELB_504_Count", ".", ".", { stat = "Sum", label = "504 (target timeout)", color = "#8c564b" }],
            [".", "HTTPCode_ELB_4XX_Count", ".", ".", { stat = "Sum", label = "ELB 4xx (460 client gave up, 400 bad req)", color = "#ff7f0e" }],
          ]
        }
      },
      {
        type   = "alarm"
        x      = 18
        y      = 13
        width  = 6
        height = 6
        properties = {
          title  = "Alarms"
          sortBy = "stateUpdatedTimestamp"
          states = []
          alarms = concat(
            [for a in aws_cloudwatch_metric_alarm.regional : a.arn],
            [for a in aws_cloudwatch_metric_alarm.edge : a.arn],
            [aws_cloudwatch_metric_alarm.cloudfront_5xx_rate.arn],
          )
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 19
        width  = 24
        height = 6
        properties = {
          region  = "us-east-1"
          title   = "WAF stops by rule"
          view    = "timeSeries"
          stacked = true
          period  = 60
          yAxis   = { left = { min = 0 } }
          metrics = [
            ["AWS/WAFV2", "CaptchaRequests", "WebACL", local.waf_acl_name, "Rule", "aws-anonymous-ip", { stat = "Sum", label = "CAPTCHA: hosting/VPN IPs (aws-anonymous-ip)", color = "#9467bd" }],
            ["AWS/WAFV2", "CaptchaRequests", "WebACL", local.waf_acl_name, "Rule", "rate-per-session", { stat = "Sum", label = "CAPTCHA: >300/5min per session", color = "#ffbb78" }],
            ["AWS/WAFV2", "CaptchaRequests", "WebACL", local.waf_acl_name, "Rule", "rate-per-ip", { stat = "Sum", label = "CAPTCHA: >300/5min per IP", color = "#e377c2" }],
            ["AWS/WAFV2", "CaptchaRequests", "WebACL", local.waf_acl_name, "Rule", "captcha-ja4-scrapers", { stat = "Sum", label = "CAPTCHA: known scraper JA4", color = "#ff7f0e" }],
            ["AWS/WAFV2", "ChallengeRequests", "WebACL", local.waf_acl_name, "Rule", "challenge-tokenless", { stat = "Sum", label = "Challenge: tokenless page loads", color = "#17becf" }],
            ["AWS/WAFV2", "BlockedRequests", "WebACL", local.waf_acl_name, "Rule", "block-per-session", { stat = "Sum", label = "Block: >1000/5min per session", color = "#d62728" }],
            ["AWS/WAFV2", "BlockedRequests", "WebACL", local.waf_acl_name, "Rule", "block-token-reuse", { stat = "Sum", label = "Block: token reuse (medium/high)", color = "#8c564b" }],
            ["AWS/WAFV2", "BlockedRequests", "WebACL", local.waf_acl_name, "Rule", "aws-sqli", { stat = "Sum", label = "Block: SQL injection (aws-sqli)", color = "#7f7f7f" }],
            ["AWS/WAFV2", "BlockedRequests", "WebACL", local.waf_acl_name, "Rule", "block-sqli-scanner", { stat = "Sum", label = "Block: SQLi scanner", color = "#bcbd22" }],
            ["AWS/WAFV2", "CountedRequests", "WebACL", local.waf_acl_name, "Rule", "fetch-without-xrw", { stat = "Sum", label = "Count only: script fetch() (fetch-without-xrw)", color = "#c7c7c7" }],
          ]
        }
      },
      {
        type       = "text"
        x          = 0
        y          = 25
        width      = 24
        height     = 1
        properties = { markdown = "# 1. Application Load Balancer (User Experience / RED Metrics)" }
      },
      {
        type   = "metric"
        x      = 0
        y      = 26
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ALB - Request Count"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Sum" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 26
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ALB - Response Time"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Average", label = "Average" }],
            ["...", { stat = "p99", label = "p99 (Slowest 1%)", color = "#d62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 26
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ALB - HTTP Errors"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Sum", color = "#d62728", label = "Target 5xx" }],
            [".", "HTTPCode_ELB_5XX_Count", ".", ".", { stat = "Sum", color = "#9467bd", label = "ELB 5xx" }],
            [".", "HTTPCode_Target_4XX_Count", ".", ".", { stat = "Sum", color = "#ff7f0e", label = "Target 4xx" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 26
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ALB - Target Health"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["AWS/ApplicationELB", "UnHealthyHostCount", "TargetGroup", aws_lb_target_group.ecs.arn_suffix, "LoadBalancer", aws_lb.main.arn_suffix, { stat = "Maximum", color = "#d62728" }],
            [".", "HealthyHostCount", ".", ".", ".", ".", { stat = "Maximum", color = "#2ca02c" }],
          ]
        }
      },
      {
        type       = "text"
        x          = 0
        y          = 32
        width      = 24
        height     = 1
        properties = { markdown = "# 2. ECS Fargate Cluster (Compute Health / USE Metrics)" }
      },
      {
        type   = "metric"
        x      = 0
        y      = 33
        width  = 8
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ECS - CPU Utilization"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["ECS/ContainerInsights", "TaskCpuUtilization", "ClusterName", aws_ecs_cluster.main.name, { stat = "Average", color = "#1f77b4" }],
            ["...", { stat = "Maximum", color = "#aec7e8" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 33
        width  = 8
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ECS - Memory Utilization"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["ECS/ContainerInsights", "TaskMemoryUtilization", "ClusterName", aws_ecs_cluster.main.name, { stat = "Average", color = "#2ca02c" }],
            ["...", { stat = "Maximum", color = "#98df8a" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 33
        width  = 8
        height = 6
        properties = {
          region  = var.aws_region
          title   = "ECS - Network I/O"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["ECS/ContainerInsights", "NetworkRxBytes", "ClusterName", aws_ecs_cluster.main.name, { stat = "Sum" }],
            [".", "NetworkTxBytes", ".", ".", { stat = "Sum" }],
          ]
        }
      },
      {
        type       = "text"
        x          = 0
        y          = 39
        width      = 24
        height     = 1
        properties = { markdown = "# 3. RDS PostgreSQL (Database Health)" }
      },
      {
        type   = "metric"
        x      = 0
        y      = 40
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "RDS - CPU Utilization (%) & credits"
          view    = "timeSeries"
          stacked = false
          period  = 60
          yAxis   = { left = { min = 0, max = 100 }, right = { min = 0 } }
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", aws_db_instance.postgres.identifier, { stat = "Average", color = "#1f77b4" }],
            [".", "CPUCreditBalance", ".", ".", { stat = "Minimum", color = "#ff7f0e", yAxis = "right" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 6
        y      = 40
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "RDS - Database Connections (1 per gunicorn thread)"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", aws_db_instance.postgres.identifier, { stat = "Maximum" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 40
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "RDS - Read/Write Latency"
          view    = "timeSeries"
          stacked = false
          period  = 60
          metrics = [
            ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", aws_db_instance.postgres.identifier, { stat = "Average", color = "#2ca02c" }],
            [".", "WriteLatency", ".", ".", { stat = "Average", color = "#d62728" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 40
        width  = 6
        height = 6
        properties = {
          region  = var.aws_region
          title   = "RDS - Free Memory & Storage"
          view    = "timeSeries"
          stacked = false
          period  = 300
          metrics = [
            ["AWS/RDS", "FreeableMemory", "DBInstanceIdentifier", aws_db_instance.postgres.identifier, { stat = "Minimum", color = "#9467bd" }],
            [".", "FreeStorageSpace", ".", ".", { stat = "Minimum", color = "#8c564b", yAxis = "right" }],
          ]
        }
      },
    ]
  })
}
