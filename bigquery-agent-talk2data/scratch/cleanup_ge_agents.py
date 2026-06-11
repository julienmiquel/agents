import os
import sys
import google.auth
import google.auth.transport.requests
import requests
import json
import datetime
import logging
from absl import app, flags
from dotenv import load_dotenv

# Add project root to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("gemini_app_id", None, "Gemini Enterprise App ID (comma-separated for multiple).")
flags.DEFINE_bool("dry_run", False, "List duplicates without deleting them.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def list_agents(project_id, app_id, credentials):
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "X-Goog-User-Project": project_id
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("agents", [])
        else:
            logger.error(f"Error listing agents for {app_id}: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception listing agents for {app_id}: {e}")
        return []

def delete_agent(project_id, agent_name, credentials):
    url = f"https://discoveryengine.googleapis.com/v1alpha/{agent_name}"
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "X-Goog-User-Project": project_id
    }
    try:
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            logger.info(f"Successfully deleted agent: {agent_name}")
        else:
            logger.error(f"Failed to delete agent {agent_name}: {response.text}")
    except Exception as e:
        logger.error(f"Exception deleting agent {agent_name}: {e}")

def main(argv):
    del argv  # unused
    load_dotenv(override=True)

    project_id = FLAGS.project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
    app_ids_str = FLAGS.gemini_app_id or os.getenv("GEMINI_APP_ID")

    if not project_id:
        logger.error("Missing required flag or environment variable: --project_id or GOOGLE_CLOUD_PROJECT")
        return
    if not app_ids_str:
        logger.error("Missing required flag or environment variable: --gemini_app_id or GEMINI_APP_ID")
        return

    app_ids = [acc.strip() for acc in app_ids_str.split(",")]

    logger.info(f"PROJECT: {project_id}")
    logger.info(f"APP IDs: {app_ids}")
    if FLAGS.dry_run:
        logger.info("DRY RUN mode enabled. No agents will be deleted.")

    # Get credentials
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    for engine in app_ids:
        logger.info(f"--- Checking engine: {engine} ---")
        agents = list_agents(project_id, engine, credentials)
        
        grouped = {
            "ca_bridge_agent": [],
            "Image Agent": [],
            "image_agent": []
        }
        
        for a in agents:
            display_name = a.get("displayName", "")
            
            if "ca_bridge_agent" in display_name:
                grouped["ca_bridge_agent"].append(a)
            elif "Image Agent" in display_name:
                grouped["Image Agent"].append(a)
            elif "image_agent" in display_name:
                grouped["image_agent"].append(a)
                
        for base_name, agent_list in grouped.items():
            if len(agent_list) > 1:
                logger.info(f"Found {len(agent_list)} agents for: {base_name}")
                # Sort by create time descending
                agent_list.sort(key=lambda x: x["createTime"], reverse=True)
                
                # Keep the first one (newest) and delete others
                logger.info(f"Keeping newest: {agent_list[0]['displayName']} ({agent_list[0]['name']})")
                for dup in agent_list[1:]:
                    logger.info(f"Duplicate to delete: {dup['displayName']} ({dup['name']})")
                    if not FLAGS.dry_run:
                        delete_agent(project_id, dup["name"], credentials)
            elif len(agent_list) == 1:
                logger.info(f"Only one agent found for {base_name}: {agent_list[0]['displayName']}")

if __name__ == "__main__":
    app.run(main)
