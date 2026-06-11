import os
import sys
import importlib
from google.adk.apps import App
from google.adk.agents.base_agent import BaseAgent

WORKSPACE_DIR = "/Users/julienmiquel/dev/agents"

# Setup mocks
from unittest.mock import MagicMock
class MockA2uiSchemaManager:
    def __init__(self, *args, **kwargs):
        pass
    def generate_system_prompt(self, role_description="", workflow_description="", *args, **kwargs):
        return f"{role_description}\n\n{workflow_description}"

class MockBasicCatalog:
    @staticmethod
    def get_config(*args, **kwargs):
        return {}

def setup_a2ui_mocks():
    sys.modules['a2ui'] = MagicMock()
    sys.modules['a2ui.schema'] = MagicMock()
    a2ui_schema_manager = MagicMock()
    a2ui_schema_manager.A2uiSchemaManager = MockA2uiSchemaManager
    sys.modules['a2ui.schema.manager'] = a2ui_schema_manager

    sys.modules['a2ui.basic_catalog'] = MagicMock()
    a2ui_basic_catalog_provider = MagicMock()
    a2ui_basic_catalog_provider.BasicCatalog = MockBasicCatalog
    sys.modules['a2ui.basic_catalog.provider'] = a2ui_basic_catalog_provider

def check_desc():
    for item in os.listdir(WORKSPACE_DIR):
        item_path = os.path.join(WORKSPACE_DIR, item)
        if os.path.isdir(item_path) and not item.startswith("."):
            agent_file = os.path.join(item_path, "app", "agent.py")
            if os.path.exists(agent_file):
                orig_sys_path = list(sys.path)
                sys.path.insert(0, item_path)
                
                # Clear cache
                for sys_mod_name, sys_mod in list(sys.modules.items()):
                    if sys_mod_name == 'serve' or sys_mod_name.startswith('serve.'):
                        continue
                    in_workspace = False
                    if hasattr(sys_mod, "__file__") and sys_mod.__file__:
                        file_path = sys_mod.__file__
                        in_workspace = file_path.startswith(WORKSPACE_DIR) and not file_path.startswith(os.path.join(WORKSPACE_DIR, ".venv"))
                    is_top_level_conflict = sys_mod_name in ['app', 'tools', 'a2ui', 'prompt_builder', 'app_utils'] or \
                                            sys_mod_name.startswith('app.') or sys_mod_name.startswith('tools.') or \
                                            sys_mod_name.startswith('a2ui.') or sys_mod_name.startswith('prompt_builder.') or \
                                            sys_mod_name.startswith('app_utils.')
                    if in_workspace or is_top_level_conflict:
                        del sys.modules[sys_mod_name]
                        
                setup_a2ui_mocks()
                try:
                    module = importlib.import_module("app.agent")
                    app_obj = getattr(module, "app", None)
                    if app_obj and isinstance(app_obj, App):
                        desc = app_obj.root_agent.description
                        inst = app_obj.root_agent.instruction[:50].replace('\n', ' ')
                        print(f"Agent: {item} | Desc: '{desc}' | Inst: '{inst}'")
                    else:
                        print(f"Agent: {item} | No app object found")
                except Exception as e:
                    print(f"Agent: {item} | Error: {e}")
                finally:
                    sys.path = orig_sys_path

if __name__ == "__main__":
    check_desc()
