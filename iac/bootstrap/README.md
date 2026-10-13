# IAM bootstrap

This small Terraform project creates the resources needed by `../app`:

- `tcf-terraform-deployer` in the application account, for local and GitHub Actions Terraform applies
- `tcf-terraform-planner` in the application account, for GitHub Actions Terraform plans
- `tcf-github-deployer` in the application account, for GitHub Actions code deploys
- `tcf-prod-role-boundary`, the permissions boundary every application role must carry
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
application_role_prefix = "tcf-prod-"
```

`deployer_principal_arn` can also be an existing administrator or CI role.
The principal must be able to assume the application-account deployer role.
GitHub Actions also assumes this role through OIDC from the `terraform-prod`
environment, and needs no AWS access keys.

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
hand-maintained DNS role. It can create and change only `tcf-prod-*` roles,
and only when they carry the `tcf-prod-role-boundary` permissions boundary, so
a role it creates can never exceed what the application needs. It can pass
those roles only to ECS tasks, Lambda, and EventBridge Scheduler, and cannot
remove a role's boundary.

`tcf-terraform-planner` is what the unapproved `plan` job runs as, so it
cannot change infrastructure or deploy. It receives `ReadOnlyAccess` plus:

- encrypt and decrypt with the state KMS key
- write and delete the `app/` state lock file, and write saved plans under
  `plans/`
- read `tcf-prod/*` secrets, which plan refreshes and which state already holds
- assume the hand-maintained DNS role

It is explicitly denied reading objects in the database dump bucket.

`tcf-github-deployer` is scoped to deploying application code only:

- push and look up images in `tcf-prod-*` ECR repositories
- describe and register ECS task definitions in `aws_region`
- run `tcf-prod-django` task definitions on `tcf-prod-cluster` and read those
  tasks, so it cannot start the database dump task
- describe and update `tcf-prod-*` services on `tcf-prod-cluster`
- pass only the web task's execution and task roles, and only to ECS tasks

It cannot read Terraform state, change infrastructure, or assume the DNS role.

The trust policy of `tcf-terraform-dns` in account `011713309463` must allow
both `arn:aws:iam::099933383052:role/tcf-terraform-deployer` and
`arn:aws:iam::099933383052:role/tcf-terraform-planner` to call
`sts:AssumeRole`. That account is maintained by hand, so update it there.

## Deploys in GitHub Actions

The workflow at `.github/workflows/deploy.yml` runs on every push to `master`
or `iac`, in three jobs. The `ci` job runs `.github/workflows/ci.yml` against
the pushed commit. Once CI passes, the `plan` job plans `iac/app` with
`ecr_image_tag` set to the commit SHA, so the plan includes the new web task
definition. It does not build or push the image. It writes the plan to the run summary and stores it under
`plans/<run_id>/` in the state bucket along with the Lambda zip that
`archive_file` builds during the plan. The plan is never uploaded as a GitHub
artifact, because it contains every secret in state and artifacts on a public
repository are readable by anyone.

The `apply` job waits for approval, builds the application image and pushes it
to `tcf-prod-app` tagged with the commit SHA, applies the saved plan, then
deletes it. It then runs the release task on the new task definition and points
`tcf-prod-django-service` at it. Reviewers therefore read the real plan before
approving, the applied plan is the one they read, and one approval covers both
the infrastructure change and the code deploy.

Two GitHub environments back this, under **Settings → Environments**:

- `terraform-plan` — no required reviewers, so plans run unattended.
- `terraform-prod` — required reviewers, which is what pauses the apply.

Both restrict deployments to the `master`, `dev` and `iac` branches. That
restriction is what stops other branches from obtaining an OIDC token for
either role.

Approval gating lives in the environment rather than in the workflow file, so
it applies to pushes on any branch and cannot be removed by editing the
workflow. The `workflow_dispatch` path additionally checks that the person who
started the run has repository `admin` permission; that button appears only
once the workflow exists on the default branch.

Both jobs request a GitHub OIDC token with audience `sts.amazonaws.com`. The
`plan` job assumes `tcf-terraform-planner`, whose trust statement accepts only
subject `repo:thecourseforum/theCourseForum2:environment:terraform-plan`. The
`apply` job assumes `tcf-terraform-deployer`, whose OIDC trust statement
accepts only `repo:thecourseforum/theCourseForum2:environment:terraform-prod`,
so write credentials are available only after approval. Both roles then assume
`tcf-terraform-dns` in account `011713309463` for Route 53.
Protect the `master`, `dev` and `iac` branches and the environments because
they control which workflow code can request the OIDC token.

No workflow assumes `tcf-github-deployer` any more.
