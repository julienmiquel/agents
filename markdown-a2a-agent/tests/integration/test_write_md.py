import pytest
from unittest.mock import patch, ANY
from app.agent import root_agent

def test_agent_write_md() -> None:
    # Test that the agent has the correct tools
    tools = root_agent.tools
    assert len(tools) == 1
    assert tools[0].__name__ == "write_md_file"

    # Test that the tool works correctly
    from app.agent import write_md_file
    result = write_md_file("test.md", "hello world")
    assert result["status"] == "success"

    with open("test.md", "r") as f:
        assert f.read() == "hello world"

    import os
    os.remove("test.md")
