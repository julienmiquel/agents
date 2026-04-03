import vertexai
from vertexai import agent_engines
import os
import sys

# Use the project ID
PROJECT_ID = "ml-demo-384110"
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

print(f"Initializing Vertex AI for Project: {PROJECT_ID}, Location: {LOCATION}")

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
)

print("Listing Vertex AI Agent Engines...")
try:
    # Get all agents in the location
    agents = agent_engines.list()
    
    deleted_count = 0
    for agent in agents:
        display_name = agent.display_name
        resource_name = agent.resource_name
        print(f"Found Agent: '{display_name}' [{resource_name}]")
        
        display_name_lower = display_name.lower()
        # Check if it's a trends or ca bridge agent
        if "trends" in display_name_lower or "ca_bridge" in display_name_lower or "ca bridge" in display_name_lower:
            print(f"👉 Deleting agent: {display_name}...")
            try:
                # Delete the agent with force=True to remove child resources (sessions)
                agent.delete(force=True)
                print(f"✅ Successfully deleted {display_name}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {display_name}: {e}")

    print(f"\nCleanup finished. Deleted {deleted_count} agents.")

except Exception as e:
    print(f"\n❌ Error listing agents: {e}")
    sys.exit(1)
