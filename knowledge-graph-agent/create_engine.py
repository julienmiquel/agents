import requests
import google.auth
import google.auth.transport.requests

credentials, _ = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

url = "https://discoveryengine.googleapis.com/v1alpha/projects/customer-demo-01/locations/global/collections/default_collection/engines?engineId=knowledge-graph-app"
headers = {
    "Authorization": f"Bearer {credentials.token}",
    "x-goog-user-project": "customer-demo-01",
    "Content-Type": "application/json"
}
ds_url = "https://discoveryengine.googleapis.com/v1alpha/projects/customer-demo-01/locations/global/collections/default_collection/dataStores?dataStoreId=knowledge-graph-ds"
ds_body = {
  "displayName": "Knowledge Graph Data Store",
  "industryVertical": "GENERIC",
  "solutionTypes": ["SOLUTION_TYPE_CHAT"],
  "contentConfig": "NO_CONTENT"
}
print("Creating DataStore...")
res_ds = requests.post(ds_url, headers=headers, json=ds_body)
print(res_ds.status_code, res_ds.text)

import time
time.sleep(5)

url = "https://discoveryengine.googleapis.com/v1alpha/projects/customer-demo-01/locations/global/collections/default_collection/engines?engineId=knowledge-graph-app"
body = {
  "displayName": "Knowledge Graph Agent App",
  "solutionType": "SOLUTION_TYPE_CHAT",
  "industryVertical": "GENERIC",
  "dataStoreIds": ["knowledge-graph-ds"],
  "chatEngineConfig": {
    "agentCreationConfig": {
      "business": "Knowledge Graph",
      "defaultLanguageCode": "en",
      "timeZone": "America/Los_Angeles"
    }
  }
}
print("Creating Engine...")
res = requests.post(url, headers=headers, json=body)
print(res.status_code, res.text)
