#!/bin/bash
set -e

# Load .env variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

ENGINE_ID="$1"

if [ -z "$ENGINE_ID" ]; then
  # Try to find it from deploy.log
  if [ -f deploy.log ]; then
    ENGINE_ID=$(grep -o 'projects/[0-9]*/locations/[a-z0-9\-]*/reasoningEngines/[0-9]*' deploy.log | tail -n 1)
  fi
fi

if [ -z "$ENGINE_ID" ]; then
    echo "Usage: ./poll_engine.sh <ENGINE_ID>"
    exit 1
fi

echo "Polling status for: $ENGINE_ID"

# Loop
for i in {1..20}; do
    ACCESS_TOKEN=$(gcloud auth print-access-token)
    URL="https://europe-west1-aiplatform.googleapis.com/v1beta1/$ENGINE_ID"
    
    RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "$URL")
    
    # Check for errors
    if echo "$RESPONSE" | grep -q '"error":'; then
        echo "Error fetching status:"
        echo "$RESPONSE"
        # If NOT_FOUND, maybe still creating? or failed?
    else
        # Extract state (simplified grep/sed)
        # Assuming JSON response
        echo "Response received."
        # echo "$RESPONSE" # Debug
        
        # Check if contains "state" or "createTime"
        # Reasoning Engine doesn't have a clear "state" field in v1beta1 sometimes?
        # It has `createTime` and `updateTime`.
        # If it exists, it's usually good.
        
       echo "Engine exists."
       exit 0
    fi
    
    echo "Waiting 10s..."
    sleep 10
done

echo "Timeout."
exit 1
