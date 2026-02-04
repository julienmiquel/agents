from google import genai
from google.genai import types
import os

def test_config():
    try:
        config = types.GenerateImagesConfig(
            aspect_ratio="1:1",
            number_of_images=1,
            image_size="4K"
        )
        print("Success: image_size is a valid parameter.")
    except Exception as e:
        print(f"Error: image_size is INVALID. {e}")

if __name__ == "__main__":
    test_config()
