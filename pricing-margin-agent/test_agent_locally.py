"""Test script to run the Smile Pricing & Margin Agent locally using AgentEngineApp."""
import os
import sys
import asyncio

# Add current directory to Python path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agent_engine_app import agent_engine
from google.adk.events.event import Event

async def run_test():
    print("=== Initializing Local Session with Smile Pricing & Margin Agent ===")
    
    # Set up the agent engine
    agent_engine.set_up()
    
    user_id = "test_business_manager"
    
    # Create session explicitly to keep history across turns using public async_create_session method.
    # Do NOT pass app_name as it is automatically set by AdkApp template.
    session = await agent_engine.async_create_session(
        user_id=user_id
    )
    session_id = session.id
    print(f"Created local test session: {session_id}")
    
    # Turn 1
    user_input_1 = "I need to price a Senior DevOps Engineer for a 6-month mission at Decathlon in Lille."
    print(f"\nUser: {user_input_1}")
    
    print("\nAgent: ", end="", flush=True)
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
    
    # Turn 2
    user_input_2 = "The consultant's annual salary is €65k and they are senior with 5 years of experience."
    print(f"\nUser: {user_input_2}")
    
    print("\nAgent: ", end="", flush=True)
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

    # Turn 3
    user_input_3 = "Let's propose a TJM of €665. How does the margin look? Will Decathlon accept it?"
    print(f"\nUser: {user_input_3}")
    
    print("\nAgent: ", end="", flush=True)
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

if __name__ == "__main__":
    asyncio.run(run_test())
