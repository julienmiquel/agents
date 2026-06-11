import google.auth
import google.auth.transport.requests
import requests
import json

credentials, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

project_id = "customer-demo-01"

locations = [
    ("global", "discoveryengine.googleapis.com"),
    ("eu", "eu-discoveryengine.googleapis.com"),
    ("us", "us-discoveryengine.googleapis.com")
]

for loc, endpoint in locations:
    url = f"https://{endpoint}/v1alpha/projects/{project_id}/locations/{loc}/collections/default_collection/engines"
    headers = {"Authorization": f"Bearer {credentials.token}", "x-goog-user-project": project_id}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        engines = res.json().get("engines", [])
        for e in engines:
            print(f"Location: {loc} | ID: {e['name'].split('/')[-1]} | Display: {e.get('displayName')}")
    else:
        print(f"Error in {loc}: {res.status_code} {res.text}")
