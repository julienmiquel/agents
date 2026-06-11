import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog

catalog_config = BasicCatalog.get_config("0.8")
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[catalog_config],
)

system_prompt = schema_manager.generate_system_prompt(
    role_description="Test Role",
    workflow_description="Test Workflow",
    ui_description="Test UI",
    include_schema=True,
    include_examples=True,
)

with open("scratch/system_prompt.txt", "w") as f:
    f.write(system_prompt)
print("System prompt written to scratch/system_prompt.txt")
