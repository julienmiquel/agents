import os
import vertexai
from google.cloud import geminidataanalytics
from dotenv import load_dotenv
load_dotenv()

BILLING_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

vertexai.init(project=BILLING_PROJECT, location="europe-west1")

data_chat_client = geminidataanalytics.DataChatServiceClient()

# Define 4 tables
ref1 = geminidataanalytics.BigQueryTableReference()
ref1.project_id = "bigquery-public-data"
ref1.dataset_id = "thelook_ecommerce"
ref1.table_id = "events"
ref1.schema = geminidataanalytics.Schema(description="website activity event log")

ref2 = geminidataanalytics.BigQueryTableReference()
ref2.project_id = "bigquery-public-data"
ref2.dataset_id = "thelook_ecommerce"
ref2.table_id = "order_items"
ref2.schema = geminidataanalytics.Schema(description="financial transactions, purchases, refunds, orders line items")

ref3 = geminidataanalytics.BigQueryTableReference()
ref3.project_id = "bigquery-public-data"
ref3.dataset_id = "thelook_ecommerce"
ref3.table_id = "products"
ref3.schema = geminidataanalytics.Schema(description="product catalog details")

ref4 = geminidataanalytics.BigQueryTableReference()
ref4.project_id = "bigquery-public-data"
ref4.dataset_id = "thelook_ecommerce"
ref4.table_id = "users"
ref4.schema = geminidataanalytics.Schema(description="customer demographic information")

datasource_references = geminidataanalytics.DatasourceReferences()
datasource_references.bq.table_references = [ref1, ref2, ref3, ref4]

inline_context = geminidataanalytics.Context()
inline_context.datasource_references = datasource_references
inline_context.options.analysis.python.enabled = True

messages = [geminidataanalytics.Message()]
messages[0].user_message.text = "Show the top 3 categories by total sales revenue"

chat_request = geminidataanalytics.ChatRequest(
    parent=f"projects/{BILLING_PROJECT}/locations/{LOCATION}",
    messages=messages,
    inline_context=inline_context
)

try:
    chat_response_stream = data_chat_client.chat(request=chat_request)
    table_found = False
    for event in chat_response_stream:
        if hasattr(event, 'system_message') and hasattr(event.system_message, 'table') and event.system_message.table:
            table_found = True
            table = event.system_message.table
            print("Columns:")
            cols = [col.name for col in table.columns]
            print(cols)
            
            print("\nRows:")
            for row_idx, row in enumerate(table.rows):
                row_data = []
                for cell in row.values:
                    # Let's inspect fields of cell
                    fields = [f[0].name for f in cell.ListFields()]
                    field_name = fields[0] if fields else None
                    val = getattr(cell, field_name) if field_name else None
                    row_data.append(val)
                print(f"Row {row_idx}:", dict(zip(cols, row_data)))
    if not table_found:
        print("No table event found in the stream.")
except Exception as e:
    print("Error:", e)
