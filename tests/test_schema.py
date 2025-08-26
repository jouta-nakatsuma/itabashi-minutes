
import json
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path("schemas/minutes.schema.json")
FIXTURE_PATH = Path("tests/fixtures/minutes_valid.sample.json")

def test_minutes_schema_valid():
    assert SCHEMA_PATH.exists(), f"Schema not found: {SCHEMA_PATH}"
    assert FIXTURE_PATH.exists(), f"Fixture not found: {FIXTURE_PATH}"

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    instance = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    # 素直にDraft-07で検証（formatは通す想定だが、URIは一応有効な形にしてある）
    jsonschema.validate(instance=instance, schema=schema)
