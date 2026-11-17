resource "aws_wafv2_ip_set" "uva_ranges" {
  provider           = aws.us_east_1
  name               = "uva-ranges"
  description        = "University of Virginia ARIN ranges"
  scope              = "CLOUDFRONT"
  ip_address_version = "IPV4"
  addresses = [
    "128.143.0.0/16",
    "199.111.0.0/16",
    "137.54.0.0/16",
  ]

  tags = {
    Name = "${local.name_prefix}-uva-ranges"
  }
}

resource "aws_cloudwatch_log_group" "waf" {
  provider          = aws.us_east_1
  name              = "aws-waf-logs-tcf"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${local.name_prefix}-waf-logs"
  }
}

resource "random_password" "waf_canary_header" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "waf_canary_header" {
  name_prefix = "${local.name_prefix}/waf-canary-header-"
  description = "x-tcf-canary header value that the WAF allow-canary rule matches to let synthetic canary traffic bypass bot mitigations"

  tags = {
    Name = "${local.name_prefix}-waf-canary-header"
  }
}

resource "aws_secretsmanager_secret_version" "waf_canary_header" {
  secret_id     = aws_secretsmanager_secret.waf_canary_header.id
  secret_string = random_password.waf_canary_header.result
}

resource "aws_wafv2_web_acl" "main" {
  provider = aws.us_east_1
  name     = "tcf-web-acl"
  scope    = "CLOUDFRONT"

  default_action {
    allow {}
  }

  captcha_config {
    immunity_time_property {
      immunity_time = 300
    }
  }

  rule {
    name     = "allow-canary"
    priority = 0

    statement {
      byte_match_statement {
        search_string = aws_secretsmanager_secret_version.waf_canary_header.secret_string
        field_to_match {
          single_header {
            name = "x-tcf-canary"
          }
        }
        text_transformation {
          priority = 0
          type     = "NONE"
        }
        positional_constraint = "EXACTLY"
      }
    }

    action {
      allow {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "allow-canary"
    }
  }

  rule {
    name     = "bot-control"
    priority = 1

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesBotControlRuleSet"
        version     = "Version_7.0"

        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string = "."
                field_to_match {
                  uri_path {}
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "CONTAINS"
              }
            }
          }
        }

        managed_rule_group_configs {
          aws_managed_rules_bot_control_rule_set {
            inspection_level        = "TARGETED"
            enable_machine_learning = true
          }
        }
      }
    }

    override_action {
      count {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "bot-control"
    }
  }

  rule {
    name     = "block-token-reuse"
    priority = 2

    statement {
      or_statement {
        statement {
          label_match_statement {
            scope = "LABEL"
            key   = "awswaf:managed:aws:bot-control:targeted:aggregate:volumetric:session:token_reuse:ip:medium"
          }
        }
        statement {
          label_match_statement {
            scope = "LABEL"
            key   = "awswaf:managed:aws:bot-control:targeted:aggregate:volumetric:session:token_reuse:ip:high"
          }
        }
        statement {
          label_match_statement {
            scope = "LABEL"
            key   = "awswaf:managed:aws:bot-control:targeted:aggregate:volumetric:session:token_reuse:asn:medium"
          }
        }
        statement {
          label_match_statement {
            scope = "LABEL"
            key   = "awswaf:managed:aws:bot-control:targeted:aggregate:volumetric:session:token_reuse:asn:high"
          }
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "block-token-reuse"
    }
  }

  rule {
    name     = "block-sqli-scanner"
    priority = 3

    statement {
      and_statement {
        statement {
          byte_match_statement {
            search_string = "t13d1011h2_61a7ad8aa9b6_"
            field_to_match {
              ja4_fingerprint {
                fallback_behavior = "NO_MATCH"
              }
            }
            text_transformation {
              priority = 0
              type     = "NONE"
            }
            positional_constraint = "STARTS_WITH"
          }
        }
        statement {
          or_statement {
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              byte_match_statement {
                search_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
                field_to_match {
                  single_header {
                    name = "user-agent"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
          }
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "block-sqli-scanner"
    }
  }

  rule {
    name     = "aws-sqli"
    priority = 4

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesSQLiRuleSet"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "aws-sqli"
    }
  }

  rule {
    name     = "aws-anonymous-ip"
    priority = 5

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesAnonymousIpList"

        scope_down_statement {
          and_statement {
            statement {
              not_statement {
                statement {
                  label_match_statement {
                    scope = "LABEL"
                    key   = "awswaf:managed:aws:bot-control:bot:verified"
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = "."
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                    positional_constraint = "CONTAINS"
                  }
                }
              }
            }
          }
        }

        rule_action_override {
          name = "AnonymousIPList"
          action_to_use {
            captcha {}
          }
        }
        rule_action_override {
          name = "HostingProviderIPList"
          action_to_use {
            captcha {}
          }
        }
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "aws-anonymous-ip"
    }
  }

  rule {
    name     = "block-per-session"
    priority = 6

    statement {
      rate_based_statement {
        limit                 = 1000
        evaluation_window_sec = 300
        aggregate_key_type    = "CUSTOM_KEYS"

        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string = "."
                field_to_match {
                  uri_path {}
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "CONTAINS"
              }
            }
          }
        }

        custom_key {
          label_namespace {
            namespace = "awswaf:managed:token:id:"
          }
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "block-per-session"
    }
  }

  rule {
    name     = "rate-per-session"
    priority = 7

    statement {
      rate_based_statement {
        limit                 = 300
        evaluation_window_sec = 300
        aggregate_key_type    = "CUSTOM_KEYS"

        scope_down_statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string = "."
                field_to_match {
                  uri_path {}
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "CONTAINS"
              }
            }
          }
        }

        custom_key {
          label_namespace {
            namespace = "awswaf:managed:token:id:"
          }
        }
      }
    }

    action {
      captcha {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "rate-per-session"
    }
  }

  rule {
    name     = "rate-per-ip"
    priority = 8

    statement {
      rate_based_statement {
        limit                 = 300
        evaluation_window_sec = 300
        aggregate_key_type    = "IP"

        scope_down_statement {
          and_statement {
            statement {
              not_statement {
                statement {
                  byte_match_statement {
                    search_string = "."
                    field_to_match {
                      uri_path {}
                    }
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                    positional_constraint = "CONTAINS"
                  }
                }
              }
            }
            statement {
              not_statement {
                statement {
                  ip_set_reference_statement {
                    arn = aws_wafv2_ip_set.uva_ranges.arn
                  }
                }
              }
            }
          }
        }
      }
    }

    action {
      captcha {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "rate-per-ip"
    }
  }

  rule {
    name     = "fetch-without-xrw"
    priority = 9

    statement {
      and_statement {
        statement {
          byte_match_statement {
            search_string = "cors"
            field_to_match {
              single_header {
                name = "sec-fetch-mode"
              }
            }
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
            positional_constraint = "EXACTLY"
          }
        }
        statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string = "XMLHttpRequest"
                field_to_match {
                  single_header {
                    name = "x-requested-with"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
          }
        }
        statement {
          regex_match_statement {
            regex_string = "^/(course|department|instructor|search|browse|club-category)/"
            field_to_match {
              uri_path {}
            }
            text_transformation {
              priority = 0
              type     = "NONE"
            }
          }
        }
      }
    }

    action {
      count {}
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "fetch-without-xrw"
    }
  }

  rule {
    name     = "challenge-tokenless"
    priority = 10

    statement {
      and_statement {
        statement {
          label_match_statement {
            scope = "LABEL"
            key   = "awswaf:managed:token:absent"
          }
        }
        statement {
          not_statement {
            statement {
              label_match_statement {
                scope = "LABEL"
                key   = "awswaf:managed:aws:bot-control:bot:verified"
              }
            }
          }
        }
        statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string = "."
                field_to_match {
                  uri_path {}
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "CONTAINS"
              }
            }
          }
        }
      }
    }

    action {
      challenge {}
    }

    rule_label {
      name = "tcf:tokenless"
    }

    challenge_config {
      immunity_time_property {
        immunity_time = 3600
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "challenge-tokenless"
    }
  }

  rule {
    name     = "captcha-ja4-scrapers"
    priority = 11

    statement {
      and_statement {
        statement {
          or_statement {
            statement {
              byte_match_statement {
                search_string = "t13d1516h2_8daaf6152771_02713d6af862"
                field_to_match {
                  ja4_fingerprint {
                    fallback_behavior = "NO_MATCH"
                  }
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "EXACTLY"
              }
            }
            statement {
              and_statement {
                statement {
                  byte_match_statement {
                    search_string = "t13d1516h2_8daaf6152771_d8a2da3f94cd"
                    field_to_match {
                      ja4_fingerprint {
                        fallback_behavior = "NO_MATCH"
                      }
                    }
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                    positional_constraint = "EXACTLY"
                  }
                }
                statement {
                  byte_match_statement {
                    search_string = "Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146."
                    field_to_match {
                      single_header {
                        name = "user-agent"
                      }
                    }
                    text_transformation {
                      priority = 0
                      type     = "NONE"
                    }
                    positional_constraint = "CONTAINS"
                  }
                }
              }
            }
          }
        }
        statement {
          not_statement {
            statement {
              byte_match_statement {
                search_string = "."
                field_to_match {
                  uri_path {}
                }
                text_transformation {
                  priority = 0
                  type     = "NONE"
                }
                positional_constraint = "CONTAINS"
              }
            }
          }
        }
        statement {
          not_statement {
            statement {
              label_match_statement {
                scope = "LABEL"
                key   = "awswaf:managed:aws:bot-control:bot:verified"
              }
            }
          }
        }
      }
    }

    action {
      captcha {}
    }

    rule_label {
      name = "tcf:ja4-scraper"
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "captcha-ja4-scrapers"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "tcf-web-acl"
  }

  tags = {
    Name = "${local.name_prefix}-web-acl"
  }
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  provider                = aws.us_east_1
  resource_arn            = aws_wafv2_web_acl.main.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
}
