# IAM bootstrap

This small Terraform project creates the resources needed by `../app`:

- `tcf-terraform-deployer` in the application account, for local and GitHub Actions Terraform applies
- `tcf-github-deployer` in the application account, for GitHub Actions code deploys
- `iac-test-role-boundary`, the permissions boundary every application role must carry
- A KMS-encrypted, versioned S3 state bucket in the application account, which also holds saved plans
- A GitHub Actions OIDC provider in the application account

`tcf-terraform-dns` in account `011713309463` is not managed here. It is
maintained by hand in that account and referenced by ARN through the
`dns_role_arn` variable, so bootstrap needs credentials only for the
application account.

Bootstrap used local state on its first run because it creates the state
bucket. Now that the bucket exists, bootstrap keeps its state there too, under
`bootstrap/terraform.tfstate`. Export `AWS_PROFILE` for an administrator in the
application account before running it, since the backend takes no profile of
its own.

## Setup

Create a local `terraform.tfvars` (do not commit it):

```hcl
app_profile             = "tcf-prod-admin"
deployer_principal_arn  = "arn:aws:iam::099933383052:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_2ac484676f62b043"
application_role_prefix = "iac-test-"
```

`deployer_principal_arn` can also be an existing administrator or CI role.
The principal must be able to assume the application-account deployer role.
GitHub Actions also assumes this role through OIDC from the `terraform-plan`
and `terraform-test` environments, and needs no AWS access keys.

Log in to the SSO profile and verify the account:

```bash
aws sso login --profile tcf-prod-admin
aws sts get-caller-identity --profile tcf-prod-admin
```

Then run bootstrap. It uses local state on this first run:

```bash
NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#terraform -- \
  -chdir=iac/bootstrap init

NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#terraform -- \
  -chdir=iac/bootstrap plan

NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#terraform -- \
  -chdir=iac/bootstrap apply
```

The state bucket created by bootstrap is:

```text
tcf-terraform-state-099933383052
```

The application stack uses that bucket at:

```text
s3://tcf-terraform-state-099933383052/app/terraform.tfstate
```

State and saved plans hold secrets in plaintext, so the bucket:

- encrypts objects by default with the `alias/tcf-terraform-state` KMS key,
  using S3 Bucket Keys to keep KMS requests low
- denies any request that does not use TLS
- expires old versions of `app/` state after 30 days
- expires saved plans under `plans/` after a day

The backends leave encryption to the bucket default. Setting `encrypt = true`
without a KMS key would make Terraform write state with SSE-S3 instead.

Pass the bootstrap output to the application stack:

```bash
NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#terraform -- \
  -chdir=iac/app apply \
  -var='domain_name=thecourseforumtest.com' \
  -var='dns_role_arn=<dns_role_arn-output>'
```

`tcf-terraform-deployer` receives `PowerUserAccess` plus the IAM permissions
needed by the application stack, including permission to assume the
hand-maintained DNS role. It can create and change only `iac-test-*` roles,
and only when they carry the `iac-test-role-boundary` permissions boundary, so
a role it creates can never exceed what the application needs. It can pass
those roles only to ECS tasks and Lambda, and cannot remove a role's boundary.

`tcf-github-deployer` is scoped to deploying application code only:

- push and look up images in `iac-test-*` ECR repositories
- describe and register ECS task definitions in `aws_region`
- run `iac-test-*` task definitions on `iac-test-cluster` and read those tasks
- describe and update `iac-test-*` services on `iac-test-cluster`
- pass `iac-test-*` roles only to ECS tasks

It cannot read Terraform state, change infrastructure, or assume the DNS role.

The trust policy of `tcf-terraform-dns` in account `011713309463` must allow
`arn:aws:iam::099933383052:role/tcf-terraform-deployer` to call
`sts:AssumeRole`. That account is maintained by hand, so update it there.

## Test-infrastructure deploys in GitHub Actions

The workflow at `.github/workflows/terraform-deploy.yml` runs on every push to
`iac`, in two jobs. The `plan` job plans `iac/app`, writes the plan to
the run summary, and stores it under `plans/<run_id>/` in the state bucket
along with the Lambda zip that `archive_file` builds during the plan. The plan
is never uploaded as a GitHub artifact, because it contains every secret in
state and artifacts on a public repository are readable by anyone. The `apply`
job waits for approval, applies that saved plan, then deletes it. Reviewers therefore read the real plan
before approving, and the applied plan is the one they read. Both jobs use the
existing S3 state, the test domain, and the `test` image tag, and neither
builds or deploys an application image.

Two GitHub environments back this, under **Settings → Environments**:

- `terraform-plan` — no required reviewers, so plans run unattended.
- `terraform-test` — required reviewers, which is what pauses the apply.

Both restrict deployments to the `dev` and `iac` branches. That restriction is
what stops other branches from obtaining an OIDC token for the deployer role,
and the Terraform deployer's trust policy accepts both environment names.

Approval gating lives in the environment rather than in the workflow file, so
it applies to pushes on any branch and cannot be removed by editing the
workflow. The `workflow_dispatch` path additionally checks that the person who
started the run has repository `admin` permission; that button appears only
once the workflow exists on the default branch.

The workflow requests a GitHub OIDC token and assumes
`tcf-terraform-deployer` in account `099933383052`. Its OIDC trust statement
requires audience `sts.amazonaws.com` and subject
`repo:thecourseforum/theCourseForum2:environment:terraform-plan` or
`repo:thecourseforum/theCourseForum2:environment:terraform-test`. The role
then assumes `tcf-terraform-dns` in account `011713309463` for Route 53.
Protect the `dev` branch and the environment because they control which
workflow code can request the OIDC token.

## Code deploys in GitHub Actions

The workflow at `.github/workflows/aws.yml` runs on every push to `master` or
`iac`. Its `ci` job runs `.github/workflows/ci.yml` against the pushed commit.
Once CI passes, the `deploy` job waits for approval, then builds the
application image, pushes it to `iac-test-app`, runs the release task, and
updates `iac-test-django-service`.

The `deploy` job runs in the `prod` environment, which requires a reviewer and
allows deployments only from `master` and `iac`. It assumes
`tcf-github-deployer` through OIDC with subject
`repo:thecourseforum/theCourseForum2:environment:prod`. The role's account ID
comes from the `prod` environment's `AWS_ACCOUNT_ID` variable.
