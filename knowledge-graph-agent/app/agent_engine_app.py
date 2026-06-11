"""Module defining the AgentEngineApp class for Vertex AI Reasoning Engine deployment."""
import logging
import os
from typing import Any, Optional

import vertexai
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.sessions.session import Session

from app.agent import app as adk_app

class SafeVertexAiSessionService(VertexAiSessionService):
    """Custom session service to handle Discovery Engine session path integrations."""
    
    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        if session_id and "/" in session_id:
            cleaned = session_id.split("/")[-1]
            session_id = cleaned
        session = await super().get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )
        if session is None:
            from google.genai.errors import ClientError
            raise ClientError(
                code=404,
                response_json={"message": f"Session {session_id} not found in Vertex AI."},
            )
        return session

    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        if session_id and "/" in session_id:
            session_id = session_id.split("/")[-1]
        await super().delete_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

def safe_session_service_builder() -> SafeVertexAiSessionService:
    """Builder for SafeVertexAiSessionService."""
    return SafeVertexAiSessionService(
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
        agent_engine_id=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"),
    )

class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging."""
        vertexai.init()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")

agent_engine = AgentEngineApp(
    app=adk_app,
    artifact_service_builder=lambda: (
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    ),
    session_service_builder=safe_session_service_builder,
)
