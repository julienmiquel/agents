"""Deployment script for CA Bridge Agent using Robust Architecture."""

import os
import sys
import argparse
import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# Add current working directory to sys.path so 'app' module can be found
sys.path.append(os.getcwd())

# We import root_agent from app.agent
from app.agent import root_agent

import google.auth
import google.auth.transport.requests
import requests
import json

def parse_args():
    """Parse command-line arguments for deployment."""
    parser = argparse.ArgumentParser(description="Deploy CA Bridge Agent to Vertex AI.")
    parser.add_argument("--project_id", type=str, default=None, help="GCP project ID.")
    parser.add_argument("--location", type=str, default=None, help="GCP location.")
    parser.add_argument("--bucket", type=str, default=None, help="GCP bucket.")
    parser.add_argument("--gemini_app_id", type=str, default=None, help="Gemini Enterprise App ID.")
    parser.add_argument("--list", action="store_true", help="List all agents.")
    parser.add_argument("--create", action="store_true", help="Creates a new agent.")
    parser.add_argument("--delete", action="store_true", help="Deletes an existing agent.")
    parser.add_argument("--resource_id", type=str, default=None, help="Resource ID for delete.")
    return parser

def register_agent(remote_agent: object, project_id: str, app_id: str) -> None:
    """Registers the agent with Gemini Enterprise (Discovery Engine)."""
    if not app_id:
        print("Skipping registration (GEMINI_APP_ID not provided).")
        return

    print(f"Registering agent {remote_agent.display_name} with Gemini Enterprise (App ID: {app_id})...")
    
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
    
    print(f"Registration URL: {url}")

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    payload = {
        "displayName": f"{remote_agent.display_name} {timestamp}",
        "description": f"Deployed via robust ADK architecture at {timestamp}",
        "adkAgentDefinition": {
             "provisionedReasoningEngine": {
                "reasoningEngine": remote_agent.resource_name
             }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"Successfully registered agent. Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Failed to register agent. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error registering agent: {e}")

def create(args) -> None:
    """Creates an agent engine."""
    from app.agent_engine_app import agent_engine
    adk_app = agent_engine

    print("Deploying Reasoning Engine (Agent Engines)...")
    remote_agent = agent_engines.create(
        adk_app,
        display_name=root_agent.name,
        requirements=[
            "google-adk>=1.15.0",
            "google-cloud-aiplatform[agent-engines]==1.130.0",
            "google-genai>=1.5.0",
            "google-auth",
            "requests",
            "google-cloud-geminidataanalytics",
        ],
        extra_packages=["app"],
    )
    print(f"Created remote agent: {remote_agent.resource_name}")
    
    project_id = args.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    app_id = args.gemini_app_id or os.getenv("GEMINI_APP_ID")
    
    register_agent(remote_agent, project_id, app_id)


def delete(resource_id: str) -> None:
    """Deletes a remote agent by resource ID."""
    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Deleted remote agent: {resource_id}")


def list_agents() -> None:
    """Lists all remote agents in the current location."""
    remote_agents = agent_engines.list()
    template = """
{agent.name} ("{agent.display_name}")
- Create time: {agent.create_time}
- Update time: {agent.update_time}
"""
    remote_agents_string = "\n".join(
        template.format(agent=agent) for agent in remote_agents
    )
    print(f"All remote agents:\n{remote_agents_string}")


def main() -> None:
    """Main entry point for deployment CLI."""
    load_dotenv(override=True)
    parser = parse_args()
    args = parser.parse_args()

    project_id = args.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = args.location or os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = args.bucket or os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")

    print(f"PROJECT: {project_id}")
    print(f"LOCATION: {location}")
    print(f"BUCKET: {bucket}")

    if not project_id:
        print("Missing project_id")
        return
    if not location:
        print("Missing location")
        return
    if not bucket:
        print("Missing bucket")
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=bucket if bucket.startswith("gs://") else f"gs://{bucket}",
    )

    if args.list:
        list_agents()
    elif args.create:
        create(args)
    elif args.delete:
        if not args.resource_id:
            print("resource_id is required for delete")
            return
        delete(args.resource_id)
    else:
        print("Unknown command or missing action flag (--create, --delete, --list)")


if __name__ == "__main__":
    main()
