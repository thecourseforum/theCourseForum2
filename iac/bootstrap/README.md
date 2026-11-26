# IAM bootstrap

This small Terraform project creates the resources needed by `../app`:

- `tcf-terraform-deployer` in the application account, for local and GitHub Actions Terraform applies
- `tcf-terraform-planner` in the application account, for GitHub Actions Terraform plans
- `tcf-github-task-runner` in the application account, for scheduled GitHub Actions jobs that start tasks from existing task definitions
- `tcf-prod-role-boundary`, the permissions boundary every application role must carry
- A KMS-encrypted, versioned S3 state bucket in the application account, which also holds saved plans
- A GitHub Actions OIDC provider in the application account

`tcf-terraform-dns` and `tcf-terraform-dns-readonly` in account `011713309463`
are not managed here. They live in the `dns/` module of `thecourseforum/infra`
and are referenced by ARN through the `dns_role_arn` and
`dns_readonly_role_arn` variables, so bootstrap needs credentials only for the
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

`dns_role_arn` is ephemeral, so Terraform never stores it in a saved plan or
in state. Pass it again when applying a saved plan.

`tcf-terraform-deployer` receives `PowerUserAccess` plus the IAM permissions
needed by the application stack, including permission to assume
`tcf-terraform-dns`. It can create and change only `tcf-prod-*` roles,
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
- assume `tcf-terraform-dns-readonly`, which can only read the Route 53 zones

It is explicitly denied reading objects in the database dump bucket.

`tcf-github-task-runner` is scoped to running one-off tasks on the web cluster,
which `.github/workflows/fetch-enrollment.yml` and
`.github/workflows/load-course-data.yml` use:

- run `tcf-prod-django` (enrollment) and `tcf-prod-load-course-data` (course
  CSV load) task definitions on `tcf-prod-cluster` and read those tasks, so it
  cannot start the database dump task
- describe `tcf-prod-*` services on `tcf-prod-cluster`, to copy their network
  configuration
- list and stop tasks on that cluster so a cancelled load job does not leave a
  Fargate task running
- read log events from `/ecs/tcf-prod-django`, to stream the task's output
  into the job
- pass only the web task's execution and task roles, and only to ECS tasks

It cannot register task definitions, push images, update services, read
Terraform state, change infrastructure, or assume either DNS role. The load
task family is defined in the app Terraform stack. GitHub Actions assumes this
role only from the `ecs-tasks` environment, which allows only `dev` and has no
required reviewer so scheduled jobs run unattended. Manual Load course data
runs require typing `LOAD` as confirmation.

In account `011713309463`, `tcf-terraform-dns` trusts only
`tcf-terraform-deployer` and can change records, while
`tcf-terraform-dns-readonly` trusts only `tcf-terraform-planner` and can only
read them. Both are managed in `thecourseforum/infra`, so change them there.

## Deploys in GitHub Actions

The workflow at `.github/workflows/deploy.yml` runs on every push to `dev`,
in three jobs. The `ci` job runs `.github/workflows/ci.yml` against
the pushed commit. Once CI passes, the `plan` job runs
`.github/workflows/terraform-plan.yml`, which plans `iac/app` with
`ecr_image_tag` set to the last commit that changes application code, so the
plan includes the new web task definition. It does not build or push the image. It writes the plan to the run summary and stores it under
`plans/<run_id>/` in the state bucket along with the Lambda zip that
`archive_file` builds during the plan. The plan is never uploaded as a GitHub
artifact, because it contains every secret in state and artifacts on a public
repository are readable by anyone.

The `apply` job waits for approval, pushes the image CI built and tested to
`tcf-prod-app` under that tag, applies the saved plan, then deletes it. It then
uploads static files, runs the release task on the new task definition and
points `tcf-prod-django-service` at it. See [`../app`](../app/README.md) for
the application side of a deploy. Reviewers therefore read the real plan before
approving, the applied plan is the one they read, and one approval covers both
the infrastructure change and the code deploy.

Three GitHub environments back this, under **Settings → Environments**:

- `terraform-plan` — no required reviewers, so plans run unattended.
- `terraform-prod` — required reviewers, which is what pauses the apply.
- `terraform-pr-plan` — required reviewers, with admin bypass off. Pull requests
  that touch `iac/` or the plan and deploy workflows run the same plan through
  `.github/workflows/terraform-pr-plan.yml`, without locking or saving it. The
  planner role can read every secret in state, so a reviewer must read the pull
  request's Terraform and workflow changes before approving the run. Pull
  requests from forks never receive an OIDC token.

`terraform-prod` restricts deployments to the `dev` branch. That restriction
is what stops other branches from obtaining an OIDC token for the deployer
role.

Approval gating lives in the environment rather than in the workflow file, so
it applies to pushes on any branch and cannot be removed by editing the
workflow. The `workflow_dispatch` path additionally checks that the person who
started the run has repository `admin` permission; that button appears only
once the workflow exists on the default branch.

Both jobs request a GitHub OIDC token with audience `sts.amazonaws.com`. The
`plan` job assumes `tcf-terraform-planner`, whose trust statement accepts only
the subjects `repo:thecourseforum/theCourseForum2:environment:terraform-plan`
and `repo:thecourseforum/theCourseForum2:environment:terraform-pr-plan`. The
`apply` job assumes `tcf-terraform-deployer`, whose OIDC trust statement
accepts only `repo:thecourseforum/theCourseForum2:environment:terraform-prod`,
so write credentials are available only after approval. For Route 53 in account
`011713309463`, the `plan` job then assumes `tcf-terraform-dns-readonly` and
the `apply` job assumes `tcf-terraform-dns`. Each job sets its own
`TF_VAR_dns_role_arn`, and because the variable is ephemeral the saved plan
does not carry the read-only role into the apply.
Protect the `dev` branch and the environments because
they control which workflow code can request the OIDC token.

Only `.github/workflows/fetch-enrollment.yml` assumes `tcf-github-task-runner`.
