"""Module defining the BigQuery Agent (CA Bridge Agent) and its tools."""
import os
import sys
import traceback

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.cloud import geminidataanalytics

# Load environment variables from .env if present
load_dotenv()

# Configuration
BILLING_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- Define the Bridge Tool ---
def query_conversational_analytics_api(prompt: str) -> str:
    """
    Queries the Google Trends Conversational Analytics API to analyze datasets in BigQuery.
    Use this tool when you need to answer questions about rising search terms or top terms in Google Trends.

    Args:
        prompt: The natural language question to ask the Trends Data Agent.

    Returns:
        The text response from the Data Agent.
    """
    print(f"\n[Bridge Tool] Intercepted Prompt: {prompt}")
    
    try:
        data_chat_client = geminidataanalytics.DataChatServiceClient()
    except Exception as e:
        return f"❌ Error initializing CA client: {e}\n{traceback.format_exc()}"

    # Define Data Sources (Stateless style with inline context)
    ref1 = geminidataanalytics.BigQueryTableReference()
    ref1.project_id = "bigquery-public-data"
    ref1.dataset_id = "google_trends"
    ref1.table_id = "international_top_rising_terms"
    ref1.schema = geminidataanalytics.Schema(description="rapidly increasing search terms popularity")

    ref2 = geminidataanalytics.BigQueryTableReference()
    ref2.project_id = "bigquery-public-data"
    ref2.dataset_id = "google_trends"
    ref2.table_id = "international_top_terms"
    ref2.schema = geminidataanalytics.Schema(description="most searched terms overall")

    datasource_references = geminidataanalytics.DatasourceReferences()
    datasource_references.bq.table_references = [ref1, ref2]

    inline_context = geminidataanalytics.Context()
    inline_context.system_instruction = "You are a trends analysis data agent. Help users analyze Google Trends in BigQuery."
    inline_context.datasource_references = datasource_references
    inline_context.options.analysis.python.enabled = True

    messages = [geminidataanalytics.Message()]
    messages[0].user_message.text = prompt

    chat_request = geminidataanalytics.ChatRequest(
        parent=f"projects/{BILLING_PROJECT}/locations/{LOCATION}",
        messages=messages,
        inline_context=inline_context
    )

    print("[Bridge Tool] Sending request to CA API...")
    try:
        chat_response_stream = data_chat_client.chat(request=chat_request)
        final_answer = ""
        for event in chat_response_stream:
            if hasattr(event, 'system_message'):
                m = event.system_message
                if hasattr(m, 'text'):
                     if hasattr(m.text, 'text_type') and m.text.text_type == geminidataanalytics.TextMessage.TextType.FINAL_RESPONSE:
                          final_answer += "".join(m.text.parts)
                elif hasattr(m, 'text_type') and m.text_type == geminidataanalytics.TextMessage.TextType.FINAL_RESPONSE:
                     final_answer += "".join(m.parts)
                        
        if not final_answer:
            return "✅ Tool success, but wait, check logs for output."
            
        return final_answer
        
    except Exception as e:
        return f"❌ Error during CA API chat: {e}\n{traceback.format_exc()}"

# --- Define the ADK Agent ---
root_agent = Agent(
    name="ca_bridge_agent",
    description="Google Trends analytics agent - answers questions about trends data from BigQuery.",
    model=Gemini(
        model=MODEL_NAME,
        retry_options=types.HttpRetryOptions(attempts=3, 
            http_status_codes=[408, 429, 500, 502, 503, 504],
        ), 
    ), 
    instruction="""Tu es un analyste de données expert pour Google Trends.
Ton rôle est de fournir des réponses claires, structurées et purement analytiques.
Tu utilises l'outil 'query_conversational_analytics_api' pour analyser les données des tendances de recherche.

### PROCESSUS :
1. Appelle l'outil 'query_conversational_analytics_api' avec la question exacte de l'utilisateur.
2. L'outil renvoie un rapport ou des données à analyser.

### REGLES DE REPONSE (CRITIQUE) :
- **LANGUE** : Réponds TOUJOURS dans la langue utilisée par l'utilisateur (Français ou Anglais).
- **CONTENU UTILE UNIQUEMENT** : Ne conserve que les parties intéressantes (Résumé, Tableaux, Insights).
- **AUCUN PREAMBULE** : Ne commence jamais par "Voici l'analyse", "Selon les données", ou "D'après ma recherche".
- **AUCUNE POLITESSE FINALE** : Ne termine jamais par "J'espère que cela aide", "N'hésitez pas à poser d'autres questions".
- **FORMATAGE** : Assure-toi que les tableaux Markdown sont bien espacés et que les titres (###) ont bien un espace après.
- **ERREUR** : Si l'outil échoue, indique simplement que l'analyse est indisponible pour le moment.

En résumé : Ta réponse doit ressembler à un rapport professionnel brut, sans fioritures et sans métadonnées inutiles.
""",
    tools=[query_conversational_analytics_api],
    planner=BuiltInPlanner(thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=256))
)

app = App(root_agent=root_agent, name="app")
