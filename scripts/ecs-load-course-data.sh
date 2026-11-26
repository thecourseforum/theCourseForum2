#!/usr/bin/env bash
# One-off Fargate task that downloads a semester CSV from public
# thecourseforum/tCF-data and loads it into the prod DB.
#
# Separate from ecs-run-command.sh. Runs the Terraform-managed task family
# tcf-prod-load-course-data (fixed fetch_data + load_semester command). Does
# not register task definitions. Network matches the live web service.
#
# Needs python3 + aws CLIv2 (authenticate with 'aws configure' or OIDC).
#
# Usage:
#   ./scripts/ecs-load-course-data.sh
#   ./scripts/ecs-load-course-data.sh 2026_fall
#
# With no argument, the task uses the same "today" semester as fetch_data.
# Refuses ALL_DANGEROUS and FIX_LAST_TAUGHT_SEMESTERS.
#
# Env: AWS_REGION, ECS_CLUSTER, ECS_SERVICE, ECS_CONTAINER_NAME,
#      ECS_LOAD_TASK_FAMILY, ECS_LOG_GROUP, ECS_LOG_STREAM_PREFIX

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_REGION="$REGION"
CLUSTER="${ECS_CLUSTER:-tcf-prod-cluster}"
SERVICE="${ECS_SERVICE:-tcf-prod-django-service}"
CONTAINER="${ECS_CONTAINER_NAME:-django-app}"
FAMILY="${ECS_LOAD_TASK_FAMILY:-tcf-prod-load-course-data}"
LOG_GROUP="${ECS_LOG_GROUP:-/ecs/tcf-prod-django}"
STREAM_PREFIX="${ECS_LOG_STREAM_PREFIX:-django}"

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [year_season]" >&2
  exit 1
fi

SEMESTER="${1:-}"
if [[ -n "$SEMESTER" ]]; then
  if [[ "$SEMESTER" == "ALL_DANGEROUS" || "$SEMESTER" == "FIX_LAST_TAUGHT_SEMESTERS" ]]; then
    echo "refusing $SEMESTER" >&2
    exit 1
  fi
  if [[ ! "$SEMESTER" =~ ^[0-9]{4}_[A-Za-z]+$ ]]; then
    echo "usage: $0 [year_season]" >&2
    echo "semester must look like 2026_fall" >&2
    exit 1
  fi
fi

describe_json="$(aws ecs describe-services \
  --cluster "$CLUSTER" --services "$SERVICE" --region "$REGION" \
  --query 'services[0].{networkConfiguration:networkConfiguration,platformVersion:platformVersion}' \
  --output json)"

tmp_run="$(mktemp)"
TAIL_PID=""
task_arn=""
cleanup() {
  [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
  if [[ -n "$task_arn" ]]; then
    status="$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task_arn" --region "$REGION" \
      --query 'tasks[0].lastStatus' --output text 2>/dev/null | tr -d '\r\n' || true)"
    if [[ -n "$status" && "$status" != "None" && "$status" != "STOPPED" ]]; then
      aws ecs stop-task --cluster "$CLUSTER" --task "$task_arn" --region "$REGION" \
        --reason "ecs-load-course-data script cleanup" >/dev/null 2>&1 || true
    fi
  fi
  rm -f "$tmp_run"
}
trap cleanup EXIT

running="$(aws ecs list-tasks --cluster "$CLUSTER" --family "$FAMILY" \
  --desired-status RUNNING --region "$REGION" \
  --query 'taskArns' --output text | tr -d '\r\n')"
if [[ -n "$running" && "$running" != "None" ]]; then
  echo "load task already running in family ${FAMILY}: ${running}" >&2
  exit 1
fi

run_task_json="$(
  ECS_CLUSTER="$CLUSTER" ECS_CONTAINER_NAME="$CONTAINER" \
  ECS_LOAD_TASK_FAMILY="$FAMILY" COURSE_DATA_SEMESTER="$SEMESTER" \
  python3 - "$describe_json" <<'PY'
import json, os, sys

info = json.loads(sys.argv[1])
if not info.get("networkConfiguration"):
    sys.exit("describe-services: missing networkConfiguration")

override = {"name": os.environ["ECS_CONTAINER_NAME"]}
semester = os.environ.get("COURSE_DATA_SEMESTER", "")
if semester:
    override["environment"] = [{"name": "COURSE_DATA_SEMESTER", "value": semester}]

body = {
    "cluster": os.environ["ECS_CLUSTER"],
    "taskDefinition": os.environ["ECS_LOAD_TASK_FAMILY"],
    "launchType": "FARGATE",
    "networkConfiguration": info["networkConfiguration"],
    "overrides": {"containerOverrides": [override]},
}
if info.get("platformVersion"):
    body["platformVersion"] = info["platformVersion"]
print(json.dumps(body))
PY
)"

printf '%s\n' "$run_task_json" >"$tmp_run"

task_arn="$(aws ecs run-task --region "$REGION" --cli-input-json "file://${tmp_run}" \
  --query 'tasks[0].taskArn' --output text)"
task_arn="$(printf '%s' "$task_arn" | tr -d '\r\n')"
[[ -n "$task_arn" && "$task_arn" != "None" ]] || {
  echo "run-task did not return a task ARN" >&2
  exit 1
}

task_id="${task_arn##*/}"
log_stream="${STREAM_PREFIX}/${CONTAINER}/${task_id}"

echo "$task_arn" >&2
echo "Tailing ${LOG_GROUP}/${log_stream}..." >&2

n=0
while ((++n <= 180)); do
  if aws logs get-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "$log_stream" \
    --limit 1 \
    --region "$REGION" \
    --output json >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ((n > 180)); then
  echo "Log stream did not appear within ~6m; giving up on tail." >&2
else
  aws logs tail "$LOG_GROUP" --log-stream-names "$log_stream" --region "$REGION" \
    --format short --since 30m --follow &
  TAIL_PID=$!
fi

while true; do
  status="$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task_arn" --region "$REGION" \
    --query 'tasks[0].lastStatus' --output text | tr -d '\r\n')"
  [[ "$status" == STOPPED ]] && break
  sleep 2
done

sleep 2
[[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
wait "$TAIL_PID" 2>/dev/null || true
TAIL_PID=""

exit_code="$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$task_arn" --region "$REGION" \
  --query 'tasks[0].containers[0].exitCode' --output text | tr -d '\r\n')"
if [[ -z "$exit_code" || "$exit_code" == "None" || "$exit_code" == "null" ]]; then
  echo "container exit code missing" >&2
  exit 1
fi
exit "$exit_code"
