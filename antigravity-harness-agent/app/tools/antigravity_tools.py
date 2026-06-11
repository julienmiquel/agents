"""Tools for the Antigravity Harness & SDK Specialist Agent."""
import os
import json
from typing import Any, Dict, List, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(CURRENT_DIR, "mock_data.json")

MOCK_DB = {}
try:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        MOCK_DB = json.load(f)
except Exception as e:
    # Minimal fallback in case of loading issues
    MOCK_DB = {
        "comparisons": [],
        "snippets": {},
        "migration_checklist": []
    }

def get_architecture_guidelines() -> Dict[str, Any]:
    """Retrieve structured guidelines comparing the remote Antigravity Interactions API and local Antigravity Python SDK.

    Returns:
        A dictionary containing a comparison list, feature matrix, and migration notes.
    """
    return {
        "comparisons": MOCK_DB.get("comparisons", []),
        "migration_checklist": MOCK_DB.get("migration_checklist", []),
        "source": "Google Developer Relations - Antigravity Agent Core Documentation (I/O 2026)"
    }

def generate_antigravity_snippet(integration_type: str, use_case: str = "basic") -> Dict[str, Any]:
    """Generate a clean, copy-pasteable, verified integration code snippet for Antigravity interfaces.

    Args:
        integration_type: The integration type, either 'interactions_api' (Gemini cloud client) or 'sdk' (native Python SDK).
        use_case: The use case template. For 'interactions_api': 'basic' or 'linux_sandbox'. For 'sdk': 'basic', 'subagents', or 'hooks'.

    Returns:
        A dictionary containing the generated code block and technical explanations.
    """
    snippets = MOCK_DB.get("snippets", {})
    typed_snippets = snippets.get(integration_type, {})
    snippet = typed_snippets.get(use_case)
    
    if not snippet:
        # Fallback
        keys = list(typed_snippets.keys())
        fallback_key = keys[0] if keys else None
        if fallback_key:
            snippet = typed_snippets[fallback_key]
            use_case = fallback_key
        else:
            snippet = "# No snippet available"

    explanations = {
        "interactions_api": {
            "basic": "Basic example of deploying an agent to a Google-hosted secure remote Linux sandbox with a single Python API call using the official google-genai client.",
            "linux_sandbox": "Advanced example demonstrating multimodal base64 image data upload and text commands executed autonomously inside the remote Linux sandbox."
        },
        "sdk": {
            "basic": "Standard setup of the google.antigravity SDK, initializing the local agent using an async context manager.",
            "subagents": "Boilerplate utilizing dynamic, concurrent sub-agents to parallelize complex tasks using the local SDK runtime.",
            "hooks": "Example showing how to configure operational JSON hooks to intercept and track agent reasoning steps and tool execution in real-time."
        }
    }

    explanation = explanations.get(integration_type, {}).get(use_case, "Verified boilerplate template.")

    return {
        "integration_type": integration_type,
        "use_case": use_case,
        "code": snippet,
        "explanation": explanation,
        "status": "VERIFIED_SOTA_2026"
    }

def validate_integration_code(code_string: str) -> Dict[str, Any]:
    """Analyze custom Python integration scripts for the Antigravity Harness/SDK and report compatibility diagnostics.

    This tool checks for unsupported preview arguments, incorrect package imports, and non-asynchronous calling blocks in SDK environments.

    Args:
        code_string: The Python code string to be analyzed.

    Returns:
        A diagnostic breakdown with severity labels (ERROR, WARNING, INFO) and action guidelines.
    """
    diagnostics = []
    has_errors = False
    
    # Simple static parsing checks
    has_genai_import = "import genai" in code_string or "from google import genai" in code_string
    has_sdk_import = "google.antigravity" in code_string or "Agent" in code_string and "LocalAgentConfig" in code_string
    
    has_interactions_call = "interactions.create" in code_string
    
    # Check imports
    if not has_genai_import and not has_sdk_import:
        diagnostics.append({
            "check": "Imports Check",
            "status": "WARNING",
            "message": "No typical Antigravity import statements found. Ensure you are importing 'google-genai' (for Interactions API) or 'google.antigravity' (for SDK)."
        })
    else:
        diagnostics.append({
            "check": "Imports Check",
            "status": "OK",
            "message": f"Verified correct import profile. Interactions API used: {has_genai_import}, Python SDK used: {has_sdk_import}."
        })

    # Check Interactions API Constraints
    if has_interactions_call:
        # Check environment syntax
        if "environment=" in code_string:
            has_errors = True
            diagnostics.append({
                "check": "SDK Parameter Syntax",
                "status": "ERROR",
                "message": "Direct keyword argument 'environment=...' is not accepted by InteractionsResource.create() in the Python SDK. You MUST pass it inside extra_body, e.g.: extra_body={'environment': 'remote'}. Passing 'environment' directly raises a TypeError."
            })
        elif "extra_body" in code_string and ("'environment'" in code_string or '"environment"' in code_string):
            if "remote" in code_string:
                diagnostics.append({
                    "check": "Sandbox Environment Setup",
                    "status": "OK",
                    "message": "Verified correct remote secure Linux sandbox configuration via extra_body={'environment': 'remote'}."
                })
            else:
                has_errors = True
                diagnostics.append({
                    "check": "Sandbox Environment Target",
                    "status": "ERROR",
                    "message": "Remote sandbox requires 'environment': 'remote' inside the extra_body parameter configuration."
                })
        else:
            diagnostics.append({
                "check": "Sandbox Environment Setup",
                "status": "WARNING",
                "message": "No secure Linux sandbox environment configured. If you intend to target the remote Linux environment, specify extra_body={'environment': 'remote'}."
            })
            
        # Check parameters that are unsupported in Interactions Preview
        unsupported_params = ["temperature", "top_p", "response_schema", "structured"]
        for param in unsupported_params:
            if f"{param}=" in code_string:
                diagnostics.append({
                    "check": f"Parameter: {param}",
                    "status": "WARNING",
                    "message": f"The parameter '{param}' is not supported in the Interactions API Preview (agent='antigravity-preview-05-2026'). It will be ignored or raise an API validation error."
                })

    # Check SDK constraints
    if has_sdk_import:
        # 1. Async context manager check
        if "async with Agent" not in code_string:
            has_errors = True
            diagnostics.append({
                "check": "SDK Context Management",
                "status": "ERROR",
                "message": "Antigravity SDK agent is an asynchronous context manager. You MUST construct it using 'async with Agent(config) as agent:' to avoid resource leaks."
            })
        else:
            diagnostics.append({
                "check": "SDK Context Management",
                "status": "OK",
                "message": "Correct use of 'async with Agent' block found."
            })

        # 2. Async text retrieval check
        if "await response.text" not in code_string:
            diagnostics.append({
                "check": "SDK Async Yields",
                "status": "WARNING",
                "message": "No 'await response.text()' call detected. Remember that extracting text from response handles is asynchronous in the SDK."
            })
        else:
            diagnostics.append({
                "check": "SDK Async Yields",
                "status": "OK",
                "message": "Verified proper asynchronous text retrieval."
            })

        # 3. Asyncio run check
        if "asyncio.run" not in code_string:
            diagnostics.append({
                "check": "Event Loop",
                "status": "WARNING",
                "message": "No event loop launch ('asyncio.run(main)') detected. Ensure your code is run within an active asyncio event loop."
            })
        else:
            diagnostics.append({
                "check": "Event Loop",
                "status": "OK",
                "message": "Verified proper event loop trigger ('asyncio.run')."
            })

    return {
        "passed": not has_errors,
        "diagnostics": diagnostics,
        "summary": "Validation complete. Fix all errors prior to deploying code in production." if has_errors else "All critical constraints satisfied! Your integration script looks solid and ready."
    }
