#!/bin/bash
set -e

# Load .env variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set default values if not in .env
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"customer-demo-01"}
REGION=${GOOGLE_CLOUD_LOCATION:-"europe-west1"}

# Get Reasoning Engine ID
# If provided as argument, use it. Otherwise try to grep it from deploy.log
if [ -n "$1" ]; then
    REASONING_ENGINE_ID="$1"
elif [ -f deploy.log ]; then
    REASONING_ENGINE_ID=$(grep -o 'projects/[0-9]*/locations/[a-z0-9\-]*/reasoningEngines/[0-9]*' deploy.log | tail -n 1)
fi

# Fallback
if [ -z "$REASONING_ENGINE_ID" ]; then
    echo "Warning: Could not extract Reasoning Engine ID from logs or argument."
    echo "Attempting to fetch latest ID via gcloud..."
    REASONING_ENGINE_ID=$(gcloud beta vertex ai reasoning-engines list --project="$PROJECT_ID" --location="$REGION" --filter="display_name=image-agent" --sort-by="~createTime" --limit=1 --format="value(name)")
fi

if [ -z "$REASONING_ENGINE_ID" ]; then
    echo "Error: Failed to identify deployed Reasoning Engine ID."
    exit 1
else
    echo "Found Agent Engine ID: $REASONING_ENGINE_ID"
fi

# Attempt to fix the resource name if it uses Project Number
# The API might expect 'projects/PROJECT_ID/...'
# Check if the ID starts with a number
PROJECT_PART=$(echo "$REASONING_ENGINE_ID" | cut -d'/' -f2)

# If PROJECT_PART is numeric (simple check), try to replace it with PROJECT_ID
# Note: This is an assumption based on the 400 error.
if [[ "$PROJECT_PART" =~ ^[0-9]+$ ]]; then
# echo "Detected Project Number in ID: $PROJECT_PART"
    # ALT_REASONING_ENGINE_ID=${REASONING_ENGINE_ID/$PROJECT_PART/$PROJECT_ID}
    # echo "Alternative ID with Project ID: $ALT_REASONING_ENGINE_ID"
    
    # Use the original ID for registration (Permission fix should resolve the issue)
    TARGET_ID="$REASONING_ENGINE_ID"
else
    TARGET_ID="$REASONING_ENGINE_ID"
fi

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
    
    # Payload
    cat > register_payload.json <<EOF
{
  "displayName": "Image Agent",
  "description": "Generates and upscales images using Vertex AI models.",
  "adkAgentDefinition": {
    "provisionedReasoningEngine": "$TARGET_ID"
  }
}
EOF
    echo "Payload:"
    cat register_payload.json

    # Execute Registration
    curl -v -X POST "$URL" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d @register_payload.json
      
    echo ""
    rm register_payload.json
else
    echo "Skipping registration (GEMINI_APP_ID not provided)."
fi
