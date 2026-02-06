from google import genai
from google.genai import types
import os
import uuid
import logging
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

async def generate_image(tool_context: ToolContext, prompt: str, aspect_ratio: str = "1:1") -> str:
    """Generates an image based on the prompt using Imagen 4 and saves it as an artifact.

    Args:
        tool_context: The tool context for saving artifacts.
        prompt: The text description of the image to generate.
        aspect_ratio: The aspect ratio of the image (e.g., "1:1", "16:9", "3:4", "4:3").

    Returns:
        A message indicating where the image is saved.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("IMAGE_GEN_MODEL_REGION", "us-central1")
    
    # Use environment variable for model name
    model_name = os.environ.get("IMAGE_GEN_MODEL", "imagen-4.0-generate-001")
    
    logger.info(f"Starting image generation with model={model_name}, prompt='{prompt}', aspect_ratio={aspect_ratio}")
    
    try:
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )
        
        # Imagen 4 supports 1K and 2K image_size
        response = client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                aspect_ratio=aspect_ratio,
                number_of_images=1,
                # image_size="2K"
            )
        )
        
        if not response.generated_images:
            return "Failed to generate image."
            
        image = response.generated_images[0].image
        
        filename = f"gen_{uuid.uuid4()}.png"
        local_path = f"/tmp/{filename}"
        
        # Save locally first
        image.save(local_path)
        
        # Read back bytes for artifact saving
        with open(local_path, "rb") as f:
            image_bytes = f.read()

        report_artifact = types.Part.from_bytes(
            data=image_bytes, mime_type="image/png"
        )
        await tool_context.save_artifact(filename, report_artifact)
        
        logger.info(f"Image generated successfully and saved as artifact: {filename}")
        return f"Image generated successfully and saved as artifact: {filename}"
        
    except Exception as e:
        logger.error(f"Error generating image with {model_name}: {str(e)}", exc_info=True)
        return f"Error generating image with {model_name}: {str(e)}"
