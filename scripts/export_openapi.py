"""Export the complete FastAPI schema without loading model weights.

Run from the repository root: python -m scripts.export_openapi
"""

from pathlib import Path

import yaml

from app.main import app


def main() -> None:
    schema = app.openapi()
    responses = schema["paths"]["/ai/classify"]["post"]["responses"]
    assert "422" not in responses
    assert {"200", "400", "503", "500"} <= set(responses)
    assert "/health" in schema["paths"]
    assert schema["components"]["schemas"]["ClassificationResponse"]["properties"]["predictions"]["type"] == "array"

    output = Path(__file__).resolve().parents[1] / "docs" / "ai-classify.openapi.yaml"
    output.write_text(yaml.safe_dump(schema, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OpenAPI exported: {output}")


if __name__ == "__main__":
    main()
