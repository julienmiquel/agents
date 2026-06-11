import os
import json
import requests
import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv

def main():
    load_dotenv()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
    app_id = os.getenv("GEMINI_APP_ID", "enterprise-search-17441866_1744186606233")

    print(f"PROJECT: {project_id}")
    print(f"APP ID: {app_id}")

    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id
    }

    list_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{app_id}/assistants/default_assistant/agents"
    print(f"\nFetching registered agents from: {list_url}")

    try:
        response = requests.get(list_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to list agents. Status: {response.status_code}")
            print(response.text)
            return
        
        data = response.json()
        agents = data.get("agents", [])
        print(f"Found {len(agents)} registered agents.")

        for idx, agent in enumerate(agents):
            name = agent.get("name")
            display_name = agent.get("displayName", "Unnamed")
            create_time = agent.get("createTime")
            
            # Extract linked reasoning engine
            adk_def = agent.get("adkAgentDefinition", {})
            prov_engine = adk_def.get("provisionedReasoningEngine", {})
            re_resource = prov_engine.get("reasoningEngine", "None")

            print(f"\n[{idx+1}] Agent: {display_name}")
            print(f"    Name: {name}")
            print(f"    Created: {create_time}")
            print(f"    Linked Reasoning Engine: {re_resource}")

            # Keep only the brand new reasoning engine active, prune older ones
            if "6039300712024768512" in re_resource:
                print("    Keep active registration.")
            elif "the_look_ecommerce" in display_name.lower() or "968247531605590016" in re_resource or "8592841700743839744" in re_resource or re_resource == "None":
                print("    ⚠️ Defunct/Outdated registration detected. Deleting...")
                delete_url = f"https://discoveryengine.googleapis.com/v1alpha/{name}"
                del_resp = requests.delete(delete_url, headers=headers)
                if del_resp.status_code in [200, 204]:
                    print("    ✅ Successfully deleted agent registration.")
                else:
                    print(f"    ⚠️ Delete status: {del_resp.status_code}")
                    print(del_resp.text)
            else:
                print("    Keep active registration.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
