#!/bin/bash

repo_link="https://github.com/thecourseforum/theCourseForum2"
function get_content {
    case $GITHUB_EVENT_NAME in 
      pull_request)
        prefix="**[PR #$PR_NUMBER: $PR_TITLE]($repo_link/pull/$PR_NUMBER)**"
        head="[\`$GITHUB_HEAD_REF\`]($repo_link/tree/$GITHUB_HEAD_REF)"
        base="[\`$GITHUB_BASE_REF\`]($repo_link/tree/$GITHUB_BASE_REF)"
        echo "$prefix: $head→$base" ;;
      push)
        echo "**Push to [\`${GITHUB_REF##*/}\` branch]($repo_link/tree/${GITHUB_REF##*/})**" ;;
      *)
        echo "Unsupported event."
        exit 1 ;;
    esac
}

function get_last_commit {
    case $GITHUB_EVENT_NAME in 
      pull_request)
        echo $LATEST_PR_COMMIT ;;
      push)
        echo "HEAD" ;;
      *)
        echo "Unsupported event."
        exit 1 ;;
    esac
}

function get_color {
  if [[ $1 == "success" && $2 == "success" && $3 == "success" ]]
  then
    echo 65280;  # green
  else
    echo 16711680;  # red
  fi
}

function get_emoji {
  case $1 in 
    success) echo ":white_check_mark:" ;;
    failure) echo ":x:" ;;  # a red X
    skipped) echo ":track_next:" ;;
    cancelled) echo ":warning:" ;;  # a yellow warning sign
    *) echo ":grey_question:"; exit 1 ;;  # unexpected input
  esac
}
run_link="$repo_link/actions/runs/$GITHUB_RUN_ID"
pylint_formatted="$(get_emoji $PYLINT_RESULT) **Pylint**"
django_formatted="$(get_emoji $DJANGO_RESULT) **Django** (code coverage: ${DJANGO_COVERAGE:-unknown})"
eslint_formatted="$(get_emoji $ESLINT_RESULT) **ESLint**"
commit_message_quoted_wrapped="$(git log -1 --pretty=format:"%s" $(get_last_commit) | jq -R)"
commit_message_formatted="Last commit message: ${commit_message_quoted_wrapped:1:-1}"
body=$(cat  << EOF
{
  "content": "$(get_content) ($commit_message_formatted). See more about the result [here]($run_link).",
  "embeds": [
    {
      "description": "$pylint_formatted\\n$django_formatted\\n$eslint_formatted",
      "color": $(get_color $PYLINT_RESULT $DJANGO_RESULT $ESLINT_RESULT)
    }
  ]
}
EOF
)

response=$(curl $DISCORD_WEBHOOK \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$body" | jq -r .message)

if [[ $response != "" ]]
then
  echo $response
  exit 1
fi
