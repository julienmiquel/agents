"""Module for extracting Knowledge Graphs from text."""
import io
import csv
import re
from typing import Dict, List, Any

from google import genai

TAB = "\t"
KNOWLEDGE_GRAPH_OUTPUT_FORMAT = f"""
Format the output strictly as two TSV code blocks (including the header row):

```tsv filename="entities.tsv"
id{TAB}name{TAB}label
[data_rows]
```

```tsv filename="relationships.tsv"
source_id{TAB}link{TAB}target_id
[data_rows]
```
"""

def extract_tsv_block(data: str, filestem: str) -> str:
    """Extracts a TSV block from markdown output."""
    pattern = rf'```tsv filename="{re.escape(filestem)}\.tsv"\s*\n(.*?)```'
    match = re.search(pattern, data, flags=re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()

def parse_tsv_to_dicts(tsv_string: str, expected_fields: List[str]) -> List[Dict[str, Any]]:
    """Parses a TSV string into a list of dictionaries."""
    rows = []
    if not tsv_string:
        return rows
    for row in csv.DictReader(io.StringIO(tsv_string), delimiter="\t"):
        casted_data = {}
        for key in expected_fields:
            if key in row:
                # Attempt basic casting for IDs
                val = row[key]
                if key.endswith("id") and val.isdigit():
                    casted_data[key] = int(val)
                else:
                    casted_data[key] = val
        rows.append(casted_data)
    return rows

def extract_knowledge_graph(text: str, data_schema: str = "", instructions: str = "") -> dict:
    """Extracts a knowledge graph (entities and relationships) from the given text.

    Args:
        text: The text document to analyze.
        data_schema: Optional data schema describing the entities and relationships. If empty, uses a default open schema.
        instructions: Optional instructions on how to extract. If empty, uses default extraction rules.

    Returns:
        A dictionary containing lists of 'entities' and 'relationships'.
    """
    if not data_schema:
        data_schema = '''- Entity:
  - `id`: Unique integer identifier (0, 1, 2…).
  - `name`: Full name of the entity.
  - `label`: Entity type (e.g., PERSON, ORGANIZATION, LOCATION, CONCEPT).
- Relationship:
  - `source_id`: `id` of the subject entity.
  - `link`: `snake_case` predicate describing the relationship.
  - `target_id`: `id` of the object entity.'''

    if not instructions:
        instructions = '''- Entity Extraction:
  - Extract all distinct entities mentioned in the text.
  - Include implied entities whose names can be deduced.
  - Treat distinct aliases as entirely separate entities.
- Relationship Extraction:
  - Extract all distinct relationships between these entities.
  - Use specific `link` predicates in `snake_case` as needed.
  - For every relationship, determine if an inverse or symmetric relationship is implied and include it.'''

    prompt = f"""**Data Schema**

{data_schema}

**Instructions**

{instructions}

**Output Format**

{KNOWLEDGE_GRAPH_OUTPUT_FORMAT}

**Input Text**

{text}
"""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    response_text = response.text or ""
    
    entities_tsv = extract_tsv_block(response_text, "entities")
    relationships_tsv = extract_tsv_block(response_text, "relationships")
    
    entities = parse_tsv_to_dicts(entities_tsv, ["id", "name", "label"])
    relationships = parse_tsv_to_dicts(relationships_tsv, ["source_id", "link", "target_id"])
    
    return {
        "entities": entities,
        "relationships": relationships
    }
