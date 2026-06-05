import json
import re
from typing import Any
from llm import generate_json
DB_SYSTEM_PROMPT = """You are a database schema generator. Generate a complete PostgreSQL-compatible DB schema from a system design.

Return ONLY valid JSON. No markdown, no preamble.

Output schema:
{
  "tables": [
    {
      "name": "table_name (snake_case, plural)",
      "description": "what this table stores",
      "fields": [
        {
          "name": "field_name",
          "type": "string|integer|float|boolean|datetime|text|uuid|enum|json",
          "required": true/false,
          "unique": true/false,
          "primary_key": true/false,
          "foreign_key": "other_table.field or null",
          "default": "value or null",
          "enum_values": ["val1","val2"] or null,
          "indexed": true/false
        }
      ],
      "relations": ["User has_many Orders", "Order belongs_to User"]
    }
  ]
}

Rules:
- Every table MUST have: id (uuid, primary_key), created_at (datetime), updated_at (datetime)
- Foreign keys must reference real tables in this schema
- If a role system exists, include a roles table or role enum on users
- Snake_case for ALL names
- Add indexes on foreign keys and frequently queried fields
"""

API_SYSTEM_PROMPT = """You are an API schema generator. Generate a complete REST API schema.

Return ONLY valid JSON. No markdown, no preamble.

Output schema:
{
  "base_path": "/api/v1",
  "endpoints": [
    {
      "method": "GET|POST|PUT|PATCH|DELETE",
      "path": "/resource/:id",
      "summary": "what this endpoint does",
      "auth_required": true/false,
      "roles": ["roles that can access this"],
      "body_params": [{"name":"field","type":"string","required":true,"description":""}],
      "query_params": [{"name":"field","type":"string","required":false,"description":""}],
      "path_params": [{"name":"id","type":"uuid","required":true,"description":""}],
      "response_fields": ["field names returned"],
      "db_table": "which DB table this primarily operates on"
    }
  ]
}

Rules:
- Generate CRUD endpoints for ALL entities
- Auth endpoints: POST /auth/login, POST /auth/register, POST /auth/logout, POST /auth/refresh
- Field names in body_params/response_fields MUST match DB table field names exactly
- Roles in endpoints MUST be from the roles defined in the system design
- Include pagination params (page, limit) on all list endpoints
"""

UI_SYSTEM_PROMPT = """You are a UI schema generator. Generate a complete UI schema for a web app.

Return ONLY valid JSON. No markdown, no preamble.

Output schema:
{
  "theme": "light|dark",
  "nav_items": ["page names in nav"],
  "pages": [
    {
      "name": "PageName",
      "route": "/route",
      "title": "Page Title",
      "auth_required": true/false,
      "roles": ["roles that can access"],
      "layout": "default|sidebar|full-width",
      "components": [
        {
          "id": "unique_component_id",
          "type": "table|form|card|chart|list|modal|navbar|sidebar|button|input|badge|stats",
          "title": "Component Title",
          "fields": [
            {
              "name": "field_name",
              "label": "Human Label",
              "component": "input|select|textarea|checkbox|datepicker",
              "api_field": "maps to API body/query param name",
              "required": true/false,
              "placeholder": "hint text or null",
              "options": ["for select only"] 
            }
          ],
          "api_endpoint": "POST /api/v1/resource or null",
          "roles": ["which roles see this component"],
          "props": {}
        }
      ]
    }
  ]
}

Rules:
- Include a login page (route: /login, auth_required: false)
- Include a dashboard/home page
- Every form field's api_field MUST match an API endpoint body_param name
- Roles on pages/components MUST match auth roles
- Include a navbar component on all authenticated pages
- Admin-only pages must have roles: ["admin"]
"""

AUTH_SYSTEM_PROMPT = """You are an auth schema generator. Generate a complete auth + permissions schema.

Return ONLY valid JSON. No markdown, no preamble.

Output schema:
{
  "strategy": "jwt",
  "session_ttl_hours": 24,
  "refresh_token": true,
  "oauth_providers": [],
  "roles": [
    {
      "name": "role_name",
      "description": "what this role represents",
      "is_default": true/false,
      "permissions": [
        {
          "resource": "resource_name (matches DB table name)",
          "actions": ["create","read","update","delete"] or ["*"]
        }
      ]
    }
  ]
}

Rules:
- Roles MUST match roles defined in the system design
- One role must be is_default: true (the basic user role)
- Admin role MUST have wildcard (*) permissions or explicit full access
- Resources MUST match DB table names
- If premium plan exists, add a "premium" role with extra permissions
"""

async def generate_schemas(intent: dict, design: dict, model: str) -> dict[str, Any]:
    """Stage 3: Generate all four schemas in parallel."""
    
    context = json.dumps({"intent": intent, "design": design}, indent=2)
    
    # Run all 4 schema generations
    db_raw = generate_json(
    DB_SYSTEM_PROMPT,
    f"Generate DB schema for:\n\n{context}"
    )
    api_raw = generate_json(
    API_SYSTEM_PROMPT,
    f"Generate API schema for:\n\n{context}"
    )
    ui_raw = generate_json(
    UI_SYSTEM_PROMPT,
    f"Generate UI schema for:\n\n{context}"
    )
    auth_raw = generate_json(
    AUTH_SYSTEM_PROMPT,
    f"Generate Auth schema for:\n\n{context}"
    )
    
    def parse(raw: str) -> dict:
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw.strip())
    
    return {
        "database": parse(db_raw),
        "api": parse(api_raw),
        "ui": parse(ui_raw),
        "auth": parse(auth_raw),
    }
