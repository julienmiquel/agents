
import os
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
RESOURCE_ID = "3717759975301316608"

def test_telemetry():
    print(f"Connecting to agent: {RESOURCE_ID}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    try:
        agent = agent_engines.get(RESOURCE_ID)
        session_id = "telemetry-test-session"
        user_id = "telemetry-test-user"
        
        if hasattr(agent, "stream_query"):
            print("Using stream_query...")
            response_stream = agent.stream_query(query="Who are you?", session_id=session_id)
            for chunk in response_stream:
                print(f"Chunk: {chunk}")
        else:
             print("No query or stream_query method found!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_telemetry()
