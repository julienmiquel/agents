#!/bin/bash
set -e

# Load .env variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Find Operation Name
if [ -f deploy.log ]; then
  OPERATION_NAME=$(grep -o 'projects/[0-9]*/locations/[a-z0-9\-]*/reasoningEngines/[0-9]*/operations/[0-9]*' deploy.log | tail -n 1)
fi

if [ -z "$OPERATION_NAME" ]; then
    echo "Usage: ./check_operation.sh <OPERATION_NAME>"
    echo "Could not find operation in deploy.log"
    exit 1
fi

echo "Checking Operation: $OPERATION_NAME"

ACCESS_TOKEN=$(gcloud auth print-access-token)
# Operations are usually region-specific?
# URL format: https://europe-west1-aiplatform.googleapis.com/v1beta1/projects/.../operations/...
# But the name is fully qualified.
# Use the location from the name.
LOCATION=$(echo "$OPERATION_NAME" | cut -d'/' -f4)
URL="https://${LOCATION}-aiplatform.googleapis.com/v1beta1/$OPERATION_NAME"

curl -s -H "Authorization: Bearer $ACCESS_TOKEN" "$URL"
