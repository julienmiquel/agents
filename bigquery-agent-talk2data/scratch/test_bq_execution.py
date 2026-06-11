import os
import json
from google.cloud import bigquery
from dotenv import load_dotenv
load_dotenv()

BILLING_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110")

sql = """
SELECT item_description, SUM(sale_dollars) AS total_sales
FROM `bigquery-public-data.iowa_liquor_sales.sales`
WHERE date >= '2026-01-01' AND date <= '2026-12-31'
GROUP BY item_description
ORDER BY total_sales DESC
LIMIT 10
"""

print(f"Executing SQL in billing project: {BILLING_PROJECT}")
try:
    # Disable mTLS locally to bypass ECP connection issue
    orig_cert = os.environ.get("GOOGLE_API_USE_CLIENT_CERTIFICATE")
    orig_mtls = os.environ.get("GOOGLE_API_USE_MTLS")
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
    os.environ["GOOGLE_API_USE_MTLS"] = "never"
    
    client = bigquery.Client(project=BILLING_PROJECT)
    query_job = client.query(sql)
    results = query_job.result()
    
    rows_list = []
    for row in results:
        # Convert row values to dict
        rows_list.append(dict(row.items()))
        
    print("Success!")
    print(json.dumps(rows_list, indent=2))
    
    # Restore original env variables
    if orig_cert is not None:
        os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = orig_cert
    else:
        os.environ.pop("GOOGLE_API_USE_CLIENT_CERTIFICATE", None)
    if orig_mtls is not None:
        os.environ["GOOGLE_API_USE_MTLS"] = orig_mtls
    else:
        os.environ.pop("GOOGLE_API_USE_MTLS", None)
        
except Exception as e:
    print("Error executing query:", e)
