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

function get_color {
  case $1 in 
    success) echo 65280 ;;  # green
    failure) echo 16711680 ;;  # red
    skipped) echo 13882323 ;;  # light gray
    cancelled) echo 16776960 ;;  # yellow
    *) echo 0 ;;  # black
  esac
}

run_link="$repo_link/actions/runs/$GITHUB_RUN_ID"
body=$(cat  << EOF
{
  "content": "[$GITHUB_WORKFLOW] $(get_content). See more about the result [here]($run_link).",
  "embeds": [
    {
      "description": "**Pylint**: $PYLINT_RESULT",
      "color": $(get_color $PYLINT_RESULT)
    },
    {
      "description": "**Django**: $DJANGO_RESULT (code coverage: ${DJANGO_COVERAGE:-unknown})",
      "color": $(get_color $DJANGO_RESULT)
    },
    {
      "description": "**ESLint**: $ESLINT_RESULT",
      "color": $(get_color $ESLINT_RESULT)
    }
  ]
}
EOF
)

curl $DISCORD_WEBHOOK \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$body"
