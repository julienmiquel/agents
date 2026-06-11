from google.genai import types
import inspect

print("Fields in ImageConfig:")
for name, field in types.ImageConfig.model_fields.items():
    print(f"- {name}: {field.annotation} (default: {field.default})")
