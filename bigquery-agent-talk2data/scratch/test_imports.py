import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import prompt_builder
    print("Successfully imported prompt_builder!")
    print("get_ui_instruction function:", getattr(prompt_builder, "get_ui_instruction", None))
except Exception as e:
    print("Failed to import prompt_builder:", e)
