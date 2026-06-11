import os
from google import genai
from google.genai import types
import json
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.environ.get("GOOGLE_CLOUD_PROJECT", "ml-demo-384110"),
    location="us-central1" # Wait, us-central1 has gemini-2.5-flash / image models
)

data = {"Jan": 10, "Feb": 20, "Mar": 15}
contents = f"Représente graphiquement les données suivantes sous forme de graphique à barres simple : {json.dumps(data)}"

model_names = [
    "gemini-2.5-flash",
    "imagen-3.0-generate-002",
]

for model in model_names:
    print(f"\n--- Testing model: {model} ---")
    try:
        if "imagen" in model:
            # Imagen uses generate_images
            resp = client.models.generate_images(
                model=model,
                prompt=contents,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="4:3",
                    output_mime_type="image/png"
                )
            )
            print("Successfully called generate_images!")
            if resp.generated_images:
                img_bytes = resp.generated_images[0].image.image_bytes
                print("Image generated, bytes length:", len(img_bytes))
        else:
            # Gemini uses generate_content
            config = types.GenerateContentConfig(
                temperature=1.0,
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="4:3",
                    output_mime_type="image/png"
                )
            )
            resp = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            print("Successfully called generate_content!")
            img_b64 = None
            if hasattr(resp, 'candidates') and resp.candidates:
                for c in resp.candidates:
                    if hasattr(c, 'content') and c.content and hasattr(c.content, 'parts'):
                        for p in c.content.parts:
                            if hasattr(p, 'inline_data') and p.inline_data:
                                img_b64 = len(p.inline_data.data)
                                print(f"Found inline_data image of length {img_b64}")
    except Exception as e:
        print(f"Error with {model}: {e}")
