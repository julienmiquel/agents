# Deployment

This directory contains the Terraform configurations for provisioning the necessary Google Cloud infrastructure for your agent.

The recommended way to deploy the infrastructure and set up the CI/CD pipeline is by using the `agent-starter-pack setup-cicd` command from the root of your project.

However, for a more hands-on approach, you can always apply the Terraform configurations manually for a do-it-yourself setup.

For detailed information on the deployment process, infrastructure, and CI/CD pipelines, please refer to the official documentation:

**[Agent Starter Pack Deployment Guide](https://googlecloudplatform.github.io/agent-starter-pack/guide/deployment.html)**

## Using Deployment Script

For manual deployment management without Terraform, you can use the `deploy.py` script:

### Prerequisites
Ensure you have the necessary environment variables set in your `.env` file or environment:
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_CLOUD_STORAGE_BUCKET`
- `GEMINI_APP_ID` (for Gemini Enterprise registration)

### Commands

**Create or Update Agent:**
```bash
uv run python deploy.py --create [--project_id=...] [--location=...]
```

**List Agents:**
```bash
uv run python deploy.py --list
```

**Delete Agent:**
```bash
uv run python deploy.py --delete --resource_id=...
```