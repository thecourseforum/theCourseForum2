#!/bin/bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--latest] [filename]" >&2
  echo "  --latest  download the newest existing dump instead of running a new one" >&2
  exit 1
}

latest=false
if [ "${1:-}" = "--latest" ]; then
  latest=true
  shift
fi
[ $# -le 1 ] || usage

filename="${1:-prod.dump}"

if [ ! -d "$(dirname "db/$filename")" ]; then
  echo "Database destination 'db/$filename' invalid."
  echo "Ensure the directory db exists, and provide just the filename."
  exit 1
fi

export AWS_REGION="${AWS_REGION:-us-east-1}"
schedule="${DUMP_SCHEDULE:-tcf-prod-db-dump}"

if ! caller=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null); then
  echo "--- ❌ No AWS credentials found. Log in with administrator access to the production account first."
  exit 1
fi
if [[ "$caller" != arn:aws:sts::*:assumed-role/AWSReservedSSO_AdministratorAccess_*/* ]]; then
  echo "--- ❌ $caller is not an AWS administrator. Production dumps require administrator access."
  exit 1
fi

target=$(aws scheduler get-schedule --name "$schedule" --query Target --output json)
cluster=$(jq -r '.Arn' <<< "$target")
task_definition=$(jq -r '.EcsParameters.TaskDefinitionArn' <<< "$target")
bucket=$(aws ecs describe-task-definition --task-definition "$task_definition" \
  --query "taskDefinition.containerDefinitions[].environment[?name=='DUMP_BUCKET'].value[] | [0]" --output text)

if [ "$latest" = false ]; then
  network=$(jq -c '.EcsParameters.NetworkConfiguration.awsvpcConfiguration
    | {awsvpcConfiguration: {subnets: .Subnets, securityGroups: .SecurityGroups, assignPublicIp: .AssignPublicIp}}' <<< "$target")

  task=$(aws ecs run-task --cluster "$cluster" --task-definition "$task_definition" \
    --launch-type FARGATE --network-configuration "$network" --started-by prod_dump.sh \
    --query 'tasks[0].taskArn' --output text)
  echo "--- Started dump task ${task##*/} from schedule '$schedule'..."

  while [ "$(aws ecs describe-tasks --cluster "$cluster" --tasks "$task" --query 'tasks[0].lastStatus' --output text)" != "STOPPED" ]; do
    sleep 10
  done

  failed=$(aws ecs describe-tasks --cluster "$cluster" --tasks "$task" \
    --query 'tasks[0].containers[?exitCode!=`0`].name' --output text)
  if [ -n "$failed" ]; then
    echo "--- ❌ Dump task failed in: $failed"
    aws ecs describe-tasks --cluster "$cluster" --tasks "$task" \
      --query 'tasks[0].{stoppedReason: stoppedReason, containers: containers[].{name: name, exitCode: exitCode, reason: reason}}'
    exit 1
  fi
fi

key=$(aws s3api list-objects-v2 --bucket "$bucket" --query 'max_by(Contents || `[]`, &LastModified).Key' --output text)
if [ -z "$key" ] || [ "$key" = "None" ]; then
  echo "--- ❌ No dumps found in s3://$bucket"
  exit 1
fi

echo "--- Downloading s3://$bucket/$key..."
aws s3 cp "s3://$bucket/$key" "db/$filename"

echo "--- ✅ Successfully created remote database dump at: db/$filename"
