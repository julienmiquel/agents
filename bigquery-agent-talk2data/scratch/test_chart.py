import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.visualization import generate_data_chart

dummy_data = {"A": 10, "B": 20, "C": 15}

print("Running with apply_theme_ai=True:")
res_ai = generate_data_chart(dummy_data, apply_theme_ai=True)
print("Type of result:", type(res_ai))
print("Keys of result:", res_ai.keys() if isinstance(res_ai, dict) else "N/A")
print("gcsUri:", res_ai.get("gcsUri") if isinstance(res_ai, dict) else "N/A")
print("dataUri prefix:", res_ai.get("dataUri")[:50] if isinstance(res_ai, dict) and res_ai.get("dataUri") else "N/A")

print("\nRunning with apply_theme_ai=False:")
res_pil = generate_data_chart(dummy_data, apply_theme_ai=False)
print("Type of result:", type(res_pil))
print("gcsUri:", res_pil.get("gcsUri") if isinstance(res_pil, dict) else "N/A")
print("dataUri prefix:", res_pil.get("dataUri")[:50] if isinstance(res_pil, dict) and res_pil.get("dataUri") else "N/A")
