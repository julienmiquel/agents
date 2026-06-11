import os
import sys
import vertexai
from dotenv import load_dotenv
load_dotenv()

vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
)

ENGINE_ID = "projects/ml-demo-384110/locations/europe-west1/reasoningEngines/7237451726951809024"

from vertexai import agent_engines
engine = agent_engines.get(ENGINE_ID)

prompt = "fait un graphique de visualisation des ventes d'alcool par produit en 2026"
print(f"Sending prompt to engine: {prompt}")

try:
    response_stream = engine.stream_query(message=prompt, user_id="test_user")
    print("\n--- Response ---")
    for chunk in response_stream:
        print(chunk)
    print("\n--- End Response ---")
except Exception as e:
    print(f"Error: {e}")
