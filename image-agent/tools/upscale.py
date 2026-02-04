from google import genai
from google.genai import types
from google.adk.tools import ToolContext
import os
import io
import uuid
import logging
from typing import Optional



logger = logging.getLogger(__name__)

async def upscale_image(tool_context: ToolContext, image_path: Optional[str] = None, scale_factor: float = 2.0, artifact_name: Optional[str] = None) -> str:
    """Upscales an image using Imagen 4 and saves it as an artifact.

    Args:
        tool_context: The tool context for saving/loading artifacts.
        image_path: The local path or GCS URI of the image to upscale.
        scale_factor: The factor to upscale by (2.0, 3.0, or 4.0).
        artifact_name: The name of the artifact to upscale (if provided, image_path is ignored).

    Returns:
        A message indicating where the upscaled image is saved.
    """
    if not image_path and not artifact_name:
        logger.error("Error: Either image_path or artifact_name must be provided.")
        return "Error: Either image_path or artifact_name must be provided."

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    # Upscale service requires us-central1 independently
    location = os.environ.get("GOOGLE_CLOUD_REGION_UPSCALE_SERVICE", "us-central1")
    model_name = os.environ.get("IMAGE_UPSCALE_MODEL", "imagen-4.0-upscale-preview") 
    
    logger.info(f"Starting upscale_image with model={model_name}, scale_factor={scale_factor}, location={location}")

    try:
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        if artifact_name:
            logger.info(f"Loading artifact for upscaling: {artifact_name}")
            artifact = await tool_context.load_artifact(filename=artifact_name)
            if not artifact:
                return f"Error: Artifact '{artifact_name}' not found."
            
            # Extract bytes from artifact
            if hasattr(artifact, 'inline_data') and artifact.inline_data:
                source_image_bytes = artifact.inline_data.data
            elif hasattr(artifact, 'file_data') and artifact.file_data:
                 return f"Error: Artifact '{artifact_name}' is not inline data (not supported yet)."
            elif isinstance(artifact, bytes):
                source_image_bytes = artifact
            else:
                 return f"Error: Could not extract bytes from artifact '{artifact_name}'."

            # Create types.Image from bytes
            source_image = types.Image(image_bytes=source_image_bytes)
            
        else:
             # Load from path
             with open(image_path, "rb") as f:
                 source_image_bytes = f.read()
             source_image = types.Image(image_bytes=source_image_bytes)

        # Upscale using the SDK method
        upscale_factor_str = f"x{int(scale_factor)}"
        
        logger.info(f"Calling client.models.upscale_image with factor {upscale_factor_str}")
        
        response = client.models.upscale_image(
            model=model_name,
            image=source_image,
            upscale_factor=upscale_factor_str
        )
        
        if not response or not response.generated_images:
            logger.error(f"Failed to upscale image: {response}")
            return "Failed to upscale image."

        upscaled_image = response.generated_images[0].image
        filename = f"upscaled_{uuid.uuid4()}.png"
        
        local_path = f"/tmp/{filename}"
        upscaled_image.save(local_path)
        
        with open(local_path, "rb") as f:
            upscaled_bytes = f.read()

        report_artifact = types.Part.from_bytes(
            data=upscaled_bytes, mime_type="image/png"
        )
        await tool_context.save_artifact(filename, report_artifact)
        
        logger.info(f"Image upscaled successfully and saved as artifact: {filename}")
        return f"Image upscaled successfully and saved as artifact: {filename}"

    except Exception as e:
        logger.error(f"Error upscaling image with {model_name}: {str(e)}", exc_info=True)
        return f"Error upscaling image with {model_name}: {str(e)}"
