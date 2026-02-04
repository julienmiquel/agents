import sys
import os

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from agent import root_agent

def verify_agent_structure():
    print(f"Agent Name: {root_agent.name}")
    # print(f"Model: {root_agent.model}") # Attribute might vary
    print(f"Tools: {[t.__name__ for t in root_agent.tools]}")
    
    assert root_agent.name == "image_agent"
    assert "generate_image" in [t.__name__ for t in root_agent.tools]
    assert "upscale_image" in [t.__name__ for t in root_agent.tools]
    
    print("Agent structure verification passed!")

if __name__ == "__main__":
    verify_agent_structure()
