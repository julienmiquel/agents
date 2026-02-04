#!/bin/bash
set -e

# Load .env variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Set default values if not in .env
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"customer-demo-01"}
REGION=${GOOGLE_CLOUD_LOCATION:-"europe-west1"}

# Ask for staging bucket if not provided as arg or env var
if [ -z "$STAGING_BUCKET" ]; then
    read -p "Enter GCS Staging Bucket (e.g., gs://my-bucket): " STAGING_BUCKET
fi

if [ -z "$STAGING_BUCKET" ]; then
    echo "Error: STAGING_BUCKET is required."
    exit 1
fi

echo "Deploying image-agent to Agent Engine..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Staging Bucket: $STAGING_BUCKET"

# Run ADK deploy command
# Using current directory (.) as the agent path
# Capture output to log file for parsing
echo "Starting deployment..."
# Fix: Run from project root to satisfy ADK CLI requirements
pushd .. > /dev/null
python3 -m google.adk.cli deploy agent_engine \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --staging_bucket="$STAGING_BUCKET" \
  --display_name="image-agent" \
  --adk_app="deployment_entrypoint" \
  image-agent | tee image-agent/deploy.log
popd > /dev/null

# Extract Reasoning Engine ID
# Look for "Reasoning Engine resource [...]" in the log
# Format: projects/PROJECT_NUMBER/locations/REGION/reasoningEngines/ID
REASONING_ENGINE_ID=$(grep -o 'projects/[0-9]*/locations/[a-z0-9\-]*/reasoningEngines/[0-9]*' deploy.log | tail -n 1)

if [ -z "$REASONING_ENGINE_ID" ]; then
    echo "Warning: Could not extract Reasoning Engine ID from logs."
    echo "Attempting to fetch latest ID via gcloud..."
    # Fallback to gcloud (requires beta component)
    REASONING_ENGINE_ID=$(gcloud beta ai reasoning-engines list --project="$PROJECT_ID" --location="$REGION" --filter="display_name=image-agent" --sort-by="~createTime" --limit=1 --format="value(name)")
fi

if [ -z "$REASONING_ENGINE_ID" ]; then
    echo "Error: Failed to identify deployed Reasoning Engine ID. Skipping registration."
    exit 1
else
    echo "Deployed Agent Engine ID: $REASONING_ENGINE_ID"
fi

# Wait for the Engine to be ready
# Wait for the Engine to be ready
echo "Waiting for Reasoning Engine to be available..."
for i in {1..30}; do
    if gcloud beta ai reasoning-engines describe "$REASONING_ENGINE_ID" --project="$PROJECT_ID" --location="$REGION" &>/dev/null; then
        echo "Reasoning Engine is ready."
        break
    fi
    echo "Waiting 10s..."
    sleep 10
done



# --- Registration ---

# Ask for Gemini App ID if not set
if [ -z "$GEMINI_APP_ID" ]; then
    read -p "Enter Gemini App ID (from Agentspace): " GEMINI_APP_ID
fi

if [ -n "$GEMINI_APP_ID" ]; then
    echo "Registering agent with Gemini Enterprise (App ID: $GEMINI_APP_ID)..."
    
    # Get Access Token
    ACCESS_TOKEN=$(gcloud auth print-access-token)
    
    # Registration Endpoint
    URL="https://discoveryengine.googleapis.com/v1alpha/projects/$PROJECT_ID/locations/global/collections/default_collection/engines/$GEMINI_APP_ID/assistants/default_assistant/agents"
    
    # Fix: Ensure Provisioned Reasoning Engine ID uses Project ID, not Number
    PROJECT_PART=$(echo "$REASONING_ENGINE_ID" | cut -d'/' -f2)
    if [[ "$PROJECT_PART" =~ ^[0-9]+$ ]]; then
         # We need to construct the ID with Project ID manually or assume the API accepts the number.
         # Based on testing, the resource name in the payload must match the deployed resource.
         # If deployment returned Project Number, we should probably stick to it unless validation fails.
         # BUT, for the payload structure fix, nested object is key.
         TARGET_ID="$REASONING_ENGINE_ID"
    else
         TARGET_ID="$REASONING_ENGINE_ID"
    fi
    
    # Payload
    # Fix: Nested provisionedReasoningEngine structure
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

    # Execute Registration
    curl -X POST "$URL" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -H "X-Goog-User-Project: $PROJECT_ID" \
      -d @register_payload.json
      
    echo "" # Newline
    echo "Registration request sent."
    rm register_payload.json
else
    echo "Skipping registration (GEMINI_APP_ID not provided)."
fi
