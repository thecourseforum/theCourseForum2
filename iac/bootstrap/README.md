# IAM bootstrap

This small Terraform project creates the resources needed by `../app`:

- `tcf-terraform-deployer` in the application account, for local applies
- `tcf-github-terraform-deployer` in the application account, for GitHub Actions
- `iac-test-role-boundary`, the permissions boundary every application role must carry
- An encrypted, versioned S3 state bucket in the application account
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
GitHub Actions does not use this role. It assumes
`tcf-github-terraform-deployer` through OIDC and needs no AWS access keys.

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

Pass the bootstrap output to the application stack:

```bash
NIXPKGS_ALLOW_UNFREE=1 nix run --impure nixpkgs#terraform -- \
  -chdir=iac/app apply \
  -var='domain_name=thecourseforumtest.com' \
  -var='dns_role_arn=<dns_role_arn-output>'
```

`tcf-terraform-deployer` receives `PowerUserAccess` plus the IAM permissions
needed by the application stack, including permission to assume the
hand-maintained DNS role.

`tcf-github-terraform-deployer` is scoped to the application stack instead:

- read and write only the `app/` prefix of the state bucket
- the services the stack uses (ACM, CloudFront, Cognito, ECR, ECS, ElastiCache,
  ELB, Lambda, CloudWatch Logs, RDS), limited to `aws_region`
- VPC, subnet, route, and security group changes, but no instances
- only `iac-test/*` secrets and `iac-test-static-*` buckets
- create and change only `iac-test-*` roles, and only when they carry the
  `iac-test-role-boundary` permissions boundary, so a role it creates can never
  exceed what the application needs
- pass those roles only to ECS tasks and Lambda
- assume the DNS role

The trust policy of `tcf-terraform-dns` in account `011713309463` must allow
`arn:aws:iam::099933383052:role/tcf-github-terraform-deployer` to call
`sts:AssumeRole`. That account is maintained by hand, so update it there.

## Test-infrastructure deploys in GitHub Actions

The workflow at `.github/workflows/terraform-deploy.yml` runs on every push to
`iac`, in two jobs. The `plan` job plans `iac/app`, writes the plan to
the run summary, and uploads it as an artifact along with the Lambda zip that
`archive_file` builds during the plan. The `apply` job waits for
approval, then applies that saved plan. Reviewers therefore read the real plan
before approving, and the applied plan is the one they read. Both jobs use the
existing S3 state, the test domain, and the `test` image tag, and neither
builds or deploys an application image.

Two GitHub environments back this, under **Settings → Environments**:

- `terraform-plan` — no required reviewers, so plans run unattended.
- `terraform-test` — required reviewers, which is what pauses the apply.

Both restrict deployments to the `dev` and `iac` branches. That restriction is
what stops other branches from obtaining an OIDC token for the deployer role,
and the GitHub deployer's trust policy accepts both environment names.

Approval gating lives in the environment rather than in the workflow file, so
it applies to pushes on any branch and cannot be removed by editing the
workflow. The `workflow_dispatch` path additionally checks that the person who
started the run has repository `admin` permission; that button appears only
once the workflow exists on the default branch.

The workflow requests a GitHub OIDC token and assumes
`tcf-github-terraform-deployer` in account `099933383052`. Its trust policy
requires audience `sts.amazonaws.com` and subject
`repo:thecourseforum/theCourseForum2:environment:terraform-plan` or
`repo:thecourseforum/theCourseForum2:environment:terraform-test`. The role
then assumes `tcf-terraform-dns` in account `011713309463` for Route 53.
The repository's existing AWS access-key secrets remain for the older workflow
targeting the other account; this test-infrastructure workflow does not use
them. Protect the `dev` branch and the environment because they control which
workflow code can request the OIDC token.
