#!/usr/bin/env bash
# Interactive review moderation tool.
#
# Fetches all reviews for a course/instructor page from production,
# lets you browse them, and hide or unhide individual reviews.
#
# Requires: AWS CLI v2 + session-manager-plugin, authenticated (aws configure)
# Run from the repo root: ./scripts/hide_review.sh
#
# For local dev (docker): set USE_DOCKER=1
#   USE_DOCKER=1 ./scripts/hide_review.sh

set -euo pipefail

REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
CLUSTER="${ECS_CLUSTER:-tcf-fargate-cluster}"
SERVICE="${ECS_SERVICE:-barrett-fogle-love-v1}"
CONTAINER="${ECS_CONTAINER_NAME:-tcf-container}"
USE_DOCKER="${USE_DOCKER:-0}"

TASK_ARN=""
CAPTURED_FILE=""
CAPTURED=""

trap '[[ -n "$CAPTURED_FILE" ]] && rm -f "$CAPTURED_FILE"' EXIT INT TERM

_get_task_arn() {
    aws ecs list-tasks \
        --cluster "$CLUSTER" \
        --service-name "$SERVICE" \
        --desired-status RUNNING \
        --region "$REGION" \
        --query 'taskArns[0]' \
        --output text
}

_ecs_command() {
    # Build the command locally with bash's printf '%q', then base64-encode it
    # so the container's /bin/sh can pass it to bash without any quoting issues
    # (single quotes, double quotes, dollar signs, etc. in argument values are
    # all safely carried through base64).
    local inner_cmd b64
    inner_cmd="python manage.py $(printf '%q ' "$@")"
    b64="$(printf '%s' "$inner_cmd" | base64 | tr -d '\n')"
    aws ecs execute-command \
        --cluster "$CLUSTER" \
        --task "$TASK_ARN" \
        --container "$CONTAINER" \
        --region "$REGION" \
        --interactive \
        --command "bash -c \"\$(echo $b64|base64 -d)\""
}

_run_cmd() {
    if [[ "$USE_DOCKER" == "1" ]]; then
        docker exec -it tcf_django python manage.py "$@"
    else
        _ecs_command "$@"
    fi
}

_run_cmd_capture() {
    [[ -n "$CAPTURED_FILE" ]] && rm -f "$CAPTURED_FILE"
    CAPTURED_FILE="$(mktemp)"
    if [[ "$USE_DOCKER" == "1" ]]; then
        docker exec tcf_django python manage.py "$@" > "$CAPTURED_FILE" 2>&1
    else
        _ecs_command "$@" > "$CAPTURED_FILE" 2>&1 || true
    fi
    CAPTURED="$(cat "$CAPTURED_FILE")"
}

_display_captured() {
    while IFS= read -r line; do
        [[ "$line" == *"REVIEW|"* ]] && continue
        # Filter SSM session manager noise
        [[ "$line" == *"SessionId"* ]] && continue
        [[ "$line" == *"Session Manager plugin"* ]] && continue
        [[ "$line" == "Starting session"* ]] && continue
        [[ "$line" == "Exiting session"* ]] && continue
        echo "$line"
    done <<< "$CAPTURED"
}

_extract_review_lines() {
    grep 'REVIEW|' <<< "$CAPTURED" | sed 's/.*\(REVIEW|.*\)/\1/' || true
}

print_header() {
    echo ""
    echo "================================================"
    echo "  TheCourseForum — Review Moderation Tool"
    echo "================================================"
    echo ""
}

print_review_table() {
    if [[ ${#REVIEW_LINES[@]} -eq 0 ]]; then
        echo "  No reviews found for this page."
        return
    fi
    printf "\n  %-4s %-20s %-28s %-8s %s\n" "#" "Name" "Email" "Status" "Comment (first 80 chars)"
    printf "  %-4s %-20s %-28s %-8s %s\n" "----" "--------------------" "----------------------------" "--------" "------------------------"
    local i=1
    for line in "${REVIEW_LINES[@]}"; do
        IFS='|' read -r _ rid name email hidden excerpt <<< "$line"
        local status="visible"
        [[ "$hidden" == "True" ]] && status="HIDDEN"
        name="${name:0:20}"
        excerpt="${excerpt:0:80}"
        printf "  %-4s %-20s %-28s %-8s %s\n" "$i" "$name" "$email" "$status" "\"$excerpt\""
        ((i++))
    done
    echo ""
}

main() {
    print_header

    # Resolve running task ARN once (ECS mode only)
    if [[ "$USE_DOCKER" != "1" ]]; then
        echo "Looking up running task..."
        TASK_ARN="$(_get_task_arn)"
        if [[ -z "$TASK_ARN" || "$TASK_ARN" == "None" ]]; then
            echo "ERROR: No running task found in cluster $CLUSTER / service $SERVICE"
            exit 1
        fi
        echo "Task: $TASK_ARN"
        echo ""

        # Guard: the --command strings use bash-specific quoting, so the
        # container must have bash available.
        if ! aws ecs execute-command \
                --cluster "$CLUSTER" \
                --task "$TASK_ARN" \
                --container "$CONTAINER" \
                --region "$REGION" \
                --interactive \
                --command "bash --version" > /dev/null 2>&1; then
            echo "ERROR: 'bash' is not available in the container. This script requires bash inside the ECS task."
            exit 1
        fi
    fi

    # --- Step 1: Get URL ---
    local url
    echo "Paste the review page URL (e.g. https://thecourseforum.com/course/42/67/):"
    echo -n "> "
    read -r url

    if [[ -z "$url" ]]; then
        echo "No URL provided. Exiting."
        exit 0
    fi

    # --- Step 2: Fetch review list ---
    echo ""
    echo "Fetching reviews..."
    echo ""

    _run_cmd_capture list_reviews --url "$url" --parseable
    REVIEW_LINES=()
    while IFS= read -r line; do
        REVIEW_LINES+=("$line")
    done < <(_extract_review_lines)

    if [[ ${#REVIEW_LINES[@]} -eq 0 ]]; then
        echo "No reviews found for that URL. Check the URL and try again."
        exit 0
    fi

    # --- Step 3: Interactive selection loop ---
    while true; do
        print_review_table

        local selection
        echo "Enter review # to act on, or 'q' to quit:"
        echo -n "> "
        read -r selection

        [[ "$selection" == "q" || "$selection" == "Q" ]] && { echo "Goodbye."; exit 0; }

        if ! [[ "$selection" =~ ^[0-9]+$ ]] || \
           (( selection < 1 || selection > ${#REVIEW_LINES[@]} )); then
            echo "Invalid selection. Enter a number between 1 and ${#REVIEW_LINES[@]}."
            continue
        fi

        local chosen_line="${REVIEW_LINES[$((selection-1))]}"
        IFS='|' read -r _ review_id name email hidden _ <<< "$chosen_line"

        echo ""
        echo "Selected: #$selection — $name ($email)"
        echo ""
        echo "What would you like to do?"
        echo "  [v] View full review"
        echo "  [h] Hide this review"
        echo "  [u] Unhide this review"
        echo "  [b] Back to list"
        echo "  [q] Quit"
        echo -n "> "
        local action
        read -r action

        case "$(echo "$action" | tr '[:upper:]' '[:lower:]')" in
            v)
                echo ""
                _run_cmd hide_review --id "$review_id" --show || true
                echo ""
                ;;
            h)
                if [[ "$hidden" == "True" ]]; then
                    echo "This review is already hidden. Use [u] to unhide it."
                    continue
                fi
                local reason
                echo ""
                echo "Enter the reason for hiding this review:"
                echo -n "> "
                read -r reason
                if [[ -z "$reason" ]]; then
                    echo "Reason cannot be empty. Action cancelled."
                    continue
                fi
                echo ""
                echo "Hiding review $review_id..."
                _run_cmd hide_review --id "$review_id" --reason "$reason" || {
                    echo "ERROR: Command failed. Review was NOT hidden."
                    continue
                }
                REVIEW_LINES[$((selection-1))]="${chosen_line/|False|/|True|}"
                echo ""
                echo "Review $review_id is now hidden."
                ;;
            u)
                if [[ "$hidden" == "False" ]]; then
                    echo "This review is already visible. Use [h] to hide it."
                    continue
                fi
                local reason
                echo ""
                echo "Enter the reason for unhiding this review:"
                echo -n "> "
                read -r reason
                if [[ -z "$reason" ]]; then
                    echo "Reason cannot be empty. Action cancelled."
                    continue
                fi
                echo ""
                echo "Unhiding review $review_id..."
                _run_cmd hide_review --id "$review_id" --reason "$reason" --unhide || {
                    echo "ERROR: Command failed. Review was NOT changed."
                    continue
                }
                REVIEW_LINES[$((selection-1))]="${chosen_line/|True|/|False|}"
                echo ""
                echo "Review $review_id is now visible."
                ;;
            b)
                continue
                ;;
            q|Q)
                echo "Goodbye."
                exit 0
                ;;
            *)
                echo "Unknown action. Enter v, h, u, b, or q."
                ;;
        esac
    done
}

main "$@"
