# IAM bootstrap

This small Terraform project creates the resources needed by `../app`:

- `tcf-terraform-deployer` in the application account
- An encrypted, versioned S3 state bucket in the application account
- A GitHub Actions OIDC provider in the application account

`tcf-terraform-dns` in account `011713309463` is not managed here. It is
maintained by hand in that account and referenced by ARN through the
`dns_role_arn` variable, so bootstrap needs credentials only for the
application account.

Bootstrap uses local state on its first run because it creates the state
bucket. The application stack uses that bucket remotely after bootstrap
completes.

## Setup

Create a local `terraform.tfvars` (do not commit it):

```hcl
app_profile             = "tcf-prod-admin"
deployer_principal_arn  = "arn:aws:iam::099933383052:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_2ac484676f62b043"
application_role_prefix = "iac-test-"
```

`deployer_principal_arn` can also be an existing administrator or CI role.
The principal must be able to assume the application-account deployer role.
GitHub Actions uses OIDC separately; it does not need AWS access keys.

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

The application role receives `PowerUserAccess` plus the IAM permissions
needed by the application stack, including permission to assume the
hand-maintained DNS role.

For production, replace the broad PowerUser attachment with a reviewed
least-privilege policy.

## Manual test-infrastructure apply in GitHub Actions

The workflow at `.github/workflows/terraform-apply.yml` runs a Terraform plan
on every push to `dev`. To apply, a repository admin starts **Actions → Plan
test infrastructure (manual apply) → Run workflow** from `dev`. That manual
run makes a fresh plan and applies the saved plan. Both runs use the existing
S3 state, test domain, and `test` image tag. Neither builds or deploys an
application image.

Before the first workflow run:

1. Use an administrator profile in account `099933383052` to apply the OIDC
   provider and deployer-role trust change in `iac/bootstrap`. Use the
   **existing bootstrap state**: it is local and ignored by Git, and is not
   present in this checkout. Retrieve it from the machine where bootstrap was
   last applied, or import the existing resources into a new state. Before
   applying, confirm `terraform state list` contains the existing deployer
   role, DNS role, and state bucket. The plan should only add the GitHub OIDC
   provider and update the deployer role's trust policy. If it proposes
   recreating existing resources, stop and recover the state first.
2. In GitHub, verify the `terraform-test` environment under **Settings →
   Environments**. It has already been created with deployment restricted to
   `dev`. Leave it without required reviewers so plans can run on every push;
   the apply path separately checks that the person who started it has
   repository `admin` permission.
3. Merge the workflow and bootstrap change into the default `dev` branch.
   The manual **Run workflow** button appears only when the workflow exists on
   the default branch.

The workflow requests a GitHub OIDC token and assumes `tcf-terraform-deployer`
in account `099933383052`. Its trust policy requires audience
`sts.amazonaws.com` and subject
`repo:thecourseforum/theCourseForum2:environment:terraform-test`. The deployer
role then assumes `tcf-terraform-dns` in account `011713309463` for Route 53.
The repository's existing AWS access-key secrets remain for the older workflow
targeting the other account; this test-infrastructure workflow does not use
them. Protect the `dev` branch and the environment because they control which
workflow code can request the OIDC token.
