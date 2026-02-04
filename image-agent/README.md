# Google ADK Image Agent

This agent is a reference implementation using the **Google Agent Development Kit (ADK)**. It demonstrates how to build an agent that can generate and upscale images using Vertex AI models.

## Features

- **Image Generation**: Generates images from text descriptions using Gemini 3 Pro Image models.
- **Image Upscaling**: Enhances image resolution (up to 4K) using Imagen 4.0.
- **Conversational Interface**: Remembers context, allowing for iterative refinement (e.g., "Make it bigger").

## Setup

1.  **Prerequisites**:
    - Google Cloud Project with Vertex AI enabled.
    - Python 3.10+ installed.
    - `adk` CLI installed.

2.  **Environment Variables**:
    Create a `.env` file or export these variables:
    ```bash
    export GOOGLE_CLOUD_PROJECT="your-project-id"
    export GOOGLE_CLOUD_LOCATION="europe-west1" # or your preferred region
    ```

3.  **Installation**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running Locally
To test the agent structure:
```bash
python3 tests/verify_structure.py
```

### Deployment
Use the `deploy.sh` script to deploy to Google Cloud Agent Engine:
```bash
./deploy.sh
```
This script will:
1. Deploy the agent to Vertex AI Agent Engine.
2. Automatically register it with Gemini Enterprise (Agentspace).

Requires a GCS bucket for staging artifacts (you will be prompted if not set in `.env`).

## Documentation
- [Functional Specifications](docs/FSD.md)
- [Product Requirements](docs/PRD.md)
