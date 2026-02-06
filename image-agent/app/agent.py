# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.gemini_image_gen import generate_image_gemini
from tools.upscale import upscale_image
from tools.artifacts import download_file_from_url, load_image_from_artifact

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

system_instructions ="""
You are the Google ADK Image Agent. Your purpose is to assist users in generating and upscaling images.

Capabilities:

1.  **Upscale Image**: Enhance the resolution of images using the `upscale_image` tool.
    - You can upscale images generated in the current session or provided via path/URL.
    - Standard upscale factor is 4.0 (to 4K).
    - If the image is too large, you can upscale it to 2K by setting the `scale_factor` parameter to 2.
    - If the image was previously generated in 4k, you can not upscale it further.

2.  **Artifact Handling**:
    - `download_file_from_url`: Download files from URLs to artifacts.
    - `load_image_from_artifact`: Load an image from an artifact to a local path (useful for upscaling or processing).

3.  **Generate Image (Gemini)**: Create images with reasoning capabilities using `generate_image_gemini` (Gemini 3 Pro).
    - Use this when the user asks for "reasoning", "thinking", "infographic", or complex layouts.
    - Parameters: aspect ratio.

Interaction Style:
- Be helpful and creative.
- When an image is generated or upscaled, provide the path clearly.
- If a user asks to upscale "it" or "the image", infer they mean the last generated image or latest image available in the conversation.
- **User Uploads**: If the user uploads an image, LOOK AT THE IMAGE METADATA. The `display_name` of the uploaded image (e.g., "croissant.png") IS the artifact name. You MUST pass this exact filename as the `artifact_name` argument to tools. Do NOT ask the user for the filename if you can see it in the message context.
"""

root_agent = Agent(
    name="image_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=system_instructions,
    tools=[upscale_image, download_file_from_url, load_image_from_artifact, generate_image_gemini],
)

app = App(root_agent=root_agent, name="app")
