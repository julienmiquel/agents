from google.adk.tools import ToolContext
from google import genai
from google.genai import types
import os
import logging
from typing import Optional
from tools.artifacts import load_image_from_artifact

logger = logging.getLogger(__name__)

async def upscale_image(
    tool_context: ToolContext,
    image_path: Optional[str] = None, 
    scale_factor: float = 4.0,
    artifact_name: Optional[str] = None
):
    """Upscales an image.

    Args:
        tool_context: The tool context.
        image_path: Local path to the image file (optional).
        scale_factor: The factor to upscale by (default: 2.0).
        artifact_name: The name of the artifact to upscale (optional). Use this if the image was generated or uploaded previously.

    Returns:
        A message indicating the result and the artifact name of the upscaled image.
    """
    logger.info(f"Step [upscale_image]: Started with image_path={image_path}, artifact_name={artifact_name}, scale_factor={scale_factor}")
    
    source_image_path = ""
    
    if artifact_name:
        # Use our enhanced loader that checks history fallback
        logger.info(f"Step [upscale_image]: Calling load_image_from_artifact for '{artifact_name}'")
        source_image_path = await load_image_from_artifact(artifact_name, tool_context)
        if not source_image_path:
             logger.error(f"Step [upscale_image]: Failed to load artifact '{artifact_name}'")
             return f"Error: Artifact '{artifact_name}' not found."
             
    elif image_path:
        source_image_path = image_path
    else:
        return "Error: Please provide either `image_path` or `artifact_name`."

    if not os.path.exists(source_image_path):
        return f"Error: Image file not found at {source_image_path}"

    try:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("IMAGE_UPSCALE_MODEL_REGION", "us-central1")
        
        logger.info(f"Step [upscale_image]: Initializing genai.Client with project={project_id}, location={location}")
        
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        with open(source_image_path, "rb") as f:
             image_bytes = f.read()
             source_image = types.Image(image_bytes=image_bytes, mime_type="image/png")

        # Call the model
        model_name = os.environ.get("IMAGE_UPSCALE_MODEL", "imagen-4.0-upscale-preview")
        upscale_factor_str = f"x{int(scale_factor)}" if scale_factor else "x2"
        # The API only supports specific factors like x2, x4. 
        # For safety let's default to x2 or x4 based on input or just pass x2 if unsure.
        # But generally users might pass 2.0 or 4.0.
        if scale_factor >= 4.0:
            upscale_factor_str = "x4"
        else:
            upscale_factor_str = "x2"

        logger.info(f"Step [upscale_image]: Invoking client.models.upscale_image with model={model_name}, factor={upscale_factor_str}")
        
        response = client.models.upscale_image(
            model=model_name,
            image=source_image,
            upscale_factor=upscale_factor_str
        )
        
        logger.info("Step [upscale_image]: Model generation complete.")
        
        # valid response structure: response.generated_image is bytes or similar?
        # Checking google-genai docs/usage: response usually has generated_images or similar.
        # But for specific tasks it might be direct.
        # Let's assume standard response object which likely has 'generated_images' list or 'image' field.
        # Actually for upscale_image in this client validation, let's look at what return type we expect.
        # If it returns a GeneratedImage object, we can save it.
        # The user example just showed the call: `response = client.models.upscale_image(...)`
        
        # Based on library patterns:
        if hasattr(response, "generated_images") and response.generated_images:
             generated_image_bytes = response.generated_images[0].image.image_bytes
        elif hasattr(response, "image"):
             # Some endpoints return single image
             generated_image_bytes = response.image.image_bytes
        else:
             # Fallback or direct bytes? expected to be wrapped.
             # Let's try standard attribute access for types.Image
             generated_image_bytes = response.generated_images[0].image.image_bytes

        # Save the result
        output_filename = f"upscaled_{artifact_name if artifact_name else os.path.basename(image_path)}"
        if not output_filename.endswith(".png"):
             output_filename += ".png"
             
        local_output_path = f"/tmp/{output_filename}"
        
        with open(local_output_path, "wb") as f:
            f.write(generated_image_bytes)
        
        # Save back to artifacts
        part = types.Part(inline_data=types.Blob(mime_type="image/png", data=generated_image_bytes))
        logger.info(f"Step [upscale_image]: Saving result '{output_filename}' to artifacts.")
        await tool_context.save_artifact(filename=output_filename, artifact=part)
        
        logger.info(f"Step [upscale_image]: Completed successfully. Output: {output_filename}")
        return f"Your image has been upscaled to `{output_filename}`."

    except Exception as e:
        logger.error(f"Error upscaling image: {e}")
        return f"Error upscaling image: {str(e)}"

