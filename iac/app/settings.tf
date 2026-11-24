locals {
  setting_profiles = {
    normal = {
      waf_mode                = "off"
      waf_logs_enabled        = false
      cloudfront_logs_enabled = false
      alb_access_logs_enabled = false
      rds_logs_enabled        = false
      vpc_flow_logs_enabled   = false
      container_insights      = "enabled"
      database_insights_mode  = "standard"
      canary_enabled          = false
    }
    enrollment = {
      waf_mode                = "targeted"
      waf_logs_enabled        = true
      cloudfront_logs_enabled = true
      alb_access_logs_enabled = true
      rds_logs_enabled        = true
      vpc_flow_logs_enabled   = false
      container_insights      = "enhanced"
      database_insights_mode  = "advanced"
      canary_enabled          = true
    }
  }

  setting_profile = local.setting_profiles[var.enrollment_mode ? "enrollment" : "normal"]

  waf_mode                = var.waf_mode != null ? var.waf_mode : local.setting_profile.waf_mode
  waf_logs_enabled        = var.waf_logs_enabled != null ? var.waf_logs_enabled : local.setting_profile.waf_logs_enabled
  cloudfront_logs_enabled = var.cloudfront_logs_enabled != null ? var.cloudfront_logs_enabled : local.setting_profile.cloudfront_logs_enabled
  alb_access_logs_enabled = var.alb_access_logs_enabled != null ? var.alb_access_logs_enabled : local.setting_profile.alb_access_logs_enabled
  rds_logs_enabled        = var.rds_logs_enabled != null ? var.rds_logs_enabled : local.setting_profile.rds_logs_enabled
  vpc_flow_logs_enabled   = var.vpc_flow_logs_enabled != null ? var.vpc_flow_logs_enabled : local.setting_profile.vpc_flow_logs_enabled
  container_insights      = var.container_insights != null ? var.container_insights : local.setting_profile.container_insights
  database_insights_mode  = var.database_insights_mode != null ? var.database_insights_mode : local.setting_profile.database_insights_mode
  canary_enabled          = var.canary_enabled != null ? var.canary_enabled : local.setting_profile.canary_enabled
}
