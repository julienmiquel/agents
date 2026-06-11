# Antigravity Harness & SDK Specialist Agent

This repository contains a SOTA **Vertex AI Reasoning Engine (Agent Engines)** application that serves as a **Developer Advocate & Systems Architect** for the Google unified agent engine (**Antigravity Harness** & **Antigravity SDK**).

---

## 📖 Presentation

The **Antigravity Harness** (introduced at Google I/O 2026) is the single runtime that powers all Google agents. This agent is trained on all formal technical details of the Harness ecosystem. It assists developers in:

1.  **Architecting Integrations**: Explaining and comparing the **Interactions API** (Managed ephemeral Linux sandboxing in the cloud) and the **Antigravity SDK** (Native Python library for custom and local execution).
2.  **Generating Boilerplates**: Instantly providing copy-pasteable, verified integration code blocks for sandboxing, subagents, and step hooks.
3.  **Static Debugging**: Analyzing Python integration scripts to verify imports, identify unsupported parameters (e.g., using `temperature` or `top_p` in preview), and enforce asynchronous guidelines.
### 💡 Programmatic Integrations

#### 1. Interactions API (Managed Remote Sandbox)
Ideal for executing text/image tasks autonomously in a secure, ephemeral remote Linux sandbox using the standard `google-genai` Python client.

```python
from google import genai

client = genai.Client()

# Deploys an ephemeral Linux sandbox and executes in the cloud
interaction = client.interactions.create(
    agent="antigravity-preview-05-2026",
    input="Lis Hacker News, résume les 10 meilleurs articles.",
    extra_body={"environment": "remote"}, # Configures sandbox environment
)

print(interaction.output_text)
```

#### 2. Antigravity SDK (Native Application Runner)
Ideal for custom local agents, dynamic parallel execution loops, and tracking reasoning step callbacks.

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig

async def main():
    config = LocalAgentConfig()
    async with Agent(config) as agent:
        response = await agent.chat("Quels sont les fichiers dans le répertoire courant ?")
        print(await response.text())

asyncio.run(main())
```

---

## 🛠️ Repository Structure

-   `app/`: Modern ADK-based agent package.
    -   `agent.py`: Principal agent definition containing directives, models, and tools imports.
    -   `agent_engine_app.py`: `AdkApp` wrapper integrating telemetry and Google Cloud session managers.
    -   `app_utils/`: Common typing, schema validations, and OpenTelemetry integrations.
    -   `tools/`: Python tooling functions.
        -   `antigravity_tools.py`: Developer toolkit (Guidelines comparer, Snippets catalog, Code validator).
        -   `mock_data.json`: Static assets and verified templates database.
-   `deployment/`: Staging and deployment resources.
    -   `deploy.py`: Staging compilation and registration script for Reasoning Engine and Discovery Engine.
-   `re_register.sh`: CLI runner convenience utility wrapper.
-   `test_agent_locally.py`: Scenario verification pipeline runner.

---

## 🚀 Getting Started

### 1. Prerequisites

1.  **Google Cloud SDK**: Active `gcloud` configuration. Authenticate with ADC credentials:
    ```bash
    gcloud auth application-default login
    ```
2.  **Environment Variables**: Create a `.env` file at the repository root containing:
    ```bash
    GOOGLE_CLOUD_PROJECT="ml-demo-384110"
    GOOGLE_CLOUD_LOCATION="europe-west1"
    GOOGLE_CLOUD_STORAGE_BUCKET="ml-demo-384110-agent-engine"
    GEMINI_APP_ID="enterprise-search-17441866_1744186606233"
    ```

### 2. Run Local Verifications

Test the agent locally on the virtual environment before deployment:

```bash
./re_register.sh --list   # Verification (should list active reasoning engines)
# Run scenario test runner:
.venv/bin/python antigravity-harness-agent/test_agent_locally.py
```

### 3. Register & Deploy to Gemini Enterprise

Registering the agent onto **Gemini Enterprise (Discovery Engine App)** is integrated with the Reasoning Engine build. To compile and deploy, execute:

```bash
./antigravity-harness-agent/re_register.sh --create
```

This script automates the following actions:
1.  **Packages** the `app/` subfolder.
2.  **Registers** dependencies (`google-adk`, `google-genai`, `google-cloud-aiplatform`) with matching versions in the staging environment.
3.  **Uploads** context files to GCS and initiates target-compilation on **Vertex AI Agent Engine**.
4.  **Publishes** and binds the remote Agent Engine ID to the corresponding **Gemini Enterprise Engine App** (`enterprise-search-17441866_1744186606233`).

---

## 🔍 Verification of Remote Deployment

Once registered, you can view the active engine resource metadata via the deploy helper:

```bash
./antigravity-harness-agent/re_register.sh --list
```

You can now interact with this agent dynamically through the Gemini Enterprise dashboard or programmatically by querying the registered Google Cloud agent endpoint!
