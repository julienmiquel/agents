import os
import google.auth
import google.auth.transport.requests
import requests
import json
from dotenv import load_dotenv

load_dotenv()

project_id = "ml-demo-384110"
app_id = "enterprise-search-17441866_1744186606233"

credentials, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json",
    "X-Goog-User-Project": project_id
}

url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
res = requests.get(url, headers=headers)
if res.status_code == 200:
    agents = res.json().get("agents", [])
    print(f"Total agents found: {len(agents)}")
    print("\nListing all data_analyst_orchestrator agents:")
    for ag in agents:
        disp = ag.get('displayName', '')
        if "data_analyst_orchestrator" in disp:
            print(f"- Agent: {ag.get('name')}")
            print(f"  Display Name: {disp}")
            print(f"  State: {ag.get('state')}")
            print(f"  Reasoning Engine: {ag.get('adkAgentDefinition', {}).get('provisionedReasoningEngine', {}).get('reasoningEngine')}")
else:
    print(res.text)
