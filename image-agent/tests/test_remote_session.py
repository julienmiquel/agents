import os
import google.adk as adk
from google.adk.sessions import VertexAiSessionService
from google.genai import types
from agent import root_agent
from dotenv import load_dotenv

load_dotenv()

# Configuration from .env
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
# Use the latest deployed engine ID (can be set via env or updated here)
AGENT_ENGINE_ID = os.getenv(
    "AGENT_ENGINE_RESOURCE_ID", 
    "projects/1008225662928/locations/europe-west1/reasoningEngines/2509850794677764096"
)

app_name = "image-agent"
user_id = "test-user-001"
session_id = "session-unique-id-123"

# Create the ADK runner with VertexAiSessionService
session_service = VertexAiSessionService(
    project=PROJECT_ID,
    location=LOCATION,
    reasoning_engine_id=AGENT_ENGINE_ID
)

runner = adk.Runner(
    agent=root_agent,
    app_name=app_name,
    session_service=session_service
)

# Helper method to send query to the runner
def call_agent(query, session_id, user_id):
    print(f"\n--- User ({user_id}, {session_id}): {query} ---")
    content = types.Content(role='user', parts=[types.Part(text=query)])
    events = runner.run(
        user_id=user_id, 
        session_id=session_id, 
        new_message=content
    )

    for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)
            return final_response

if __name__ == "__main__":
    print(f"Starting Session Test with Engine: {AGENT_ENGINE_ID}")
    
    # Message 1: Generate an image
    call_agent("Generate a high-quality image of a coffee shop on Mars.", session_id, user_id)
    
    # Message 2: Request an upscale (testing context memory)
    call_agent("Now upscale it to 4K.", session_id, user_id)
