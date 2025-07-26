#!/bin/bash

# Default foreign language
DEFAULT_LANGUAGE="Japanese"

# Check if a word argument was provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <word> [foreign_language]"
    exit 1
fi

WORD=$1
FOREIGN_LANGUAGE="${2:-$DEFAULT_LANGUAGE}"

# Perform the curl request
curl -X POST "http://localhost:5001/api/lesson" \
     -H "Content-Type: application/json" \
     -d "{
           \"word\": \"$WORD\",
           \"foreignLanguage\": \"$FOREIGN_LANGUAGE\"
         }" | jq .

# Print a newline for better readability of the output
echo ""