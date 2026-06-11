import os
import sys
import uuid
import json
import asyncio
import importlib
from typing import Optional, Dict, List, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn

from google.genai import types
from google.adk.apps import App
from google.adk.agents.base_agent import BaseAgent
from google.adk.runners import Runner
from google.adk.runners import RunConfig
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.utils.context_utils import Aclosing

# Constants
WORKSPACE_DIR = "/Users/julienmiquel/dev/agents"
PORT = 8001

app = FastAPI(title="ADK Agents Explorer & Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from unittest.mock import MagicMock

class MockA2uiSchemaManager:
    def __init__(self, *args, **kwargs):
        pass
    def generate_system_prompt(self, role_description="", workflow_description="", *args, **kwargs):
        return f"{role_description}\n\n{workflow_description}"

class MockBasicCatalog:
    @staticmethod
    def get_config(*args, **kwargs):
        return {}

def setup_a2ui_mocks():
    sys.modules['a2ui'] = MagicMock()
    sys.modules['a2ui.schema'] = MagicMock()
    a2ui_schema_manager = MagicMock()
    a2ui_schema_manager.A2uiSchemaManager = MockA2uiSchemaManager
    sys.modules['a2ui.schema.manager'] = a2ui_schema_manager

    sys.modules['a2ui.basic_catalog'] = MagicMock()
    a2ui_basic_catalog_provider = MagicMock()
    a2ui_basic_catalog_provider.BasicCatalog = MockBasicCatalog
    sys.modules['a2ui.basic_catalog.provider'] = a2ui_basic_catalog_provider

# Registry of loaded agents
loaded_agents: Dict[str, Any] = {}
# Registry of runner instances per agent
runners: Dict[str, Runner] = {}
# Active session storage in-memory for simpler retrieval (sessionId -> agentId)
active_sessions: Dict[str, str] = {}

def discover_and_load_agents():
    print("=== Scanning for ADK Agents ===")
    for item in os.listdir(WORKSPACE_DIR):
        item_path = os.path.join(WORKSPACE_DIR, item)
        if os.path.isdir(item_path) and not item.startswith("."):
            agent_file = os.path.join(item_path, "app", "agent.py")
            if os.path.exists(agent_file):
                # Import module dynamically
                orig_sys_path = list(sys.path)
                sys.path.insert(0, item_path)
                try:
                    # Load .env file for agent if present
                    dotenv_path = os.path.join(item_path, ".env")
                    if os.path.exists(dotenv_path):
                        from dotenv import load_dotenv
                        load_dotenv(dotenv_path, override=True)
                        
                    # Clear sys.modules cache to prevent cross-agent import contamination
                    for sys_mod_name, sys_mod in list(sys.modules.items()):
                        # Protect the runner server itself and the main entrypoint from deletion
                        if sys_mod_name in ['serve', '__main__'] or sys_mod_name.startswith('serve.'):
                            continue
                            
                        # Check if module path is in workspace but NOT in virtualenv (.venv)
                        in_workspace = False
                        if hasattr(sys_mod, "__file__") and sys_mod.__file__:
                            file_path = sys_mod.__file__
                            in_workspace = file_path.startswith(WORKSPACE_DIR) and not file_path.startswith(os.path.join(WORKSPACE_DIR, ".venv"))
                        
                        is_top_level_conflict = sys_mod_name in ['app', 'tools', 'a2ui', 'prompt_builder', 'app_utils'] or \
                                                sys_mod_name.startswith('app.') or sys_mod_name.startswith('tools.') or \
                                                sys_mod_name.startswith('a2ui.') or sys_mod_name.startswith('prompt_builder.') or \
                                                sys_mod_name.startswith('app_utils.')
                        
                        if in_workspace or is_top_level_conflict:
                            del sys.modules[sys_mod_name]
                            
                    setup_a2ui_mocks()
                    module = importlib.import_module("app.agent")
                    print(f"DEBUG LOADED: {item} -> module: {module} from file: {getattr(module, '__file__', 'None')}")
                    if hasattr(module, "app") and isinstance(module.app, App):
                        loaded_agents[item] = module.app
                        print(f"Loaded App '{item}': {module.app.name} (ID: {id(module.app)}) (RootAgent ID: {id(module.app.root_agent)})")
                    elif hasattr(module, "root_agent") and isinstance(module.root_agent, BaseAgent):
                        loaded_agents[item] = module.root_agent
                        print(f"Loaded Agent '{item}': {module.root_agent.name} (ID: {id(module.root_agent)})")
                    else:
                        print(f"Skipping '{item}': No App or BaseAgent found in app.agent")
                except Exception as e:
                    print(f"Failed to load agent '{item}': {e}")
                finally:
                    sys.path = orig_sys_path

# Load agents at startup
discover_and_load_agents()

async def get_or_create_runner(agent_id: str) -> Runner:
    if agent_id not in loaded_agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
    if agent_id in runners:
        return runners[agent_id]
        
    setup_a2ui_mocks()
    agent_or_app = loaded_agents[agent_id]
    
    # Setup env for runner execution
    agent_dir = os.path.join(WORKSPACE_DIR, agent_id)
    dotenv_path = os.path.join(agent_dir, ".env")
    if os.path.exists(dotenv_path):
        from dotenv import load_dotenv
        load_dotenv(dotenv_path, override=True)
        
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    if isinstance(agent_or_app, App):
        runner = Runner(
            app=agent_or_app,
            session_service=session_service,
            artifact_service=artifact_service
        )
    else:
        runner = Runner(
            app_name=agent_id,
            agent=agent_or_app,
            session_service=session_service,
            artifact_service=artifact_service
        )
    runners[agent_id] = runner
    return runner

@app.get("/api/agents")
async def list_agents():
    agents_list = []
    for key, value in loaded_agents.items():
        if isinstance(value, App):
            raw_name = value.root_agent.name
            description = value.root_agent.description or value.root_agent.instruction[:100]
        else:
            raw_name = value.name
            description = value.description or value.instruction[:100]
            
        name = raw_name.replace('_', ' ').replace('-', ' ').title()
            
        agents_list.append({
            "id": key,
            "name": name,
            "description": description
        })
    return agents_list

@app.post("/api/agents/{agent_id}/sessions")
async def create_session(agent_id: str):
    runner = await get_or_create_runner(agent_id)
    session_id = str(uuid.uuid4())
    user_id = "default_user"
    
    await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id,
        state={}
    )
    active_sessions[session_id] = agent_id
    return {"sessionId": session_id, "agentId": agent_id}

@app.post("/api/chat/stream/{agent_id}")
async def stream_chat(
    agent_id: str,
    message: str = Body(None),
    sessionId: Optional[str] = Body(None),
    invocationId: Optional[str] = Body(None),
    confirmed: Optional[bool] = Body(None),
    funcCallId: Optional[str] = Body(None),
    payload: Optional[str] = Body(None)
):
    runner = await get_or_create_runner(agent_id)
    user_id = "default_user"
    
    if not sessionId:
        sessionId = str(uuid.uuid4())
        
    session = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=sessionId
    )
    if not session:
        session = await runner.session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
            session_id=sessionId,
            state={}
        )
        
    active_sessions[sessionId] = agent_id

    # Construct the input message based on whether it is a standard message or HITL tool confirmation response
    new_message = None
    if confirmed is not None and funcCallId:
        # Tool confirmation response
        # It needs to be wrapped as types.Content with a function response part
        tool_response_payload = {
            "confirmed": confirmed,
            "payload": payload or ""
        }
        part = types.Part(
            function_response=types.FunctionResponse(
                name="adk_request_confirmation",
                id=funcCallId,
                response={"response": json.dumps(tool_response_payload)}
            )
        )
        new_message = types.Content(role="user", parts=[part])
    else:
        # Normal user message
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        new_message = types.Content(role="user", parts=[types.Part(text=message)])

    async def event_generator():
        try:
            # We run the agent in streaming mode
            async with Aclosing(
                runner.run_async(
                    user_id=user_id,
                    session_id=sessionId,
                    new_message=new_message,
                    invocation_id=invocationId,
                    run_config=RunConfig(streaming_mode="sse")
                )
            ) as agen:
                async for event in agen:
                    # Filter and extract relevant event info
                    event_data = {
                        "id": event.id,
                        "invocationId": event.invocation_id,
                        "author": event.author,
                        "timestamp": event.timestamp,
                        "partial": event.partial,
                    }
                    
                    # Text content extraction
                    text_parts = []
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                text_parts.append(part.text)
                    if text_parts:
                        event_data["text"] = "".join(text_parts)
                        
                    # Function calls extraction (checking for HITL confirmations)
                    func_calls = []
                    for fc in event.get_function_calls():
                        func_calls.append({
                            "id": fc.id,
                            "name": fc.name,
                            "args": fc.args
                        })
                    if func_calls:
                        event_data["functionCalls"] = func_calls
                        
                    # Function responses
                    func_responses = []
                    for fr in event.get_function_responses():
                        func_responses.append({
                            "id": fr.id,
                            "name": fr.name,
                            "response": fr.response
                        })
                    if func_responses:
                        event_data["functionResponses"] = func_responses
                        
                    # Check for tool confirmations requested
                    confirmations = {}
                    if event.actions and event.actions.requested_tool_confirmations:
                        for fc_id, confirmation in event.actions.requested_tool_confirmations.items():
                            confirmations[fc_id] = {
                                "hint": confirmation.hint,
                                "confirmed": confirmation.confirmed,
                                "payload": confirmation.payload
                            }
                    if confirmations:
                        event_data["confirmations"] = confirmations
                        
                    # Check for other actions (like state_delta, transfer_to_agent)
                    if event.actions:
                        if event.actions.state_delta:
                            event_data["stateDelta"] = event.actions.state_delta
                        if event.actions.transfer_to_agent:
                            event_data["transferToAgent"] = event.actions.transfer_to_agent

                    yield f"data: {json.dumps(event_data)}\n\n"
                    
        except Exception as e:
            print(f"Error in running session {sessionId}: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Serve visual artifacts locally
@app.get("/api/artifacts/{filename}")
async def get_artifact(filename: str):
    # Search for filename in the workspace (matplotlib graph viz outputs files directly inWORKSPACE_DIR)
    local_path = os.path.join(WORKSPACE_DIR, filename)
    if os.path.exists(local_path):
        from fastapi.responses import FileResponse
        return FileResponse(local_path)
    
    # Also search subdirectories
    for item in os.listdir(WORKSPACE_DIR):
        sub_path = os.path.join(WORKSPACE_DIR, item, filename)
        if os.path.exists(sub_path):
            from fastapi.responses import FileResponse
            return FileResponse(sub_path)
            
    # Try searching the current process directory
    cwd_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(cwd_path):
        from fastapi.responses import FileResponse
        return FileResponse(cwd_path)
        
    raise HTTPException(status_code=404, detail="Artifact not found")

# Expose Static Web App
app.mount("/", StaticFiles(directory="web_ui", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("serve:app", host="127.0.0.1", port=PORT, reload=True)
