#!/bin/bash

function get_content {
    case $GITHUB_EVENT_NAME in 
      pull_request)
        echo "**PR #$PR_NUMBER: $PR_TITLE** (`$GITHUB_HEAD_REF` -> `$GITHUB_BASE_REF`)" ;;
      push)
        echo "**Push to master**" ;;
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
  "content": "GitHub Actions result for $(get_content)",
  "embeds": [
    {
      "title": "Pylint",
      "description": "$PYLINT_RESULT",
      "color": $(get_color $PYLINT_RESULT)
    },
    {
      "title": "Django",
      "description": "$DJANGO_RESULT",
      "color": $(get_color $DJANGO_RESULT)
    },
    {
      "title": "ESLint",
      "description": "$ESLINT_RESULT",
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
