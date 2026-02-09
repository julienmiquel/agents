# image-agent

Simple ReAct agent
Agent generated with [`googleCloudPlatform/agent-starter-pack`](https://github.com/GoogleCloudPlatform/agent-starter-pack) version `0.33.2`

## Features

*   **Image Generation**: Leverages Gemini 3 Pro for high-quality image generation with reasoning capabilities.
*   **Image Upscaling**: Enhances image resolution (4x default, 2x for large images).
*   **Artifact Handling**: Supports downloading files from URLs and loading images from artifacts for processing.

## Project Structure

```
image-agent/
├── app/         # Core agent code
│   ├── agent.py               # Main agent logic
│   ├── agent_engine_app.py    # Agent Engine application logic
│   └── app_utils/             # App utilities and helpers
├── tests/                     # Unit, integration, and load tests
├── GEMINI.md                  # AI-assisted development guide
├── Makefile                   # Development commands
└── pyproject.toml             # Project dependencies
```

> 💡 **Tip:** Use [Gemini CLI](https://github.com/google-gemini/gemini-cli) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Prerequisites

*   Python 3.10+
*   uv
    *   For dependency management and packaging. Please follow the
        instructions on the official
        [uv website](https://docs.astral.sh/uv/) for installation.

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

* A project on Google Cloud Platform
* Google Cloud CLI
    *   For installation, please follow the instruction on the official
        [Google Cloud website](https://cloud.google.com/sdk/docs/install).

## Installation

You can choose between `uv` (Recommended) or `poetry`.

### Option 1: Using `uv` (Recommended)

`uv` is extremely fast and pre-configured for this project.

```bash
# Install dependencies
uv sync
```

### Option 2: Using `poetry`

If you prefer Poetry, we have enabled support for it.

```bash
# Install dependencies
poetry install
```


## Running with uv

You can also run the agent web interface directly using `uv`:

```bash
uv run adk web
```
or 
```bash
uvx adk web
```

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install dependencies using uv                                                               |
| `make playground`    | Launch local development environment                                                        |
| `make lint`          | Run code quality checks                                                                     |
| `make test`          | Run unit and integration tests                                                              |
| `make deploy`        | Deploy agent to Agent Engine                                                                |
| `make register-gemini-enterprise` | Register deployed agent to Gemini Enterprise                                  |

For full command options and usage, refer to the [Makefile](Makefile).

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `uvx agent-starter-pack enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `uvx agent-starter-pack setup-cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `uvx agent-starter-pack upgrade` | Auto-upgrade to latest version while preserving customizations |
| `uvx agent-starter-pack extract` | Extract minimal, shareable version of your agent |

---

## Development

Edit your agent logic in `app/agent.py` and test with `make playground` - it auto-reloads on save.
See the [development guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/development-guide) for the full workflow.

## Deployment

```bash
gcloud config set project <your-project-id>
make deploy
```

To add CI/CD and Terraform, run `uvx agent-starter-pack enhance`.
To set up your production infrastructure, run `uvx agent-starter-pack setup-cicd`.
See the [deployment guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment) for details.

### Alternative Deployment (Manual)

You can also deploy using the Python script directly, which is useful for testing or simple deployments.

#### Option 1: Using `uv`

```bash
# Create and deploy the agent
uv run python deployment/deploy.py --create

# List deployed agents
uv run python deployment/deploy.py --list
```

#### Option 2: Using `poetry`

```bash
# Create and deploy the agent
poetry run python deployment/deploy.py --create

# List deployed agents
poetry run python deployment/deploy.py --list
```

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.
See the [observability guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/observability) for queries and dashboards.
