#!/bin/bash

# Script: prune-gh-branches.sh
# Requirements: Linux terminal (like WSL), gh and jq installed. 
#   Also, please use ```gh auth login``` to login to github beforehand
# Description: Deletes branches older than specified number of months (based on most recent edit)
# Usage: Run the script with the number of months as an argument.
# Example: ./prune-gh-branches.sh 18

# Check if the number of months is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <number_of_months>"
  echo "Example: ./prune-gh-branches.sh 18 (to delete branches older than 18 months)"
  exit 1
fi

# Set the repository name
REPO="thecourseforum/theCourseForum2"

# Get the number of months from the user input
MONTHS=$1

# Get the current date in ISO format
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Calculate the date X months ago
X_MONTHS_AGO=$(date -u -d "$MONTHS months ago" +"%Y-%m-%dT%H:%M:%SZ")

# Fetch all branches
BRANCHES=$(gh api repos/$REPO/branches --paginate | jq -r '.[].name')

# Check if there are any branches
if [ -z "$BRANCHES" ]; then
  echo "No branches found in the repository."
  exit 0
fi

# Initialize an empty array to store old branches
OLD_BRANCHES=()

# Loop through each branch and fetch the last commit date
echo "Checking branches for last commit date..."
for BRANCH in $BRANCHES; do
  # Fetch the last commit date for the branch
  LAST_COMMIT_DATE=$(gh api repos/$REPO/branches/$BRANCH | jq -r '.commit.commit.committer.date')

  # Check if the last commit date is older than X months
  if [[ "$LAST_COMMIT_DATE" < "$X_MONTHS_AGO" ]]; then
    OLD_BRANCHES+=("$BRANCH $LAST_COMMIT_DATE")
  fi
done

# Check if there are any old branches
if [ ${#OLD_BRANCHES[@]} -eq 0 ]; then
  echo "No branches older than $MONTHS months found."
  exit 0
fi

# Print the list of old branches with their last commit date
echo "The following branches were last edited at least $MONTHS months ago:"
echo "Branch Name | Last Commit Date"
echo "-----------------------------"
for BRANCH_INFO in "${OLD_BRANCHES[@]}"; do
  echo "$BRANCH_INFO"
done
echo ""

# Ask for confirmation
read -p "Do you want to delete these branches? (y/n): " CONFIRM
if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
  echo "Aborting. No branches were deleted."
  exit 0
fi

# Delete the branches
for BRANCH_INFO in "${OLD_BRANCHES[@]}"; do
  BRANCH_NAME=$(echo "$BRANCH_INFO" | awk '{print $1}')
  echo "Deleting branch: $BRANCH_NAME"
  gh api -X DELETE repos/$REPO/git/refs/heads/$BRANCH_NAME
done

echo "Done! All specified branches have been deleted."