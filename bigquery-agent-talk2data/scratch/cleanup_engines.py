import os
import vertexai
from dotenv import load_dotenv
load_dotenv()

project = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

vertexai.init(project=project, location=location)

from vertexai import agent_engines

old_engines = [
    "projects/1008225662928/locations/europe-west1/reasoningEngines/5398293922684403712"
]

for eng_id in old_engines:
    print(f"Deleting reasoning engine: {eng_id}")
    try:
        engine = agent_engines.get(eng_id)
        engine.delete(force=True)
        print(f"Successfully deleted engine: {eng_id}")
    except Exception as e:
        print(f"Failed to delete {eng_id}: {e}")
