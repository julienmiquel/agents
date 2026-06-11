import pytest
from unittest.mock import patch, ANY
from app.agent import root_agent

def test_agent_write_md(tmp_path) -> None:
    # Test that the agent has the correct tools
    tools = root_agent.tools
    assert len(tools) == 1
    assert tools[0].__name__ == "write_md_file"

    # Test that the tool works correctly using a temporary workspace directory
    from app.agent import write_md_file
    import os
    
    with patch.dict(os.environ, {"WORKSPACE_DIR": str(tmp_path)}):
        result = write_md_file("test.md", "hello world")
        assert result["status"] == "success"

        filepath = tmp_path / "test.md"
        assert filepath.exists()
        assert filepath.read_text() == "hello world"
