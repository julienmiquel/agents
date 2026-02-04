import os
import pytest
from vertexai.preview import reasoning_engines
import vertexai
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
# This environment variable will be set manually or via shell before running the test
AGENT_ENGINE_ID = os.getenv(
    "AGENT_ENGINE_RESOURCE_ID",
    "projects/59602385614/locations/europe-west1/reasoningEngines/3955690993017159680"
)

@pytest.mark.skipif(not AGENT_ENGINE_ID, reason="AGENT_ENGINE_RESOURCE_ID not set")
def test_remote_deployment():
    """Verifies the deployed agent on Agent Engine."""
    print(f"\nConnecting to Agent Engine: {AGENT_ENGINE_ID} in {PROJECT_ID}/{LOCATION}")
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    remote_agent = reasoning_engines.ReasoningEngine(AGENT_ENGINE_ID)
    
    # Test 1: Generate an Image
    prompt = "A futuristic city on Mars, pixel art style"
    print(f"Test 1: Querying agent with: '{prompt}'")
    
    response = remote_agent.query(input=prompt)
    print(f"Response: {response}")
    
    # Check if response contains expected text (e.g. success message or path)
    assert response is not None
    # Depending on agent output format, we might look for "generated successfully" or similar
    # The agent returns a string msg.
    assert "generated successfully" in str(response) or "saved as artifact" in str(response)

    print("Remote deployment verified successfully.")
