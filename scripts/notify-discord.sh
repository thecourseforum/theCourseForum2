#!/bin/bash

function get_content {
    case $GITHUB_EVENT_NAME in 
      pull_request)
        echo "[PR #$PR_NUMBER: $PR_TITLE](https://github.com/thecourseforum/theCourseForum2/pull/$PR_NUMBER) ([`$GITHUB_HEAD_REF`](https://github.com/thecourseforum/theCourseForum2/tree/$GITHUB_HEAD_REF)->[`$GITHUB_BASE_REF`](https://github.com/thecourseforum/theCourseForum2/tree/$GITHUB_BASE_REF))" ;;
      push)
        echo "Push to [`${GITHUB_REF##*/}` branch](https://github.com/thecourseforum/theCourseForum2/tree/${GITHUB_REF##*/})" ;;
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

body=$(cat  << EOF
{
  "content": "[$GITHUB_WORKFLOW] result for **$(get_content)**. See more at https://github.com/thecourseforum/theCourseForum2/actions/runs/$GITHUB_RUN_ID",
  "embeds": [
    {
      "description": "**Pylint**: $PYLINT_RESULT",
      "color": $(get_color $PYLINT_RESULT)
    },
    {
      "description": "**Django**: $DJANGO_RESULT",
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
