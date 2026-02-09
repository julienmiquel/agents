
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import os
from google.adk.tools import ToolContext
from google.genai import types

# Import tools
from app.tools.image_gen import generate_image
from app.tools.upscale import upscale_image
from app.tools.artifacts import download_file_from_url, load_image_from_artifact

@pytest.fixture
def mock_tool_context():
    context = AsyncMock(spec=ToolContext)
    return context

@pytest.fixture
def mock_genai_client():
    with patch("app.tools.image_gen.genai.Client") as mock:
        yield mock

@pytest.fixture
def mock_genai_client_upscale():
    with patch("app.tools.upscale.genai.Client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_generate_image_success(mock_tool_context, mock_genai_client):
    # Setup mock
    client_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    mock_image = MagicMock()
    mock_response.generated_images = [MagicMock(image=mock_image)]
    client_instance.models.generate_images.return_value = mock_response

    # Setup file saving mock
    with patch("builtins.open", mock_open(read_data=b"image_data")), \
         patch("app.tools.image_gen.uuid.uuid4", return_value="test-uuid"):
        
        result = await generate_image(mock_tool_context, "test prompt", "1:1")

    # Verify
    assert "test-uuid.png" in result
    client_instance.models.generate_images.assert_called_once()
    mock_tool_context.save_artifact.assert_called_once()
    args, _ = mock_tool_context.save_artifact.call_args
    assert args[0] == "gen_test-uuid.png"  # Filename

@pytest.mark.asyncio
async def test_upscale_image_with_path(mock_tool_context, mock_genai_client_upscale):
    # Setup mock content
    client_instance = mock_genai_client_upscale.return_value
    mock_response = MagicMock()
    # Mock behavior for response parsing (structure depends on actual API, assuming generated_images list based on impl)
    mock_image_obj = MagicMock()
    mock_image_obj.image.image_bytes = b"upscaled_data"
    mock_response.generated_images = [mock_image_obj]
    client_instance.models.upscale_image.return_value = mock_response

    with patch("builtins.open", mock_open(read_data=b"original_data")), \
         patch("os.path.exists", return_value=True):
        
        result = await upscale_image(mock_tool_context, image_path="/tmp/test.png", scale_factor=2.0)

    assert "upscaled_test.png" in result
    client_instance.models.upscale_image.assert_called_once()
    mock_tool_context.save_artifact.assert_called_once()


@pytest.mark.asyncio
async def test_download_file_from_url(mock_tool_context):
    with patch("subprocess.check_call") as mock_subprocess, \
         patch("builtins.open", mock_open(read_data=b"file_data")), \
         patch("os.remove") as mock_remove:
        
        result = await download_file_from_url("http://example.com/image.png", "image.png", mock_tool_context)
        
    assert "Successfully downloaded" in result
    mock_tool_context.save_artifact.assert_called_once()
    mock_subprocess.assert_called_once()
    mock_remove.assert_called_once()

@pytest.mark.asyncio
async def test_load_image_from_artifact_direct_success(mock_tool_context):
    # Test case where artifact exists in ToolContext
    mock_artifact = MagicMock()
    mock_artifact.inline_data.data = b"image_data"
    mock_tool_context.load_artifact.return_value = mock_artifact
    
    with patch("builtins.open", mock_open()) as mock_file:
        path = await load_image_from_artifact("test.png", mock_tool_context)
        
    assert path == "/tmp/test.png"
    mock_tool_context.load_artifact.assert_awaited_once_with(filename="test.png")

@pytest.mark.asyncio
async def test_load_image_from_artifact_fallback(mock_tool_context):
    # Test case where artifact is NOT in ToolContext but found in history
    mock_tool_context.load_artifact.return_value = None
    
    # Mock invocation context for history
    mock_invocation = MagicMock()
    # Create a user content part matching the request
    mock_part = MagicMock()
    # inline_data should be an object with .data and .display_name (if accessed via getattr)
    mock_blob = MagicMock()
    mock_blob.display_name = "test.png"
    mock_blob.data = b"fallback_image_data"
    mock_part.inline_data = mock_blob
    mock_part.parts = []
    
    # Structure: invocation -> session -> events -> content -> parts
    # OR invocation -> user_content -> parts
    
    mock_content = MagicMock()
    mock_content.parts = [mock_part]
    mock_invocation.user_content = mock_content
    mock_invocation.session.events = []
    
    mock_tool_context._invocation_context = mock_invocation

    # We need to ensure the found part is then saved and processed.
    # The code saves it back to artifact store.
    
    # Also need to mock 'open' to save the file locally
    with patch("builtins.open", mock_open()) as mock_file:
        path = await load_image_from_artifact("test.png", mock_tool_context)
    
    # Should have found it in fallback and saved it
    mock_tool_context.save_artifact.assert_awaited_once()
    assert path == "/tmp/test.png"
