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

import os
import google.auth

try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
except google.auth.exceptions.DefaultCredentialsError:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
    if "GOOGLE_API_KEY" not in os.environ:
        os.environ["GOOGLE_API_KEY"] = "mock_api_key"


def write_md_file(filename: str, content: str) -> dict:
    """Writes content to a Markdown file.

    Args:
        filename: The name of the Markdown file to write to.
        content: The Markdown content to write.

    Returns:
        A dictionary containing the status of the operation.
    """
    try:
        filename = os.path.basename(filename)
        if not filename.endswith(".md"):
            filename += ".md"
        with open(filename, "w") as f:
            f.write(content)
        return {"status": "success", "message": f"Successfully wrote to {filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="You are a helpful AI assistant that can write Markdown files. Use the write_md_file tool to write markdown files when requested.",
    tools=[write_md_file],
)

app = App(
    root_agent=root_agent,
    name="app",
)

from google.adk.a2a.utils.agent_to_a2a import to_a2a
a2a_app = to_a2a(root_agent, port=8001)
