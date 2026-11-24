# Application stack

Terraform for everything that runs theCourseForum in the application account
(`099933383052`). The IAM roles, state bucket and GitHub OIDC trust it relies on
are created by [`../bootstrap`](../bootstrap/README.md).

State lives at `s3://tcf-terraform-state-099933383052/app/terraform.tfstate`.

## What is here

| File | Manages |
| --- | --- |
| `networking.tf`, `security-groups.tf` | VPC, subnets in `us-east-1c` and `us-east-1f`, security groups |
| `alb.tf`, `acm.tf`, `route53.tf` | Load balancer, certificates, DNS records in the Route 53 account |
| `cloudfront.tf`, `waf.tf` | CloudFront in front of the ALB and the static bucket, and the WAF web ACL |
| `ecs.tf`, `ecr.tf`, `iam.tf` | ECS cluster, Django task definition and service with autoscaling, image repository, task roles |
| `rds.tf`, `elasticache.tf` | PostgreSQL and Valkey |
| `s3.tf` | Static files bucket |
| `cognito.tf`, `lambda.tf`, `ses.tf` | Cognito user pool, the pre-sign-up Lambda that requires a Virginia email, SES identity and DNS records |
| `secrets.tf` | Secrets Manager entries under `tcf-prod/*` |
| `canary.tf`, `cloudwatch.tf`, `monitoring.tf`, `logging.tf` | Heartbeat canary, log groups, alarms and dashboard, the logs bucket |
| `db-dump.tf` | Nightly database dump task, its schedule and bucket |
| `settings.tf` | The normal and enrollment setting profiles |

## Deploying

Do not apply by hand. Every push to `dev` runs `.github/workflows/deploy.yml`:

1. CI runs and builds the production image once.
2. `.github/workflows/terraform-plan.yml` saves a plan, shown in the run summary.
3. After approval in the `terraform-prod` environment, the apply job pushes the
   tested image, applies the saved plan, uploads static files, runs the release
   task (`migrate`, `clearsessions`) and rolls the ECS service.

Pull requests that touch `iac/` get a read-only plan from
`.github/workflows/terraform-pr-plan.yml` after a reviewer approves the
`terraform-pr-plan` environment. The roles and environments behind this are
described in the bootstrap README.

### Image tag

`ecr_image_tag` is the last commit that changes anything outside `iac/` and
`.github/`, not the pushed commit. Infrastructure-only and workflow-only pushes
therefore keep the running image and do not replace the task definition. A push
that touches root files such as `renovate.json` counts as an application change
and rolls out a new image.

### Static files

Static files are not in the runtime image. The image only carries
`staticfiles.json`, the manifest that maps names to hashed file names. The
apply job builds the `static-files` Docker stage, checks that its manifest
matches the image's, and syncs the files to the static bucket behind CloudFront.

The sync does not use `--delete`, so files from older deploys stay in the
bucket. Hashed names change with content, so old and new versions never
collide, and pages rendered by the previous task keep working during a rollout.

## Settings

`enrollment_mode` (set in `terraform-plan.yml`) picks one of two profiles in
`settings.tf`:

| Setting | normal | enrollment |
| --- | --- | --- |
| `waf_mode` | `off` | `targeted` |
| `waf_logs_enabled` | `false` | `true` |
| `cloudfront_logs_enabled` | `false` | `true` |
| `alb_access_logs_enabled` | `false` | `true` |
| `rds_logs_enabled` | `false` | `true` |
| `vpc_flow_logs_enabled` | `false` | `false` |
| `container_insights` | `enabled` | `enhanced` |
| `database_insights_mode` | `standard` | `advanced` |
| `canary_enabled` | `false` | `true` |

Each setting also has its own variable. Left `null`, it follows the profile;
set, it wins over the profile.

## Quirks

- **Turning the WAF off takes about 10 minutes longer than other applies.**
  With `waf_mode = "off"` the web ACL is deleted, since AWS bills $5 a month
  for one even with no rules. Deleting it in the same apply that detaches it
  from CloudFront fails with `WAFAssociatedItemException` while the detach
  propagates, so CloudFront reads the ACL ARN through `time_sleep.waf_detach`.
  Terraform then detaches CloudFront, waits 5 minutes, and deletes the ACL,
  which the AWS provider also retries for up to 5 minutes. If the delete still
  fails, rerun the deploy: CloudFront is already detached, so the second apply
  only deletes the ACL. Turning the WAF on is a normal single apply.
- **`dns_role_arn` is ephemeral.** It is never stored in state or in a saved
  plan, so pass it again when applying a saved plan. Plans use the read-only
  DNS role and applies use the writable one.
- **Terraform version.** `.terraform-version` pins the CLI for CI and for
  tools like tenv and tfenv. Renovate opens a PR when a new version is out, and
  provider updates come as a separate PR. Neither automerges; merge them after
  reading the PR plan.
- **Hosted zone IDs are hardcoded** in `locals.tf`, because the zones live in
  the DNS account (`011713309463`) and are managed in `thecourseforum/infra`.
- **`domain_name` defaults to `thecourseforumtest.com`.** CI sets
  `thecourseforum.com`, so any run without it targets the wrong domain.
