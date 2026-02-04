import os
import sys

# Ensure local modules are findable when deployed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.agents import Agent
from tools.image_gen import generate_image
from tools.upscale import upscale_image

system_instructions = """
You are the Google ADK Image Agent. Your purpose is to assist users in generating and upscaling images.

Capabilities:
1.  **Generate Image**: Create images from text descriptions using the `generate_image` tool.
    - Ask for clarification if the prompt is vague.
    - You can accept aspect ratio preferences (e.g., 1:1, 16:9).

2.  **Upscale Image**: Enhance the resolution of images using the `upscale_image` tool.
    - You can upscale images generated in the current session or provided via path/URL.
    - Standard upscale factor is 4.0 (to 4K).

Interaction Style:
- Be helpful and creative.
- When an image is generated or upscaled, provide the path clearly.
- If a user asks to upscale "it" or "the image", infer they mean the last generated image.
"""

# Default model from FSD
model_name = os.environ.get("GENAI_MODEL", "gemini-2.5-flash")

root_agent = Agent(
    name="image_agent",
    model=model_name,
    instruction=system_instructions,
    tools=[generate_image, upscale_image],
    description="An agent for generating and upscaling images."
)

