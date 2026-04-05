#!/usr/bin/env bash
# One-off on prod Fargate (same task def + network as the live ECS service).
#
# Needs python3 + aws CLIv2 (authenticate with 'aws configure').
#
# Env: AWS_REGION, ECS_CLUSTER, ECS_SERVICE, ECS_CONTAINER_NAME, ECS_LOG_STREAM_PREFIX

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
CLUSTER="${ECS_CLUSTER:-tcf-fargate-cluster}"
SERVICE="${ECS_SERVICE:-barrett-fogle-love-v1}"
CONTAINER="${ECS_CONTAINER_NAME:-tcf-container}"
STREAM_PREFIX="${ECS_LOG_STREAM_PREFIX:-tcf-logs}"

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <command> [args...]" >&2
  exit 1
fi

describe_json="$(aws ecs describe-services \
  --cluster "$CLUSTER" --services "$SERVICE" --region "$REGION" \
  --query 'services[0].{taskDefinition:taskDefinition,networkConfiguration:networkConfiguration,platformVersion:platformVersion}' \
  --output json)"

task_def_arn="$(printf '%s' "$describe_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["taskDefinition"])')"

LOG_GROUP="$(aws ecs describe-task-definition --task-definition "$task_def_arn" --region "$REGION" \
  --query "taskDefinition.containerDefinitions[?name=='${CONTAINER}'].logConfiguration.options.\"awslogs-group\" | [0]" \
  --output text | tr -d '\r\n')"
[[ -z "$LOG_GROUP" || "$LOG_GROUP" == "None" ]] && LOG_GROUP="/ecs/tcf-prod-task"


run_task_json="$(
  ECS_CLUSTER="$CLUSTER" ECS_CONTAINER_NAME="$CONTAINER" \
  python3 - "$describe_json" "$@" <<'PY'
import json, os, sys

info = json.loads(sys.argv[1])
for k in ("taskDefinition", "networkConfiguration"):
    if not info.get(k):
        sys.exit(f"describe-services: missing {k}")
body = {
    "cluster": os.environ["ECS_CLUSTER"],
    "taskDefinition": info["taskDefinition"],
    "launchType": "FARGATE",
    "networkConfiguration": info["networkConfiguration"],
    "overrides": {
        "containerOverrides": [
            {"name": os.environ["ECS_CONTAINER_NAME"], "command": sys.argv[2:]}
        ]
    },
}
if info.get("platformVersion"):
    body["platformVersion"] = info["platformVersion"]
print(json.dumps(body))
PY
)"

tmp="$(mktemp)"
TAIL_PID=""
cleanup() {
  [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
  rm -f "$tmp"
}
trap cleanup EXIT

printf '%s\n' "$run_task_json" >"$tmp"

task_arn="$(aws ecs run-task --region "$REGION" --cli-input-json "file://${tmp}" \
  --query 'tasks[0].taskArn' --output text)"
task_arn="$(printf '%s' "$task_arn" | tr -d '\r\n')"
[[ -n "$task_arn" ]] || {
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
