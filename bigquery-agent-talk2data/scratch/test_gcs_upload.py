import os
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_MTLS"] = "never"

from google.cloud import storage
import uuid
from dotenv import load_dotenv
load_dotenv()

bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "ml-demo-384110-agent-engine")
print(f"Target Bucket: {bucket_name}")

try:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    filename = f"visualizations_test/{uuid.uuid4()}.txt"
    blob = bucket.blob(filename)
    blob.upload_from_string(b"Test upload from Antigravity agent", content_type="text/plain")
    gcs_uri = f"gs://{bucket_name}/{filename}"
    print(f"✅ Success! File uploaded to: {gcs_uri}")
    
    # Clean up
    blob.delete()
    print("Cleaned up test file.")
except Exception as e:
    print(f"❌ Failed upload: {e}")
