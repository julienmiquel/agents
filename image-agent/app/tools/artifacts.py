import os
import logging
import base64
import subprocess
import mimetypes
import uuid
from google.adk.tools import ToolContext
from google.genai import types
from google.cloud import storage

logger = logging.getLogger(__name__)

async def download_file_from_url(url: str, output_filename: str, tool_context: ToolContext) -> str:
    """Downloads a file from a URL to the artifact store.

    Args:
        url: The URL to download from.
        output_filename: The name to save the artifact as.
        tool_context: The tool context.

    Returns:
        The name of the saved artifact.
    """
    try:
        # Use curl to download the file
        # We need to save to a temporary location first, then save_artifact
        temp_path = f"/tmp/{output_filename}"
        subprocess.check_call(["curl", "-o", temp_path, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with open(temp_path, "rb") as f:
            data = f.read()
            
        # Detect mime type
        mime_type, _ = mimetypes.guess_type(output_filename)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        part = types.Part(inline_data=types.Blob(mime_type=mime_type, data=data))
        await tool_context.save_artifact(filename=output_filename, artifact=part) # Async
        
        os.remove(temp_path)
        return f"Successfully downloaded {url} to artifact '{output_filename}'"
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return f"Error downloading file: {str(e)}"

async def load_image_from_artifact(artifact_name: str, tool_context: ToolContext) -> str:
    """Loads an image from an artifact to a local file path.

    Args:
        artifact_name: The name of the artifact (e.g., "image.png").
        tool_context: The tool context.

    Returns:
         The absolute path to the local image file, or empty string if failed.
    """
    logger.info(f"Step [load_image_from_artifact]: Starting load for '{artifact_name}'")
    local_path = f"/tmp/{artifact_name}"
    
    try:
        artifact = await tool_context.load_artifact(filename=artifact_name)
        
        if artifact:
             logger.info(f"Step [load_image_from_artifact]: Found artifact '{artifact_name}' directly in artifact store.")
        
        if not artifact:
            logger.info(f"Step [load_image_from_artifact]: Artifact '{artifact_name}' not found in store. Initiating history fallback search.")
            # Fallback: Search session history for user uploads
            try:
                # Access internals to find user content
                invocation_context = getattr(tool_context, "_invocation_context", None)
                found_part = None
                
                if invocation_context:
                    # 1. Collect all candidates
                    history_candidates = []
                    if hasattr(invocation_context, 'session') and invocation_context.session.events:
                        logger.info(f"Inspecting {len(invocation_context.session.events)} session events for fallback.")
                        history_candidates.extend([e.content for e in invocation_context.session.events if e.content])

                    user_candidates = []
                    if invocation_context.user_content:
                         logger.info("Inspecting user_content for fallback.")
                         user_candidates.append(invocation_context.user_content)
                    
                    all_candidates = user_candidates + history_candidates

                    # 2. Try Exact Match First (Best effort)
                    for content in all_candidates:
                        if found_part: break
                        if not content or not content.parts: continue
                        for part in content.parts:
                            # Standardize metadata access
                            d_name = None
                            uri = ""
                            
                            if part.inline_data:
                                inline_d = part.inline_data
                                if isinstance(inline_d, dict): d_name = inline_d.get("display_name")
                                else: d_name = getattr(inline_d, "display_name", None)
                            elif part.file_data:
                                file_d = part.file_data
                                if isinstance(file_d, dict): 
                                    uri = file_d.get("file_uri", "")
                                    d_name = file_d.get("display_name")
                                else: 
                                    uri = getattr(file_d, "file_uri", "")
                                    d_name = getattr(file_d, "display_name", None)
                            
                            
                            if d_name == artifact_name or (uri and uri.endswith(f"/{artifact_name}")):
                                logger.info(f"Step [load_image_from_artifact]: Found EXACT match in history: {artifact_name}")
                                found_part = part
                                break
                    
                    # 3. If No Exact Match, Try Lenient Match (Single Image in Current Turn)
                    if not found_part and user_candidates:
                        logger.info("Step [load_image_from_artifact]: No exact match found. Checking for single image in current turn (Lenient Fallback).")
                        # collect all image parts in user content
                        image_parts = []
                        for content in user_candidates:
                             for part in content.parts:
                                 if part.inline_data or part.file_data:
                                     image_parts.append(part)
                        
                        if len(image_parts) == 1:
                            logger.info(f"Step [load_image_from_artifact]: Found exactly one image in user prompt. Using it despite name mismatch (Request: {artifact_name}).")
                            found_part = image_parts[0]
                        else:
                            logger.info(f"Lenient fallback failed: Found {len(image_parts)} images in user content.")
                
                if found_part:
                    logger.info(f"Step [load_image_from_artifact]: Match found. Saving '{artifact_name}' to artifact store for persistence.")
                    # Save it to artifact registry so next time it is found easily
                    # We need to construct a proper Part if found_part is just internal structure
                    # But typically found_part is types.Part.
                    await tool_context.save_artifact(filename=artifact_name, artifact=found_part)
                    artifact = found_part # Use it directly
                else:
                    return ""
            except Exception as e:
                logger.error(f"Error searching history: {e}")
                return ""

        if hasattr(artifact, 'inline_data') and artifact.inline_data:
            data = artifact.inline_data.data
            if isinstance(data, str):
                import base64
                image_bytes = base64.b64decode(data)
            else:
                image_bytes = data
            
            with open(local_path, "wb") as f:
                f.write(image_bytes)
            return local_path
            
        elif hasattr(artifact, 'file_data') and artifact.file_data:
             logger.info(f"Artifact is file_data: {artifact.file_data.file_uri}")
             file_uri = artifact.file_data.file_uri
             
             if file_uri.startswith("gs://"):
                 # Use google-cloud-storage to download
                 try:
                     logger.info(f"Downloading from GCS: {file_uri} to {local_path}")
                     
                     # Parse bucket and blob name
                     # gs://bucket_name/path/to/blob
                     parts = file_uri[5:].split("/", 1)
                     if len(parts) != 2:
                         logger.error(f"Invalid GCS URI: {file_uri}")
                         return ""
                         
                     bucket_name, blob_name = parts
                     
                     storage_client = storage.Client()
                     bucket = storage_client.bucket(bucket_name)
                     blob = bucket.blob(blob_name)
                     blob.download_to_filename(local_path)
                     
                     return local_path
                 except Exception as e:
                     logger.error(f"Failed to download GCS artifact: {e}")
                     return ""
             else:
                 logger.error(f"Unsupported file URI scheme: {file_uri}")
                 return ""
        
        # Fallback if artifact is just bytes (unlikely with types.Part return)
        elif isinstance(artifact, bytes):
             with open(local_path, "wb") as f:
                f.write(artifact)
             return local_path
             
        return ""

    except Exception as e:
        logger.error(f"Error loading artifact: {e}")
        return ""
