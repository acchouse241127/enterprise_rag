"""Generate API documentation using FastAPI's built-in OpenAPI support."""

import json
from pathlib import Path

from main import app

# Output directory
DOCS_DIR = Path(__file__).parent.parent / "docs" / "api"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Generate OpenAPI schema
openapi_schema = app.openapi()

# Save as JSON
json_path = DOCS_DIR / "openapi.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, ensure_ascii=False, indent=2)

# Save as YAML
try:
    import yaml

    yaml_path = DOCS_DIR / "openapi.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, allow_unicode=True, default_flow_style=False)
    print(f"✅ OpenAPI YAML generated: {yaml_path}")
except ImportError:
    print("⚠️  PyYAML not installed, skipping YAML generation")

# Generate Markdown documentation
md_path = DOCS_DIR / "api_docs.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# Enterprise RAG System API Documentation\n\n")
    f.write("## Introduction\n\n")
    f.write("This document describes the REST API for the Enterprise RAG System.\n\n\n")
    f.write(f"**API Version**: {openapi_schema.get('info', {}).get('version')}\n\n")
    f.write(f"**Base URL**: http://localhost:8000/api\n\n")
    f.write("\n## Authentication\n\n")
    f.write("Most endpoints require JWT authentication. Include the token in the Authorization header:\n\n")
    f.write("```bash\n")
    f.write("Authorization: Bearer <your_token>\n")
    f.write("```\n\n")
    f.write("## API Endpoints\n\n")

    # Group by tags
    paths = openapi_schema.get("paths", {})
    tags = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            for tag in details.get("tags", []):
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append({
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "operationId": details.get("operationId", ""),
                    "description": details.get("description", ""),
                })

    # Write documentation for each tag
    for tag, endpoints in tags.items():
        f.write(f"\n### {tag}\n\n")
        for ep in endpoints:
            f.write(f"\n#### {ep['method']} {ep['path']}\n\n")
            if ep["summary"]:
                f.write(f"**{ep['summary']}**\n\n")
            if ep["description"]:
                f.write(f"{ep['description']}\n\n")
            if ep["operationId"]:
                f.write(f"**Operation ID**: `{ep['operationId']}`\n\n")

print(f"✅ API documentation generated: {md_path}")
print(f"✅ OpenAPI schema generated: {json_path}")
print("\nView interactive API docs at: http://localhost:8000/docs")
print("View ReDoc at: http://localhost:8000/redoc")
