import os
import time
import vertexai
from dotenv import load_dotenv
load_dotenv()

project = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

vertexai.init(project=project, location=location)

from vertexai import agent_engines

engine_id = "projects/1008225662928/locations/europe-west1/reasoningEngines/5398293922684403712"

print(f"Waiting for engine {engine_id} to propagate...")
for i in range(12): # 12 * 15s = 3 minutes
    try:
        engine = agent_engines.get(engine_id)
        print(f"✅ Success! Engine retrieved after {i*15} seconds.")
        print(engine)
        
        # Verify query requesting a chart based on real database data
        prompt = "fait un graphique de visualisation des ventes d'alcool par produit en 2026"
        print("Sending verify prompt...")
        response_stream = engine.stream_query(message=prompt, user_id="test_user")
        print("--- Response ---")
        for chunk in response_stream:
            print(chunk)
        print("--- End Response ---")
        break
    except Exception as e:
        print(f"[{i*15}s] Not found yet: {e}")
        time.sleep(15)
