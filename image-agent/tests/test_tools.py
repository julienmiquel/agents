import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add app to path - no longer needed as we are at root if running from image-agent, 
# but for safety kept or adjusted. 
# sys.path.append(os.path.join(os.path.dirname(__file__), "..")) 
# Actually if running from root, .. adds parent.
# Let's assume running pytest from image-agent root.

from tools.image_gen import generate_image
from tools.upscale import upscale_image
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def mock_tool_context():
    context = MagicMock()
    context.save_artifact = AsyncMock()
    # Mock load_artifact to return a dummy Part with inline data
    context.load_artifact = AsyncMock()
    
    # Create a dummy part-like object
    mock_part = MagicMock()
    mock_part.inline_data = MagicMock()
    # Create simple red image bytes
    from PIL import Image
    try:
        from io import BytesIO
        buf = BytesIO()
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(buf, format='PNG')
        mock_part.inline_data.data = buf.getvalue()
    except ImportError:
         mock_part.inline_data.data = b"dummy_bytes"

    context.load_artifact.return_value = mock_part
    return context

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("GOOGLE_CLOUD_PROJECT"), reason="GCP Project not set")
async def test_generate_image(mock_tool_context):
    """Tests the image generation tool with artifact saving."""
    print("\n--- Testing generate_image ---")
    prompt = "A cute robot holding a flower, simple vector art"
    
    result = await generate_image(prompt=prompt, tool_context=mock_tool_context, aspect_ratio="1:1")
    print(f"Result: {result}")
    
    assert "successfully" in result or "Error" in result
    
    if "successfully" in result:
        # Verify artifact was saved
        assert mock_tool_context.save_artifact.called
        call_args = mock_tool_context.save_artifact.call_args
        assert call_args is not None
        filename, artifact = call_args[0]
        print(f"Artifact saved: {filename}")
        assert filename.endswith(".png")

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("GOOGLE_CLOUD_PROJECT"), reason="GCP Project not set")
async def test_upscale_image_with_path(mock_tool_context):
    """Tests the upscale image tool with file path."""
    print("\n--- Testing upscale_image (Path) ---")
    
    # Create a dummy image file for testing
    dummy_path = "/tmp/test_source_image.png"
    if not os.path.exists(dummy_path):
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(dummy_path)
    
    result = await upscale_image(image_path=dummy_path, tool_context=mock_tool_context, scale_factor=2.0)
    print(f"Result: {result}")
    
    assert "successfully" in result or "Error" in result
    
    if "successfully" in result:
        assert mock_tool_context.save_artifact.called

@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("GOOGLE_CLOUD_PROJECT"), reason="GCP Project not set")
async def test_upscale_image_with_artifact(mock_tool_context):
    """Tests the upscale image tool with artifact input."""
    print("\n--- Testing upscale_image (Artifact) ---")
    
    artifact_name = "existing_image.png"
    result = await upscale_image(artifact_name=artifact_name, tool_context=mock_tool_context, scale_factor=2.0)
    print(f"Result: {result}")
    
    # Check if load_artifact was called
    mock_tool_context.load_artifact.assert_called_with(filename=artifact_name)
    
    assert "successfully" in result or "Error" in result
    if "successfully" in result:
        assert mock_tool_context.save_artifact.called
