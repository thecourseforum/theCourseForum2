#!/bin/bash

function get_content() {
  repo_link="https://github.com/thecourseforum/theCourseForum2"
  run_link="$repo_link/actions/runs/$GITHUB_RUN_ID"
  if [ "$DEPLOY_RESULT" = "success" ]; then
    echo "New deployment to https://thecourseforum.com/." \
      "Click [here]($repo_link/commits/master) to see the most recent" \
      "commits to \`master\`."
  else
    echo "Deployment failed. Click [here]($run_link) to see why."
  fi
}

response=$(curl $DISCORD_WEBHOOK \
  -X "POST" \
  -H "Content-Type: application/json" \
  -d "{ \"content\" : \"$(get_content)\" }" | jq -r .message)

if [[ $response != "" ]]
then
  echo $response
  exit 1
fi
