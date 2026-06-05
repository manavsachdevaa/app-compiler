import json
import re
from typing import Any
from llm import generate_json

SYSTEM_PROMPT = """You are a software architect. Given a structured intent object, produce a system design document.

Return ONLY valid JSON. No markdown, no explanation, no preamble.

Output schema:
{
  "architecture": {
    "type": "monolith | microservice | serverless",
    "layers": ["list of layers e.g. presentation, business, data"],
    "patterns": ["design patterns used e.g. MVC, Repository, CQRS"]
  },
  "entities": [
    {
      "name": "EntityName",
      "description": "what this entity represents",
      "fields": ["field_name:type e.g. id:uuid, email:string, created_at:datetime"],
      "relations": ["e.g. User has_many Orders", "Order belongs_to User"],
      "is_auth_entity": true/false
    }
  ],
  "flows": [
    {
      "name": "flow name e.g. User Registration",
      "steps": ["step 1", "step 2"],
      "roles_involved": ["admin", "user"]
    }
  ],
  "role_access_matrix": {
    "role_name": {
      "entity_name": ["create", "read", "update", "delete"]
    }
  },
  "premium_features": ["features behind paywall"],
  "integrations": ["third-party services needed"]
}

Rules:
- Be thorough. Include ALL entities needed to implement the described features
- Always include a User/Account entity if auth is required
- Always include a Session or Token entity if JWT auth
- role_access_matrix must cover ALL roles and ALL entities
- For each entity, fields must include: id (uuid), created_at (datetime), updated_at (datetime)
"""

async def design_system(intent: dict[str, Any], model: str) -> dict[str, Any]:
    """Stage 2: Convert intent into a full system architecture."""
    
    raw = generate_json(
    SYSTEM_PROMPT,
    f"Design the system for this intent:\n\n{json.dumps(intent, indent=2)}"
)
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    
    return json.loads(raw)
