import os
import vertexai
from dotenv import load_dotenv
load_dotenv()

project = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

vertexai.init(project=project, location=location)

from vertexai import agent_engines

print("Listing all reasoning engines:")
try:
    engines = list(agent_engines.list())
    for eng in engines:
        print(f"- {eng.resource_name} ({eng.display_name})")
except Exception as e:
    print(f"Error: {e}")
