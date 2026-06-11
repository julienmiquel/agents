import os
import google.auth
import google.auth.transport.requests
import requests
from dotenv import load_dotenv

load_dotenv()

project_id = "ml-demo-384110"

credentials, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

headers = {
    "Authorization": f"Bearer {credentials.token}",
    "X-Goog-User-Project": project_id
}

old_agent_ids = [
    "2418049058772877312"
]

for agent_id in old_agent_ids:
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/enterprise-search-17441866_1744186606233/assistants/default_assistant/agents/{agent_id}"
    print(f"Deleting agent registration: {url}")
    res = requests.delete(url, headers=headers)
    print("Delete Status:", res.status_code)
    if res.status_code == 200:
        print(f"Successfully deleted agent registration: {agent_id}")
    else:
        print(res.text)
