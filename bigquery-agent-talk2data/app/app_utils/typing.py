import uuid
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field


class Feedback(BaseModel):
    """Represents feedback for a conversation."""

    score: Union[int, float]
    text: Optional[str] = ""
    log_type: Literal["feedback"] = "feedback"
    service_name: Literal["ca-bridge-agent"] = "ca-bridge-agent"
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
