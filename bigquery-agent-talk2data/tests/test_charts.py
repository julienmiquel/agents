import os
import sys
import base64
from unittest.mock import AsyncMock, MagicMock
import pytest

# Mark all tests in this file as async under anyio/pytest-asyncio
pytestmark = pytest.mark.anyio

# Mock a2ui dependencies
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

@pytest.fixture
def mock_tool_context():
    ctx = MagicMock()
    ctx.save_artifact = AsyncMock()
    return ctx

async def test_bar_simple(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"A": 10, "B": 20, "C": 15})
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")
    
async def test_bar_many(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"Item " + str(i): i*5 for i in range(1, 15)})
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_bar_large(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"X": 1000000, "Y": 2500000, "Z": 1500000})
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_bar_zero(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"A": 10, "B": 0, "C": 15})
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_bar_one(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"Only": 42})
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_dot_flow(mock_tool_context):
    result = await generate_graphviz_diagram(mock_tool_context, "digraph { rankdir=LR; A -> B -> C; }")
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_dot_tree(mock_tool_context):
    result = await generate_graphviz_diagram(mock_tool_context, "digraph { Parent -> Child1; Parent -> Child2; Child1 -> Grandchild; }")
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_dot_network(mock_tool_context):
    result = await generate_graphviz_diagram(mock_tool_context, "graph { A -- B; B -- C; C -- A; D -- A; }")
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_dot_styled(mock_tool_context):
    result = await generate_graphviz_diagram(mock_tool_context, "digraph { node [shape=box, style=filled, fillcolor=lightblue]; A -> B; }")
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_dot_complex(mock_tool_context):
    result = await generate_graphviz_diagram(mock_tool_context, "digraph { rankdir=BT; A [shape=diamond]; B [shape=box]; A -> B [label=\"yes\"]; A -> C [label=\"no\"]; }")
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_bar_theme_ai_success(mock_tool_context, monkeypatch):
    class MockInlineData:
        data = b"dummy_png_bytes"
    class MockPart:
        inline_data = MockInlineData()
    class MockContent:
        parts = [MockPart()]
    class MockCandidate:
        content = MockContent()
    class MockChunk:
        text = ""
        candidates = [MockCandidate()]
        
    class MockModels:
        def generate_content(self, *args, **kwargs):
            return MockChunk()
            
    class MockClient:
        def __init__(self, *args, **kwargs):
            self.models = MockModels()
            
    import google.genai
    monkeypatch.setattr(google.genai, "Client", MockClient)
    
    result = await generate_data_chart(mock_tool_context, {"Bananas": 50, "Apples": 30}, apply_theme_ai=True)
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

async def test_bar_theme_ai_error_fallback(mock_tool_context, monkeypatch):
    class MockModels:
        def generate_content_stream(self, *args, **kwargs):
            raise Exception("API rate limit or timeout")
            
    class MockClient:
        def __init__(self, *args, **kwargs):
            self.models = MockModels()
            
    import google.genai
    monkeypatch.setattr(google.genai, "Client", MockClient)
    result = await generate_data_chart(mock_tool_context, {"Cyberpunk": 100, "Neon": 200}, apply_theme_ai=True)
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

@pytest.mark.skip(reason="Nécessite l'accès au modèle d'aperçu natif réel dans le projet Cloud")
async def test_bar_theme_ai_context_mixed(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"Arbre": 50, "Fleuve": 80, "Montagne": 60, "Cyber": 40}, apply_theme_ai=True)
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")

@pytest.mark.skip(reason="Nécessite l'accès au modèle d'aperçu natif réel dans le projet Cloud")
async def test_bar_theme_ai_context_default(mock_tool_context):
    result = await generate_data_chart(mock_tool_context, {"Normal1": 30, "Normal2": 70}, apply_theme_ai=True)
    assert isinstance(result, dict)
    assert result["dataUri"].startswith("data:image/png;base64,")
