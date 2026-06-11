import os
import vertexai
from google.cloud import geminidataanalytics
from dotenv import load_dotenv
load_dotenv()

BILLING_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

vertexai.init(project=BILLING_PROJECT, location="europe-west1")

data_chat_client = geminidataanalytics.DataChatServiceClient()

# Minimal config to run a query
ref2 = geminidataanalytics.BigQueryTableReference()
ref2.project_id = "bigquery-public-data"
ref2.dataset_id = "thelook_ecommerce"
ref2.table_id = "order_items"
ref2.schema = geminidataanalytics.Schema(description="financial transactions, purchases, refunds, orders line items")

datasource_references = geminidataanalytics.DatasourceReferences()
datasource_references.bq.table_references = [ref2]

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

print("Sending chat request...")
try:
    chat_response_stream = data_chat_client.chat(request=chat_request)
    for idx, event in enumerate(chat_response_stream):
        print(f"\n--- Event #{idx} ---")
        print("Type:", type(event))
        print("Fields/Attributes in event:")
        for attr in dir(event):
            if attr.startswith('_'):
                continue
            try:
                val = getattr(event, attr)
                if val:
                    # If it's a message/object, print its attributes
                    print(f"  - {attr}: {type(val)}")
                    # Let's inspect system_message
                    if attr == "system_message":
                         print("    System Message details:")
                         for subattr in dir(val):
                              if subattr.startswith('_'):
                                   continue
                              subval = getattr(val, subattr)
                              if subval:
                                   print(f"      * {subattr}: {type(subval)}")
                                   if subattr == "text":
                                        print(f"        Text Parts: {getattr(subval, 'parts', None)}")
                                        print(f"        Text Type: {getattr(subval, 'text_type', None)}")
                                   elif subattr == "table":
                                        # Let's see how table is structured!
                                        table_val = subval
                                        print(f"        Table columns: {getattr(table_val, 'columns', None)}")
                                        # Print first few rows
                                        print(f"        Table rows preview: {list(getattr(table_val, 'rows', []))[:3]}")
                                   elif subattr == "chart":
                                        # Let's see if a chart object is returned!
                                        print(f"        Chart details: {subval}")
            except Exception as e:
                pass
except Exception as e:
    print("Error during CA chat:", e)
