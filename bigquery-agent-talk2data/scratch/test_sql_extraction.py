import os
import vertexai
from google.cloud import geminidataanalytics
from dotenv import load_dotenv
load_dotenv()

BILLING_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

vertexai.init(project=BILLING_PROJECT, location="europe-west1")

data_chat_client = geminidataanalytics.DataChatServiceClient()

ref1 = geminidataanalytics.BigQueryTableReference()
ref1.project_id = "bigquery-public-data"
ref1.dataset_id = "iowa_liquor_sales"
ref1.table_id = "sales"
ref1.schema = geminidataanalytics.Schema(description="Iowa liquor sales transactions")

datasource_references = geminidataanalytics.DatasourceReferences()
datasource_references.bq.table_references = [ref1]

inline_context = geminidataanalytics.Context()
inline_context.datasource_references = datasource_references
inline_context.options.analysis.python.enabled = True

messages = [geminidataanalytics.Message()]
messages[0].user_message.text = "Liquor sales by product for the year 2026"

chat_request = geminidataanalytics.ChatRequest(
    parent=f"projects/{BILLING_PROJECT}/locations/{LOCATION}",
    messages=messages,
    inline_context=inline_context
)

try:
    chat_response_stream = data_chat_client.chat(request=chat_request)
    for idx, event in enumerate(chat_response_stream):
        if hasattr(event, 'system_message') and event.system_message:
            m = event.system_message
            fields = [f[0].name for f in m._pb.ListFields()]
            if "query" in fields:
                print(f"Found query in Event #{idx}!")
                print("Query type:", type(m.query))
                print("Query attributes:", dir(m.query))
                # Print SQL query string
                print("SQL:", getattr(m.query, "sql", None))
except Exception as e:
    print("Error:", e)
