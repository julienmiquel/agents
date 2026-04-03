# BigQuery Agent (Talk2Data / CA Bridge Agent)

This repository contains a Vertex AI Agent Engine (Reasoning Engine) application that bridges queries to the Google Trends Conversational Analytics API or BigQuery.

## Repository Structure

- `app/`: Modern ADK-based agent package.
    - `agent.py`: Defines the ADK agent and tools.
    - `agent_engine_app.py`: Defines the `AdkApp` wrapper for deployment.
- `deployment/`: Deployment scripts.
    - `deploy.py`: Standard tool for deploying and registering the agent.
- `scripts/`: Utility scripts.
    - `add_permissions.sh`: Sets up IAM permissions for service accounts to access BigQuery and Vertex AI.
    - `cleanup_agents.py`: Cleans up deployed agents from Vertex AI.
    - `verify_ca_bridge.py`: Verifies the deployment by sending a test query.

## Prerequisites

1.  **Google Cloud Project**: Ensure you have a GCP project with Vertex AI and BigQuery APIs enabled.
2.  **Authentication**: Authenticate using `gcloud auth application-default login`.
3.  **Permissions**: Run `scripts/add_permissions.sh` to grant necessary roles to service accounts.

## Usage

### 1. Setup Permissions

Run the permissions script to ensure Vertex AI can access BigQuery:

```bash
chmod +x scripts/add_permissions.sh
./scripts/add_permissions.sh
```

### 2. Set Environment Variables

Create a `.env` file or export the variables:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_CLOUD_STORAGE_BUCKET="your-staging-bucket"
export GEMINI_MODEL="gemini-2.5-flash" # Default is gemini-2.5-flash
export GEMINI_APP_ID="your-gemini-enterprise-app-id" # Optional for registration
```

### 3. Deploy the Agent

Use the standard deployment script:

```bash
python deployment/deploy.py --create
```

This will:
1.  Package the `app/` directory.
2.  Deploy the agent to Vertex AI Reasoning Engine.
3.  Register the agent with Gemini Enterprise (if `GEMINI_APP_ID` is provided).

### 4. Verify Deployment

Run the verification script:

```bash
export REASONING_ENGINE="projects/your-project-number/locations/us-central1/reasoningEngines/your-engine-id"
python scripts/verify_ca_bridge.py
```

### 5. CI/CD Deployment with Cloud Build

You can deploy the agent automatically using Google Cloud Build. The repo contains a root `cloudbuild.yaml` that triggers this sub-project's build.

To trigger it manually from the workspace root (recommended to run in the target project):

```bash
gcloud builds submit --project=your-target-project-id --config=cloudbuild.yaml .
```

Or run it directly for this sub-project (faster upload of code context):

```bash
cd bigquery-agent-talk2data
gcloud builds submit --project=your-target-project-id --config=deployment/cloudbuild.yaml .
```

### 6. Cleanup

To list or delete agents:

```bash
python deployment/deploy.py --list
python deployment/deploy.py --delete --resource_id "projects/.../reasoningEngines/..."
```

Or use the cleanup script to remove all Trends/CA Bridge agents:

```bash
python scripts/cleanup_agents.py
```
