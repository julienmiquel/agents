"""Test script to run the Antigravity Harness & SDK Specialist Agent locally using AgentEngineApp."""
import os
import sys
import asyncio

# Add current directory to Python path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agent_engine_app import agent_engine
from google.adk.events.event import Event

async def run_test():
    print("=== Initializing Local Session with Antigravity Harness & SDK Specialist Agent ===")
    
    # Set up the agent engine
    agent_engine.set_up()
    
    user_id = "test_developer_julien"
    
    # Create session explicitly using public async_create_session method
    session = await agent_engine.async_create_session(
        user_id=user_id
    )
    session_id = session.get("id") if isinstance(session, dict) else session.id
    print(f"Created local test session: {session_id}")
    
    # Turn 1: Ask for guidelines comparison (should trigger get_architecture_guidelines)
    user_input_1 = "Bonjour, je suis Julien. Peux-tu m'expliquer la différence entre l'API Interactions et le SDK Python pour Antigravity ?"
    print(f"\n[USER]: {user_input_1}")
    
    print("\n[AGENT]: ", end="", flush=True)
    async for event_dict in agent_engine.async_stream_query(
        message=user_input_1, 
        user_id=user_id, 
        session_id=session_id
    ):
        event = Event.model_validate(event_dict)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()
    
    # Turn 2: Request hooks sample snippet (should trigger generate_antigravity_snippet)
    user_input_2 = "C'est très clair. Donne-moi un exemple de code pour configurer les hooks JSON avec le SDK Antigravity."
    print(f"\n[USER]: {user_input_2}")
    
    print("\n[AGENT]: ", end="", flush=True)
    async for event_dict in agent_engine.async_stream_query(
        message=user_input_2, 
        user_id=user_id, 
        session_id=session_id
    ):
        event = Event.model_validate(event_dict)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()

    # Turn 3: Submit code for debugging (should trigger validate_integration_code)
    user_input_3 = (
        "Super. Peux-tu analyser ce code pour moi et me dire s'il y a des erreurs ?\n\n"
        "```python\n"
        "from google import genai\n\n"
        "client = genai.Client()\n\n"
        "interaction = client.interactions.create(\n"
        "    agent='antigravity-preview-05-2026',\n"
        "    input='Lis Hacker News',\n"
        "    temperature=0.7,\n"
        "    environment='remote'\n"
        ")\n"
        "```"
    )
    print(f"\n[USER]: {user_input_3}")
    
    print("\n[AGENT]: ", end="", flush=True)
    async for event_dict in agent_engine.async_stream_query(
        message=user_input_3, 
        user_id=user_id, 
        session_id=session_id
    ):
        event = Event.model_validate(event_dict)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()

    # Turn 4: Submit corrected code (should trigger validate_integration_code -> OK!)
    user_input_4 = (
        "Merci, voici le code corrigé avec extra_body. Est-il correct maintenant ?\n\n"
        "```python\n"
        "from google import genai\n\n"
        "client = genai.Client()\n\n"
        "interaction = client.interactions.create(\n"
        "    agent='antigravity-preview-05-2026',\n"
        "    input='Lis Hacker News',\n"
        "    extra_body={'environment': 'remote'}\n"
        ")\n"
        "```"
    )
    print(f"\n[USER]: {user_input_4}")
    
    print("\n[AGENT]: ", end="", flush=True)
    async for event_dict in agent_engine.async_stream_query(
        message=user_input_4, 
        user_id=user_id, 
        session_id=session_id
    ):
        event = Event.model_validate(event_dict)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(run_test())
