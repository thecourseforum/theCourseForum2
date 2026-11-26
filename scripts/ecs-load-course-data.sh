#!/usr/bin/env bash
# One-off Fargate task that downloads a semester CSV from public
# thecourseforum/tCF-data and loads it into the prod DB.
#
# Separate from ecs-run-command.sh: registers (or revises) task family
# tcf-prod-load-course-data from the live service's task definition, with a
# fixed fetch_data + load_semester command. Network matches the live service.
#
# Needs python3 + aws CLIv2 (authenticate with 'aws configure').
#
# Usage:
#   ./scripts/ecs-load-course-data.sh
#   ./scripts/ecs-load-course-data.sh 2026_fall
#
# With no argument, the task uses the same "today" semester as fetch_data.
# Refuses ALL_DANGEROUS and FIX_LAST_TAUGHT_SEMESTERS.
#
# Env: AWS_REGION, ECS_CLUSTER, ECS_SERVICE, ECS_CONTAINER_NAME,
#      ECS_LOAD_TASK_FAMILY, ECS_LOG_STREAM_PREFIX

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_REGION="$REGION"
CLUSTER="${ECS_CLUSTER:-tcf-prod-cluster}"
SERVICE="${ECS_SERVICE:-tcf-prod-django-service}"
CONTAINER="${ECS_CONTAINER_NAME:-django-app}"
FAMILY="${ECS_LOAD_TASK_FAMILY:-tcf-prod-load-course-data}"
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
  --query 'services[0].{taskDefinition:taskDefinition,networkConfiguration:networkConfiguration,platformVersion:platformVersion}' \
  --output json)"

source_task_def="$(printf '%s' "$describe_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["taskDefinition"])')"
[[ -n "$source_task_def" && "$source_task_def" != "None" ]] || {
  echo "describe-services: missing taskDefinition" >&2
  exit 1
}

# Fixed entrypoint for this family. SEMESTER is injected as an env override.
LOAD_COMMAND='set -euo pipefail
if [ -n "${COURSE_DATA_SEMESTER:-}" ]; then
  python manage.py fetch_data "$COURSE_DATA_SEMESTER"
  python manage.py load_semester "$COURSE_DATA_SEMESTER"
else
  python manage.py fetch_data
  shopt -s nullglob
  csv=(fetched/*.csv)
  if [[ ${#csv[@]} -ne 1 ]]; then
    echo "expected exactly one csv in fetched/, got ${#csv[@]}" >&2
    exit 1
  fi
  python manage.py load_semester "$(basename "${csv[0]}" .csv)"
fi
'

# Clone the live task def into family tcf-prod-load-course-data with the load command.
register_json="$(
  ECS_LOAD_TASK_FAMILY="$FAMILY" ECS_CONTAINER_NAME="$CONTAINER" \
  python3 - "$source_task_def" "$LOAD_COMMAND" <<'PY'
import json, os, sys, subprocess

source = sys.argv[1]
load_command = sys.argv[2]
family = os.environ["ECS_LOAD_TASK_FAMILY"]
container = os.environ["ECS_CONTAINER_NAME"]

raw = subprocess.check_output(
    [
        "aws", "ecs", "describe-task-definition",
        "--task-definition", source,
        "--region", os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")),
        "--query", "taskDefinition",
        "--output", "json",
    ],
    text=True,
)
td = json.loads(raw)
drop = {
    "taskDefinitionArn", "revision", "status", "requiresAttributes",
    "compatibilities", "registeredAt", "registeredBy", "deregisteredAt",
}
for k in list(td):
    if k in drop:
        del td[k]

td["family"] = family
found = False
for c in td["containerDefinitions"]:
    if c.get("name") == container:
        c["command"] = ["bash", "-c", load_command]
        found = True
        break
if not found:
    sys.exit(f"container {container!r} not in task definition")

print(json.dumps(td))
PY
)"

tmp_reg="$(mktemp)"
tmp_run="$(mktemp)"
TAIL_PID=""
cleanup() {
  [[ -n "$TAIL_PID" ]] && kill "$TAIL_PID" 2>/dev/null || true
  rm -f "$tmp_reg" "$tmp_run"
}
trap cleanup EXIT

printf '%s\n' "$register_json" >"$tmp_reg"
load_task_def_arn="$(aws ecs register-task-definition --region "$REGION" \
  --cli-input-json "file://${tmp_reg}" \
  --query 'taskDefinition.taskDefinitionArn' --output text | tr -d '\r\n')"
[[ -n "$load_task_def_arn" && "$load_task_def_arn" != "None" ]] || {
  echo "register-task-definition failed" >&2
  exit 1
}
echo "task definition $load_task_def_arn" >&2

LOG_GROUP="$(aws ecs describe-task-definition --task-definition "$load_task_def_arn" --region "$REGION" \
  --query "taskDefinition.containerDefinitions[?name=='${CONTAINER}'].logConfiguration.options.\"awslogs-group\" | [0]" \
  --output text | tr -d '\r\n')"
[[ -z "$LOG_GROUP" || "$LOG_GROUP" == "None" ]] && LOG_GROUP="/ecs/tcf-prod-django"

run_task_json="$(
  ECS_CLUSTER="$CLUSTER" ECS_CONTAINER_NAME="$CONTAINER" \
  COURSE_DATA_SEMESTER="$SEMESTER" \
  python3 - "$describe_json" "$load_task_def_arn" <<'PY'
import json, os, sys

info = json.loads(sys.argv[1])
task_def = sys.argv[2]
for k in ("networkConfiguration",):
    if not info.get(k):
        sys.exit(f"describe-services: missing {k}")

override = {"name": os.environ["ECS_CONTAINER_NAME"]}
semester = os.environ.get("COURSE_DATA_SEMESTER", "")
if semester:
    override["environment"] = [{"name": "COURSE_DATA_SEMESTER", "value": semester}]

body = {
    "cluster": os.environ["ECS_CLUSTER"],
    "taskDefinition": task_def,
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
