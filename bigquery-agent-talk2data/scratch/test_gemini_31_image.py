import os
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110"),
    location="global"
)

data = {"Jan": 10, "Feb": 20, "Mar": 15}
contents = f"Représente graphiquement les données suivantes sous forme de graphique à barres simple : {json.dumps(data)}"

model = "gemini-3.1-flash-image-preview"

try:
    config = types.GenerateContentConfig(
        temperature=1.0,
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(
            output_mime_type="image/png"
        )
    )
    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    print("Successfully called generate_content!")
    print("Candidates:")
    for c in resp.candidates:
        print("Candidate Content Parts:")
        for p in c.content.parts:
            print(f"- Type: {type(p)}")
            if hasattr(p, 'text') and p.text:
                print(f"  Text: {p.text}")
            if hasattr(p, 'inline_data') and p.inline_data:
                print(f"  Inline Data Mime Type: {p.inline_data.mime_type}")
                print(f"  Inline Data Length: {len(p.inline_data.data)}")
except Exception as e:
    print(f"Error: {e}")
