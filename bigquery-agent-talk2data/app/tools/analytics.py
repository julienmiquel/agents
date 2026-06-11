import os
import traceback
import json
from google.cloud import geminidataanalytics

def _parse_table(table) -> str:
    """Parses a Table proto object into a JSON list of dictionaries."""
    try:
        cols = [col.name for col in table.columns]
        rows_list = []
        for row in table.rows:
            row_data = []
            for cell in row.values:
                # Find the set field in the cell proto
                fields = [f[0].name for f in cell.ListFields()]
                field_name = fields[0] if fields else None
                val = getattr(cell, field_name) if field_name else None
                row_data.append(val)
            rows_list.append(dict(zip(cols, row_data)))
        return json.dumps(rows_list, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Analytics] Error parsing table: {e}")
        return ""

def _execute_bq_query(sql_query: str) -> str:
    """Executes SQL directly in BigQuery and returns a JSON string of results."""
    try:
        from google.cloud import bigquery
        
        # Save original env variables to restore them later
        orig_cert = os.environ.get("GOOGLE_API_USE_CLIENT_CERTIFICATE")
        orig_mtls = os.environ.get("GOOGLE_API_USE_MTLS")
        
        # Disable mTLS locally to bypass ECP connection issue
        os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
        os.environ["GOOGLE_API_USE_MTLS"] = "never"
        
        client = bigquery.Client(project=BILLING_PROJECT)
        query_job = client.query(sql_query)
        results = query_job.result()
        
        rows_list = []
        for row in results:
            rows_list.append(dict(row.items()))
            
        # Restore original env variables
        if orig_cert is not None:
            os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = orig_cert
        else:
            os.environ.pop("GOOGLE_API_USE_CLIENT_CERTIFICATE", None)
            
        if orig_mtls is not None:
            os.environ["GOOGLE_API_USE_MTLS"] = orig_mtls
        else:
            os.environ.pop("GOOGLE_API_USE_MTLS", None)
            
        return json.dumps(rows_list, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Analytics] BQ fallback execution failed: {e}")
        return ""

# Configuration
BILLING_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

def query_look_ecommerce_api(prompt: str) -> str:
    """
    Queries the Conversational Analytics API to analyze the Look E-Commerce dataset in BigQuery.
    Use this tool when you need to answer questions about orders, products, users, or website events for the Look E-Commerce platform.

    Args:
        prompt: The natural language question to ask about the Look E-Commerce data.

    Returns:
        The text response from the Data Agent.
    """
    print(f"\n[Look E-Commerce Tool] Intercepted Prompt: {prompt}")
    
    try:
        data_chat_client = geminidataanalytics.DataChatServiceClient()
    except Exception as e:
        return f"❌ Error initializing CA client: {e}\n{traceback.format_exc()}"

    # Define Data Sources
    ref1 = geminidataanalytics.BigQueryTableReference()
    ref1.project_id = "bigquery-public-data"
    ref1.dataset_id = "thelook_ecommerce"
    ref1.table_id = "events"
    ref1.schema = geminidataanalytics.Schema(description="website activity event log (page views, product detail views, clicks, search)")

    ref2 = geminidataanalytics.BigQueryTableReference()
    ref2.project_id = "bigquery-public-data"
    ref2.dataset_id = "thelook_ecommerce"
    ref2.table_id = "order_items"
    ref2.schema = geminidataanalytics.Schema(description="financial transactions, purchases, refunds, orders line items")

    ref3 = geminidataanalytics.BigQueryTableReference()
    ref3.project_id = "bigquery-public-data"
    ref3.dataset_id = "thelook_ecommerce"
    ref3.table_id = "products"
    ref3.schema = geminidataanalytics.Schema(description="product catalog details, categories, brands, departments, and retail prices")

    ref4 = geminidataanalytics.BigQueryTableReference()
    ref4.project_id = "bigquery-public-data"
    ref4.dataset_id = "thelook_ecommerce"
    ref4.table_id = "users"
    ref4.schema = geminidataanalytics.Schema(description="customer demographic information, signup locations, email, and age")

    datasource_references = geminidataanalytics.DatasourceReferences()
    datasource_references.bq.table_references = [ref1, ref2, ref3, ref4]

    system_instruction = (
        "You are a data analyst specialized in the Looks E-commerce dataset. "
        "Analyze the e-commerce and website activity tables to answer customer and analytics questions. "
        "All answers must be derived by querying and joining these 4 core BigQuery tables:\n\n"
        "1. events: captures website traffic (page views, event_type, session_id, user_id, ip_address, created_at)\n"
        "2. order_items: contains line-item purchases and financial transactions. Use for all financial/order questions (order_id, user_id, sale_price, status, created_at)\n"
        "3. products: details the catalog (id, category, brand, department, retail_price)\n"
        "4. users: contains user demographics (id, first_name, last_name, email, age, traffic_source, created_at)\n\n"
        "JOIN LOGIC:\n"
        "- order_items.user_id = users.id\n"
        "- events.user_id = users.id\n"
        "- order_items.inventory_item_id groups sales by product.\n"
        "- To link events to products, parse the events.uri column to extract the product ID and join to products.id.\n\n"
        "METRICS CALCULATIONS:\n"
        "- Total Revenue/Sales: SUM(sale_price) on order_items\n"
        "- Order Count: COUNT(DISTINCT order_id) on order_items\n"
        "- Item Count: COUNT(*) on order_items\n"
        "- Average Item Price: AVG(sale_price) on order_items\n"
        "- Total Users/Customers: COUNT(DISTINCT id) on users\n"
        "- Unique Visitors: COUNT(DISTINCT ip_address) on events\n"
        "- Session Count: COUNT(DISTINCT session_id) on events\n\n"
        "DATE HANDLING:\n"
        "- Always use the created_at column from the relevant table for time filtering.\n"
        "- Use ONLY the date (no timestamps/hours). TIMESTAMP_TRUNC is not required, and resultsets must NOT include timestamps."
    )

    inline_context = geminidataanalytics.Context()
    inline_context.system_instruction = system_instruction
    inline_context.datasource_references = datasource_references
    inline_context.options.analysis.python.enabled = True

    messages = [geminidataanalytics.Message()]
    messages[0].user_message.text = prompt

    chat_request = geminidataanalytics.ChatRequest(
        parent=f"projects/{BILLING_PROJECT}/locations/{LOCATION}",
        messages=messages,
        inline_context=inline_context
    )

    print("[Look E-Commerce Tool] Sending request to CA API...")
    try:
        chat_response_stream = data_chat_client.chat(request=chat_request)
        final_answer = ""
        table_json = ""
        sql_query = ""
        for event in chat_response_stream:
            event_dict = type(event).to_dict(event)
            if "system_message" in event_dict:
                m = event_dict["system_message"]
                
                # Extract text final response parts
                if "text" in m:
                    text_obj = m["text"]
                    if text_obj.get("text_type") == 1:  # TextType.FINAL_RESPONSE
                        final_answer += "".join(text_obj.get("parts", []))
                
                # Extract data result and SQL query
                if "data" in m:
                    data_obj = m["data"]
                    if "generated_sql" in data_obj:
                        sql_query = data_obj["generated_sql"]
                    if "result" in data_obj and "data" in data_obj["result"]:
                        rows = data_obj["result"]["data"]
                        if rows:
                            table_json = json.dumps(rows, indent=2, ensure_ascii=False)
                                     
        if not table_json and sql_query:
            print(f"[Analytics] Table not found in stream. Running BQ fallback: {sql_query}")
            table_json = _execute_bq_query(sql_query)
                        
        if not final_answer:
            return "✅ Tool success, but wait, check logs for output."
            
        if table_json:
            return f"{final_answer}\n\n--- Structured Data (JSON) ---\n{table_json}"
        return final_answer
        
    except Exception as e:
        return f"❌ Error during CA API chat: {e}\n{traceback.format_exc()}"


def query_iowa_liquor_sales_api(prompt: str) -> str:
    """
    Queries the Conversational Analytics API to analyze the Iowa Liquor Sales dataset in BigQuery.
    Use this tool when you need to answer questions about liquor sales transactions, category volumes, store sales, or vendors in Iowa.

    Args:
        prompt: The natural language question to ask about the Iowa Liquor Sales data.

    Returns:
        The text response from the Data Agent.
    """
    print(f"\n[Iowa Liquor Tool] Intercepted Prompt: {prompt}")
    
    try:
        data_chat_client = geminidataanalytics.DataChatServiceClient()
    except Exception as e:
        return f"❌ Error initializing CA client: {e}\n{traceback.format_exc()}"

    # Define Data Sources
    ref1 = geminidataanalytics.BigQueryTableReference()
    ref1.project_id = "bigquery-public-data"
    ref1.dataset_id = "iowa_liquor_sales"
    ref1.table_id = "sales"
    ref1.schema = geminidataanalytics.Schema(description="Iowa liquor sales transactions (invoices, dates, stores, categories, vendor, cost, retail, bottles sold, sales, volumes)")

    datasource_references = geminidataanalytics.DatasourceReferences()
    datasource_references.bq.table_references = [ref1]

    system_instruction = (
        "You are a data analyst specialized in the Iowa Liquor Sales dataset. "
        "Analyze the sales table to answer liquor order and transactions questions. "
        "All answers must be derived by querying the table:\n\n"
        "1. sales: captures liquor purchase transactions (invoice_and_item_number, date, store_number, store_name, address, city, zip_code, store_location, county_number, county, category, category_name, vendor_number, vendor_name, item_number, item_description, pack, bottle_volume_ml, state_bottle_cost, state_bottle_retail, bottles_sold, sale_dollars, volume_sold_liters, volume_sold_gallons)\n\n"
        "METRICS CALCULATIONS:\n"
        "- Total Sales/Revenue: SUM(sale_dollars)\n"
        "- Total Bottles Sold: SUM(bottles_sold)\n"
        "- Total Volume (Liters): SUM(volume_sold_liters)\n"
        "- Total Volume (Gallons): SUM(volume_sold_gallons)\n"
        "- Number of Stores: COUNT(DISTINCT store_number)\n"
        "- Number of Invoices/Orders: COUNT(DISTINCT invoice_and_item_number)\n"
        "- Average Bottle Cost: AVG(state_bottle_cost)\n"
        "- Average Bottle Retail: AVG(state_bottle_retail)\n\n"
        "DATE HANDLING:\n"
        "- Always use the date column for time filtering.\n"
        "- Use ONLY the date (no timestamps/hours). TIMESTAMP_TRUNC is not required, and resultsets must NOT include timestamps."
    )

    inline_context = geminidataanalytics.Context()
    inline_context.system_instruction = system_instruction
    inline_context.datasource_references = datasource_references
    inline_context.options.analysis.python.enabled = True

    messages = [geminidataanalytics.Message()]
    messages[0].user_message.text = prompt

    chat_request = geminidataanalytics.ChatRequest(
        parent=f"projects/{BILLING_PROJECT}/locations/{LOCATION}",
        messages=messages,
        inline_context=inline_context
    )

    print("[Iowa Liquor Tool] Sending request to CA API...")
    try:
        chat_response_stream = data_chat_client.chat(request=chat_request)
        final_answer = ""
        table_json = ""
        sql_query = ""
        for event in chat_response_stream:
            event_dict = type(event).to_dict(event)
            if "system_message" in event_dict:
                m = event_dict["system_message"]
                
                # Extract text final response parts
                if "text" in m:
                    text_obj = m["text"]
                    if text_obj.get("text_type") == 1:  # TextType.FINAL_RESPONSE
                        final_answer += "".join(text_obj.get("parts", []))
                
                # Extract data result and SQL query
                if "data" in m:
                    data_obj = m["data"]
                    if "generated_sql" in data_obj:
                        sql_query = data_obj["generated_sql"]
                    if "result" in data_obj and "data" in data_obj["result"]:
                        rows = data_obj["result"]["data"]
                        if rows:
                            table_json = json.dumps(rows, indent=2, ensure_ascii=False)
                                     
        if not table_json and sql_query:
            print(f"[Analytics] Table not found in stream. Running BQ fallback: {sql_query}")
            table_json = _execute_bq_query(sql_query)
                        
        if not final_answer:
            return "✅ Tool success, but wait, check logs for output."
            
        if table_json:
            return f"{final_answer}\n\n--- Structured Data (JSON) ---\n{table_json}"
        return final_answer
        
    except Exception as e:
        return f"❌ Error during CA API chat: {e}\n{traceback.format_exc()}"
