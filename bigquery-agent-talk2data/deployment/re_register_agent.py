import os
import sys
import google.auth
import google.auth.transport.requests
import requests
import json
import datetime
from absl import app, flags
from dotenv import load_dotenv

# Add project root to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("gemini_app_id", None, "Gemini Enterprise App ID.")
flags.DEFINE_string("reasoning_engine_id", None, "Reasoning Engine Resource Name (e.g. projects/.../locations/.../reasoningEngines/...)")

def main(argv):
    del argv  # unused
    load_dotenv(override=True)

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    app_id = FLAGS.gemini_app_id or os.getenv("GEMINI_APP_ID")
    reasoning_engine_id = FLAGS.reasoning_engine_id

    if not project_id:
        print("Missing required flag or environment variable: --project_id or GOOGLE_CLOUD_PROJECT")
        return
    if not app_id:
        print("Missing required flag or environment variable: --gemini_app_id or GEMINI_APP_ID")
        return
    if not reasoning_engine_id:
        print("Missing required flag: --reasoning_engine_id")
        return

    print(f"PROJECT: {project_id}")
    print(f"APP ID: {app_id}")
    print(f"REASONING ENGINE: {reasoning_engine_id}")

    # Get credentials
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "displayName": f"ca_bridge_agent {timestamp}",
        "description": f"Re-registered via utility at {timestamp}",
        "adkAgentDefinition": {
             "provisionedReasoningEngine": {
                "reasoningEngine": reasoning_engine_id
             }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Successfully registered agent. Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Failed to register agent. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error registering agent: {e}")

if __name__ == "__main__":
    app.run(main)
