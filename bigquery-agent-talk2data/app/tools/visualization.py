import os
import io
import base64
import json
import uuid
from PIL import Image, ImageDraw, ImageFont
from google.cloud import storage
from google.adk.tools import ToolContext
from google.genai import types

def _get_http_url(gs_uri: str) -> str:
    """Converts a gs:// URI to an HTTP GCS URL."""
    if gs_uri.startswith("gs://"):
        parts = gs_uri[5:].split("/", 1)
        if len(parts) == 2:
            bucket_name, path = parts
            return f"https://storage.googleapis.com/{bucket_name}/{path}"
    return ""

def _upload_bytes_to_gcs(bytes_data: bytes) -> str:
    """Uploads bytes to the GCS staging bucket and returns the gs:// URI or empty string."""
    bucket_name = os.environ.get("GOOGLE_CLOUD_STORAGE_BUCKET") or os.environ.get("STAGING_BUCKET")
    if not bucket_name:
        print("[Visualization] No GCS bucket configured for uploading.")
        return ""
    
    # Save original env variables to restore them later
    orig_cert = os.environ.get("GOOGLE_API_USE_CLIENT_CERTIFICATE")
    orig_mtls = os.environ.get("GOOGLE_API_USE_MTLS")
    
    # Disable mTLS locally to bypass CAA issue
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
    os.environ["GOOGLE_API_USE_MTLS"] = "never"
    
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        filename = f"visualizations/{uuid.uuid4()}.png"
        blob = bucket.blob(filename)
        blob.upload_from_string(bytes_data, content_type="image/png")
        return f"gs://{bucket_name}/{filename}"
    except Exception as e:
        print(f"[Visualization] GCS upload failed: {e}")
        return ""
    finally:
        # Restore original env variables
        if orig_cert is not None:
            os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = orig_cert
        else:
            os.environ.pop("GOOGLE_API_USE_CLIENT_CERTIFICATE", None)
            
        if orig_mtls is not None:
            os.environ["GOOGLE_API_USE_MTLS"] = orig_mtls
        else:
            os.environ.pop("GOOGLE_API_USE_MTLS", None)

async def generate_data_chart(tool_context: ToolContext, data: dict, chart_type: str = "bar", apply_theme_ai: bool = False) -> dict:
    """
    Generates a rich diagram (chart) from data and returns a dictionary containing 'url', 'gcsUri', 'dataUri' and 'filename'.
    Use this tool when you need to visualize data trends, comparisons, or distributions.

    Args:
        tool_context: The ADK tool context.
        data: A dictionary where keys are labels and values are numeric data points.
              Example: {"Jan": 10, "Feb": 20, "Mar": 15}
        chart_type: The type of chart to generate. Currently supported: 'bar'.
        apply_theme_ai: If True, optionally calls Gemini AI to improve chart colors based on the data theme.

    Returns:
        A dict containing 'url' (HTTP GCS URL), 'gcsUri' (GCS gs:// path), 'dataUri' (base64 data URI), and 'filename' of the saved artifact.
    """
    try:
        if not data:
            return "Error: No data provided for chart."

        if apply_theme_ai:
            # 1. Tentative de génération d'une véritable image native via l'API Gemini Multimodale
            try:
                from google import genai
                import json
                
                client = genai.Client(
                    vertexai=True,
                    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
                    location="global"
                )
                model = "gemini-3.1-flash-image-preview"
                
                contents = f"garde les legendes. Représente purement graphiquement, de façon magnifique et photoréaliste, sans textes superflus, les données suivantes : {json.dumps(data)}"

                generate_content_config = types.GenerateContentConfig(
                    temperature = 1,
                    top_p = 0.95,
                    max_output_tokens = 32768,
                    response_modalities = ["TEXT", "IMAGE"],
                    safety_settings = [
                        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
                    ],
                    image_config = types.ImageConfig(
                        aspect_ratio="auto",
                        output_mime_type="image/png"
                    )
                )

                resp = client.models.generate_content(
                    model = model,
                    contents = contents,
                    config = generate_content_config,
                )
                
                native_img_base64 = None
                if hasattr(resp, 'candidates') and resp.candidates:
                    for c in resp.candidates:
                        if hasattr(c, 'content') and c.content and hasattr(c.content, 'parts'):
                            for p in c.content.parts:
                                if hasattr(p, 'inline_data') and p.inline_data:
                                    native_img_base64 = base64.b64encode(p.inline_data.data).decode('utf-8')
                                    break
                        if native_img_base64: break

                if native_img_base64:
                    print("\n[Visualization] Image native générée avec succès via Gemini AI Stream.")
                    raw_bytes = base64.b64decode(native_img_base64)
                    gcs_uri = _upload_bytes_to_gcs(raw_bytes)
                    gcs_url = _get_http_url(gcs_uri)
                    
                    filename = f"chart_{uuid.uuid4().hex[:8]}.png"
                    image_part = types.Part.from_bytes(
                        data=raw_bytes,
                        mime_type="image/png"
                    )
                    await tool_context.save_artifact(filename=filename, artifact=image_part)
                    
                    return {
                        "url": gcs_url,
                        "gcsUri": gcs_uri,
                        "dataUri": f"data:image/png;base64,{native_img_base64}",
                        "filename": filename
                    }
            except Exception as e:
                print(f"[Visualization] Rendu natif échoué : {e}. Falling back to standard PIL rendering.")

        # Mode standard par défaut (non infographie premium)
        width, height = 800, 500
        margin = 80
        bg_color = (30, 30, 46)
        text_color = (205, 214, 244)
        grid_color = (69, 71, 90)
        bar_color = (137, 180, 250)
        
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=20)
        except:
            try:
                font = ImageFont.truetype("Arial", size=20)
            except:
                font = ImageFont.load_default()

        labels = list(data.keys())
        values = list(data.values())
        
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        
        chart_x = margin
        chart_y = margin + 20
        chart_w = width - 2 * margin
        chart_h = height - 2 * margin - 20
        
        num_grid_lines = 5
        for i in range(num_grid_lines + 1):
            y = chart_y + chart_h - (i * chart_h / num_grid_lines)
            draw.line([chart_x, y, chart_x + chart_w, y], fill=grid_color, width=1)
            val_label = int(min_val + (max_val - min_val) * (i / num_grid_lines))
            draw.text((chart_x - 65, y - 10), str(val_label), fill=text_color, font=font)

        if chart_type == "bar":
            num_bars = len(data)
            bar_width = (chart_w / num_bars) * 0.7
            spacing = (chart_w / num_bars) * 0.3
            
            for i, (label, val) in enumerate(data.items()):
                bar_h = (val / max_val) * chart_h if max_val > 0 else 0
                x0 = chart_x + i * (bar_width + spacing) + spacing / 2
                y0 = chart_y + chart_h - bar_h
                x1 = x0 + bar_width
                y1 = chart_y + chart_h
                
                radius = 8
                if bar_h > radius:
                    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=bar_color)
                else:
                    draw.rectangle([x0, y0, x1, y1], fill=bar_color)
                
                draw.text((x0, y1 + 15), str(label), fill=text_color, font=font)
                draw.text((x0 + bar_width/4, y0 - 30), str(val), fill=text_color, font=font)
                
            draw.line([chart_x, chart_y + chart_h, chart_x + chart_w, chart_y + chart_h], fill=text_color, width=2)
        else:
            return f"Error: Chart type '{chart_type}' not supported."

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        png_bytes = buf.getvalue()
        base64_encoded = base64.b64encode(png_bytes).decode('utf-8')
        
        gcs_uri = _upload_bytes_to_gcs(png_bytes)
        gcs_url = _get_http_url(gcs_uri)
        
        filename = f"chart_{uuid.uuid4().hex[:8]}.png"
        image_part = types.Part.from_bytes(
            data=png_bytes,
            mime_type="image/png"
        )
        await tool_context.save_artifact(filename=filename, artifact=image_part)
        
        return {
            "url": gcs_url,
            "gcsUri": gcs_uri,
            "dataUri": f"data:image/png;base64,{base64_encoded}",
            "filename": filename
        }
        
    except Exception as e:
        return {"error": f"Error generating chart: {e}"}

async def generate_graphviz_diagram(tool_context: ToolContext, dot_code: str) -> dict:
    """
    Generates a rich diagram from DOT code using Graphviz and returns a dictionary containing 'url', 'gcsUri', 'dataUri' and 'filename'.
    Use this tool when you need to show a flowchart, network graph, or complex structural diagram.

    Args:
        tool_context: The ADK tool context.
        dot_code: The Graphviz DOT language code defining the diagram.

    Returns:
        A dict containing 'url', 'gcsUri', 'dataUri' and 'filename', or an error dict.
    """
    try:
        import graphviz
        
        default_styles = """
        graph [bgcolor="#1E1E2E", fontname="Helvetica", fontcolor="#CDD6F4"];
        node [shape=box, style="filled,rounded", fillcolor="#89B4FA", fontname="Helvetica", fontcolor="#1E1E2E", color="#45475A"];
        edge [color="#F5C2E7", fontname="Helvetica", fontcolor="#CDD6F4"];
        """
        
        idx = dot_code.find('{')
        if idx != -1:
            dot_code = dot_code[:idx+1] + default_styles + dot_code[idx+1:]
            
        src = graphviz.Source(dot_code)
        png_bytes = src.pipe(format='png')
        base64_encoded = base64.b64encode(png_bytes).decode('utf-8')
        
        gcs_uri = _upload_bytes_to_gcs(png_bytes)
        gcs_url = _get_http_url(gcs_uri)
        
        filename = f"diagram_{uuid.uuid4().hex[:8]}.png"
        image_part = types.Part.from_bytes(
            data=png_bytes,
            mime_type="image/png"
        )
        await tool_context.save_artifact(filename=filename, artifact=image_part)
        
        return {
            "url": gcs_url,
            "gcsUri": gcs_uri,
            "dataUri": f"data:image/png;base64,{base64_encoded}",
            "filename": filename
        }
    except Exception as e:
        return {"error": f"Error generating diagram: {e}"}
