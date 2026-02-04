#!/bin/bash
set -e

# Load .env variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set default values if not in .env
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"customer-demo-01"}
REGION=${GOOGLE_CLOUD_LOCATION:-"europe-west1"}

TARGET_ID="projects/ml-demo-384110/locations/europe-west1/reasoningEngines/3868811982236811264"
echo "Using ID for registration: $TARGET_ID"


# --- Registration ---

# Ask for Gemini App ID if not set
if [ -z "$GEMINI_APP_ID" ]; then
    read -p "Enter Gemini App ID (from Agentspace): " GEMINI_APP_ID
fi

if [ -n "$GEMINI_APP_ID" ]; then
    echo "Registering agent with Gemini Enterprise (App ID: $GEMINI_APP_ID)..."
    
    # Try using ADC token as suggested by the warning
    echo "Getting Access Token..."
    # Try ADC first, then standard
    if gcloud auth application-default print-access-token &>/dev/null; then
        echo "Using Application Default Credentials (ADC)..."
        ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
    else
        echo "Using standard gcloud auth..."
        ACCESS_TOKEN=$(gcloud auth print-access-token)
    fi
    
    # Registration Endpoint
    URL="https://discoveryengine.googleapis.com/v1alpha/projects/$PROJECT_ID/locations/global/collections/default_collection/engines/$GEMINI_APP_ID/assistants/default_assistant/agents"
    echo "URL: $URL"
    # Payload
    cat > register_payload.json <<EOF
{
  "displayName": "Image Agent",
  "description": "Generates and upscales images using Vertex AI models.",
  "adkAgentDefinition": {
    "provisionedReasoningEngine": {
      "reasoningEngine": "$TARGET_ID"
    }
  }
}
EOF
    echo "Payload:"
    cat register_payload.json

    # Execute Registration
    curl -v -X POST "$URL" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" -H "X-Goog-User-Project: ml-demo-384110" \
      -d @register_payload.json
      
    echo ""
    rm register_payload.json
else
    echo "Skipping registration (GEMINI_APP_ID not provided)."
fi
