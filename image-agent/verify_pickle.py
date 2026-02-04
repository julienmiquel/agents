import cloudpickle
import sys
import os

# Ensure cwd is in path
sys.path.append(os.getcwd())

from deployment_entrypoint import agent

print("Attempting to pickle agent...")
try:
    dumped = cloudpickle.dumps(agent)
    print(f"Successfully pickled agent. Size: {len(dumped)} bytes")
    
    loaded = cloudpickle.loads(dumped)
    print("Successfully unpickled agent.")
    
    if hasattr(loaded, "agent_framework"):
        print(f"Verification Check: agent_framework={loaded.agent_framework}")
    else:
        print("Verification Check: FAILED. agent_framework attribute missing after unpickle.")
        sys.exit(1)
    
except Exception as e:
    print(f"Pickling failed: {e}")
    sys.exit(1)
