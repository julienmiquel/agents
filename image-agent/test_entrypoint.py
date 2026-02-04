
import sys
import os

# Mock the environment to resemble Vertex AI
os.environ["PROJECT_ID"] = "ml-demo-384110"

print("Importing deployment_entrypoint...")
try:
    import deployment_entrypoint
    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print(f"Agent object type: {type(deployment_entrypoint.agent)}")


print("Inspecting root_agent internals...")
try:
    from agent import root_agent
    print(f"Type: {type(root_agent)}")
    print(f"Is Pydantic? {hasattr(root_agent, 'model_dump')}")
    print(f"Has __dict__? {hasattr(root_agent, '__dict__')}")
    print(f"Has __slots__? {hasattr(root_agent, '__slots__')}")
    
    # Try Class Swapping
    print("Attempting Class Swapping...")
    OriginalClass = root_agent.__class__
    
    class PatchedAgent(OriginalClass):
        @property
        def agent_framework(self):
            return "adk"

    try:
        root_agent.__class__ = PatchedAgent
        print("Class swapped.")
        print(f"New type: {type(root_agent)}")
        
        if root_agent.agent_framework == "adk":
             print("SUCCESS: Attribute accessible via class swap.")
        else:
             print("FAILURE: Attribute mismatch after swap.")
             
        # Verify set_up would work (mocking it if needed? No, just check attr)
        
    except Exception as e:
        print(f"Class swap failed: {e}")
        sys.exit(1)

except Exception as e:
    print(f"Outer inspection failed: {e}")
    sys.exit(1)

print("Entrypoint check passed.")
