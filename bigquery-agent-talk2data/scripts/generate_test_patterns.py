import os
import sys
import base64
from unittest.mock import MagicMock

# Mock a2ui dependencies since they are not available in the environment
class MockA2uiSchemaManager:
    def __init__(self, *args, **kwargs):
        pass
    def generate_system_prompt(self, *args, **kwargs):
        return "Mocked System Prompt"

class MockBasicCatalog:
    @staticmethod
    def get_config(*args, **kwargs):
        return {}

a2ui_schema_manager = MagicMock()
a2ui_schema_manager.A2uiSchemaManager = MockA2uiSchemaManager
sys.modules['a2ui.schema.manager'] = a2ui_schema_manager

a2ui_basic_catalog_provider = MagicMock()
a2ui_basic_catalog_provider.BasicCatalog = MockBasicCatalog
sys.modules['a2ui.basic_catalog.provider'] = a2ui_basic_catalog_provider

# Ensure we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tools.visualization import generate_data_chart, generate_graphviz_diagram

output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../output_charts'))
os.makedirs(output_dir, exist_ok=True)

def gen_with_mocked_theme(data, bg, txt_col, grid, bar):
    class MockResponse:
        text = f'{{"doc_title": "ANALYSE PREMIUM", "summary_bullets": ["Excellente dynamique sur la période", "Les indicateurs affichent une nette surperformance"], "takeaway": "Tendance thématique IA confirmée."}}'
    class MockModels:
        def generate_content(self, *args, **kwargs): return MockResponse()
    class MockClient:
        def __init__(self, *args, **kwargs): self.models = MockModels()
    import google.genai
    google.genai.Client = MockClient
    return generate_data_chart(data, apply_theme_ai=True)

patterns = [
    ("bar_simple", lambda: generate_data_chart({"A": 10, "B": 20, "C": 15})),
    ("bar_many", lambda: generate_data_chart({"Item " + str(i): i*5 for i in range(1, 15)})),
    ("bar_large", lambda: generate_data_chart({"X": 1000000, "Y": 2500000, "Z": 1500000})),
    ("bar_zero", lambda: generate_data_chart({"A": 10, "B": 0, "C": 15})),
    ("bar_one", lambda: generate_data_chart({"Only": 42})),
    ("bar_theme_ai_cyberpunk", lambda: gen_with_mocked_theme({"Neon": 90, "Chrome": 40, "Laser": 75}, "#0B0B12", "#00FFCC", "#FF0055", "#FF00AA")),
    ("bar_theme_ai_nature", lambda: gen_with_mocked_theme({"Trees": 60, "Rivers": 30, "Hills": 45}, "#1B261C", "#E8F5E9", "#2E7D32", "#81C784")),
    ("bar_theme_ai_mixed", lambda: gen_with_mocked_theme({"Arbre": 50, "Fleuve": 80, "Montagne": 60, "Cyber": 40}, "#141418", "#EBEBF0", "#89B4FA", "#555F78")),
    ("bar_theme_ai_default", lambda: gen_with_mocked_theme({"Normal1": 30, "Normal2": 70}, "#141418", "#EBEBF0", "#89B4FA", "#555F78")),
    ("dot_flow", lambda: generate_graphviz_diagram("digraph { rankdir=LR; A -> B -> C; }")),
    ("dot_tree", lambda: generate_graphviz_diagram("digraph { Parent -> Child1; Parent -> Child2; Child1 -> Grandchild; }")),
    ("dot_network", lambda: generate_graphviz_diagram("graph { A -- B; B -- C; C -- A; D -- A; }")),
    ("dot_styled", lambda: generate_graphviz_diagram("digraph { node [shape=box, style=filled, fillcolor=lightblue]; A -> B; }")),
    ("dot_complex", lambda: generate_graphviz_diagram("digraph { rankdir=BT; A [shape=diamond]; B [shape=box]; A -> B [label=\"yes\"]; A -> C [label=\"no\"]; }")),
]

for name, func in patterns:
    print(f"Generating {name}...")
    result = func()
    if result.startswith("data:image/png;base64,"):
        base64_data = result.split(",")[1]
        image_bytes = base64.b64decode(base64_data)
        file_path = os.path.join(output_dir, f"{name}.png")
        with open(file_path, "wb") as f:
            f.write(image_bytes)
        print(f"Saved to {file_path}")
    else:
        print(f"Error generating {name}: {result}")

print("Done.")
