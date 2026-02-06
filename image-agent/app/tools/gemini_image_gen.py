from google import genai
from google.genai import types
from google.adk.tools import ToolContext
import os
import uuid
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

async def generate_image_gemini(tool_context: ToolContext, prompt: str, aspect_ratio: str = "1:1", image_size: str = "4k") -> str:
    """Generates an image using Gemini 3 Pro (Thinking Model) and saves it as an artifact.

    Args:
        tool_context: The tool context for saving artifacts.
        prompt: A text description of the image to generated.
        aspect_ratio: The aspect ratio of the image. Valid values: 1:1, 3:2, 2:3, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9.

    Returns:
        A message indicating where the image is saved.
    """
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1") # Standard location
    model_id = "gemini-3-pro-image-preview"
    
    logger.info(f"Starting generate_image_gemini with prompt='{prompt}', aspect_ratio='{aspect_ratio}', image_size='{image_size}'")

    try:
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location="global",
            # http_options={"headers": {"X-Goog-User-Project": None}} # Workaround for ADK location override issue
        )
        
        logger.info(f"Using model: {model_id}")
        
        # Using dict for image_config to avoid potential missing class in types module
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT'],
                image_config={"aspect_ratio": aspect_ratio, "image_size": image_size},
            ),
        )
        
        # Check for errors
        if not response.candidates or response.candidates[0].finish_reason != types.FinishReason.STOP:
            reason = response.candidates[0].finish_reason if response.candidates else "No candidates"
            logger.error(f"Prompt Content Error: {reason}")
            return f"Error: Image generation failed. Reason: {reason}"

        generated_filenames = []
        
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # Save image artifact
                filename = f"gemini_gen_{uuid.uuid4()}.png"
                
                # ADK ToolContext save_artifact expects types.Part
                # We can reuse the part we received, but ensure mime_type is correct
                # part.inline_data.data is bytes
                
                image_part = types.Part.from_bytes(
                    data=part.inline_data.data,
                    mime_type="image/png"  # Assuming PNG for now
                )
                
                await tool_context.save_artifact(filename, image_part)
                generated_filenames.append(filename)
                logger.info(f"Saved artifact: {filename}")
                
            if part.text:
                # Log thought process or partial text
                logger.info(f"Model thought/text: {part.text[:100]}...")

        if not generated_filenames:
             return "No image was generated in the response."

        return f"Image(s) generated successfully: {', '.join(generated_filenames)} Model thought/text: {part.text}"

    except Exception as e:
        logger.error(f"Error generating image with Gemini: {str(e)}", exc_info=True)
        return f"Error generating image: {str(e)}"
