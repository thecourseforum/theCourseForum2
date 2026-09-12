# IAM bootstrap

This small Terraform project creates the resources needed by `../app`:

- `tcf-terraform-deployer` in the application account
- `tcf-terraform-dns` in account `011713309463`
- An encrypted, versioned S3 state bucket in the application account

It is intended to be run once by an administrator with access to both
accounts. The providers use separate AWS CLI profiles so the DNS role can be
created before the application deployment role begins assuming it.

Bootstrap uses local state on its first run because it creates the state
bucket. The application stack uses that bucket remotely after bootstrap
completes.

## Setup

Create a local `terraform.tfvars` (do not commit it):

```hcl
app_profile             = "tcf-prod-admin"
dns_profile             = "tcf-dns-admin"
deployer_principal_arn  = "arn:aws:iam::099933383052:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_AdministratorAccess_2ac484676f62b043"
application_role_prefix = "iac-test-"
```

`deployer_principal_arn` can also be an existing administrator or CI role.
The principal must be able to assume the application-account deployer role.

Log in to both SSO profiles and verify the accounts:

```bash
aws sso login --profile tcf-prod-admin
aws sso login --profile tcf-dns-admin
aws sts get-caller-identity --profile tcf-prod-admin
aws sts get-caller-identity --profile tcf-dns-admin
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
needed by the application stack. The DNS role receives only the Route 53
permissions required for the two hosted zones.

For production, replace the broad PowerUser attachment with a reviewed
least-privilege policy.
