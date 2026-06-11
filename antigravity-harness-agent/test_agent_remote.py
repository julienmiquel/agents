"""Test script to verify a remote sandbox session using the Antigravity Interactions API.

This script executes an autonomous loop inside an ephemeral, secure remote Linux sandbox
hosted in Google Cloud infrastructure, using the standard google-genai client.
"""
import os
import sys
from dotenv import load_dotenv

# Load workspace .env containing project coordinates and ADC setups
load_dotenv()

# We verify that we import google-genai correctly
try:
    from google import genai
except ImportError:
    print("❌ Error: google-genai package is not installed in the active environment.")
    print("Run '.venv/bin/pip install google-genai' to install dependencies.")
    sys.exit(1)

def run_remote_test():
    print("=== Launching Ephemeral Remote Sandbox Session (Interactions API) ===")
    
    # Verify GOOGLE_GENAI_USE_VERTEXAI is configured in the env, ensuring proper routing
    use_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI")
    if not use_vertex or use_vertex != "1":
        print("⚠️ Warning: GOOGLE_GENAI_USE_VERTEXAI is not set to '1' in the environment.")
        print("Defaulting to standard routing. Setting routing to Vertex AI is recommended.")
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    print(f"Targeting Project: {project_id}")
    print("Connecting API client...")
    
    client = genai.Client()
    
    # Remote query task to execute in the secure Linux sandbox
    remote_query = "Quels sont les fichiers dans le répertoire courant de la sandbox remote ?"
    print(f"\n[USER -> REMOTE SANDBOX]: '{remote_query}'")
    
    print("\n[PROVISIONING EPHEMERAL LINUX SANDBOX ON GOOGLE CLOUD...]")
    print("Running planning-action-observation loop autonomously...")
    
    import time
    max_retries = 15
    retry_delay = 20
    
    for attempt in range(1, max_retries + 1):
        try:
            interaction = client.interactions.create(
                agent="antigravity-preview-05-2026",
                input=remote_query,
                extra_body={"environment": "remote"},  # Activates the remote secure Linux sandbox
            )
            
            print("\n--- Remote Sandbox Output ---")
            print(interaction.output_text)
            print("-----------------------------")
            print("\n✔️ REMOTE SESSION SUCCESSFUL! Autonomous execution loop completed.")
            return
            
        except Exception as e:
            err_msg = str(e)
            if "Provisioning just started" in err_msg or "invalid_request" in err_msg:
                print(f"⏳ [Attempt {attempt}/{max_retries}] Ephemeral Linux Sandbox cold-start detected. Google Cloud is provisioning the secure container... Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"\n❌ Critical Error during remote execution: {e}")
                print("Make sure you are authenticated to GCP and have proper access to the Antigravity preview.")
                sys.exit(1)
                
    print(f"\n❌ Timeout: Remote sandbox environment did not finish provisioning after {max_retries * retry_delay}s.")
    sys.exit(1)

if __name__ == "__main__":
    run_remote_test()
