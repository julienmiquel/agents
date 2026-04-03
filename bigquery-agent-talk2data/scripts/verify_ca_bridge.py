import os
import sys
import vertexai
from dotenv import load_dotenv
from vertexai.preview import reasoning_engines

# Load environment variables from .env
load_dotenv()

if not ENGINE_ID:
    print("❌ Error: REASONING_ENGINE environment variable is not set or empty in .env.")
    print("Please set it to the resource name of your deployed agent.")
    sys.exit(1)

print(f"Verifying Reasoning Engine: {ENGINE_ID}")

try:
    from vertexai import agent_engines
    engine = agent_engines.get(ENGINE_ID)
    print("Successfully retrieved reasoning engine (agent_engines.get).")
    
    print("Sending query: 'what are the latest trends ?'")
    response_stream = engine.stream_query(message="what are the latest trends ?", user_id="test_user")
    
    print("\n--- Response ---")
    for chunk in response_stream:
        # The chunk might be an event object, let's print it to see
        print(chunk)
    print("\n--- End Response ---")

except Exception as e:
    print(f"\n❌ Error during verification: {e}")
    sys.exit(1)
