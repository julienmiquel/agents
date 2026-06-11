"""Module defining the Knowledge Graph Agent and its tools."""
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.planners import BuiltInPlanner
from google.genai import types

from app.tools.knowledge_graph import extract_knowledge_graph
from app.tools.visualize_graph import visualize_knowledge_graph

load_dotenv()

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# Define the shared model configuration
shared_model = Gemini(
    model=MODEL_NAME,
    retry_options=types.HttpRetryOptions(
        attempts=3, 
        http_status_codes=[408, 429, 500, 502, 503, 504],
    ), 
)

# 1. Extraction Agent
extraction_instruction = (
    "You are a Knowledge Graph Extraction Agent.\n"
    "Your role is to analyze text documents and extract entities and their relationships, "
    "forming a structured knowledge graph.\n"
    "IMPORTANT: If you receive a document (e.g., PDF) or are asked to read a file, "
    "do NOT apologize or say you cannot access files. You natively have the ability to read them as part of your multimodal context. "
    "Simply read the text from the provided document and pass it directly as the `text` argument to the 'extract_knowledge_graph' tool.\n"
    "You can customize the data schema and instructions if specific entities "
    "(like PERSON, ANIMAL, ORGANIZATION) or specific relationships are requested.\n"
    "Return the structured entities and relationships to the caller."
)

extraction_agent = Agent(
    name="extraction_agent",
    description="Specialized agent for extracting structured knowledge graphs (entities and relationships) from text documents and PDFs.",
    model=shared_model,
    instruction=extraction_instruction,
    tools=[extract_knowledge_graph],
    planner=BuiltInPlanner(thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=256))
)

# 2. Visualization Agent
visualization_instruction = (
    "You are a Knowledge Graph Visualization Agent.\n"
    "Your role is to take structured knowledge graph data (entities and relationships) "
    "and generate visual representations, such as images or animations.\n"
    "Use the 'visualize_knowledge_graph' tool to create these visualizations. "
    "Ensure you pass the correct list of entities and relationships to the tool. "
    "Return the resulting file path or confirmation of the generated visualization to the caller."
)

visualization_agent = Agent(
    name="visualization_agent",
    description="Specialized agent for generating visual representations (images, animations) from structured knowledge graph data.",
    model=shared_model,
    instruction=visualization_instruction,
    tools=[visualize_knowledge_graph],
    planner=BuiltInPlanner(thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=256))
)

# 3. Root Orchestrator Agent
orchestrator_instruction = (
    "You are the Knowledge Graph Orchestrator Agent, the main point of contact for the user.\n"
    "Your role is to coordinate specialized sub-agents to fulfill user requests related to knowledge graphs.\n\n"
    "IMPORTANT: If you receive a document (e.g., PDF) or are asked to read a file, do NOT apologize or say you cannot access files. "
    "You natively have the ability to process them as part of your multimodal context.\n\n"
    "WORKFLOW:\n"
    "1. If the user provides a document (PDF, text, etc.) or asks to build a knowledge graph, delegate the task to the `extraction_agent` to extract the entities and relationships. Present the extracted graph clearly to the user.\n"
    "2. If the user asks for a visualization, image, or animation of the knowledge graph, delegate the extracted entities and relationships data to the `visualization_agent` to generate it. Provide the resulting file path to the user.\n"
    "3. You can chain these operations. For example, if a user asks to extract a graph AND visualize it in one request, first call the `extraction_agent`, then pass its output to the `visualization_agent`.\n\n"
    "Always synthesize the final results clearly for the user, summarizing key findings and providing paths to generated visualizations."
)

root_agent = Agent(
    name="knowledge_graph_orchestrator",
    description="Main orchestrator agent that delegates knowledge graph extraction and visualization tasks.",
    model=shared_model,
    instruction=orchestrator_instruction,
    sub_agents=[extraction_agent, visualization_agent],
    planner=BuiltInPlanner(thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=256))
)

app = App(root_agent=root_agent, name="app")
