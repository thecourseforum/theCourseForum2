#!/bin/bash

repo_link="https://github.com/thecourseforum/theCourseForum2"
function get_content {
    case $GITHUB_EVENT_NAME in 
      pull_request)
        prefix="**[PR #$PR_NUMBER: $PR_TITLE]($repo_link/pull/$PR_NUMBER)**"
        head="[\`$GITHUB_HEAD_REF\`]($repo_link/tree/$GITHUB_HEAD_REF)"
        base="[\`$GITHUB_BASE_REF\`]($repo_link/tree/$GITHUB_BASE_REF)"
        echo "$prefix ($head->$base)" ;;
      push)
        echo "**Push to [\`${GITHUB_REF##*/}\` branch]($repo_link/tree/${GITHUB_REF##*/})**" ;;
      *)
        echo "Unsupported event."
        exit 1 ;;
    esac
  # 
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
pylint_formatted="**Pylint** $(get_emoji $PYLINT_RESULT)"
django_formatted="**Django** $(get_emoji $DJANGO_RESULT) (code coverage: ${DJANGO_COVERAGE:-unknown})"
eslint_formatted="**ESLint** $(get_emoji $ESLINT_RESULT)"
body=$(cat  << EOF
{
  "content": "$(get_content). See more about the result [here]($run_link).",
  "embeds": [
    {
      "description": "$pylint_formatted | $django_formatted | $eslint_formatted"
    }
  ]
}
EOF
)

curl $DISCORD_WEBHOOK \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$body"
