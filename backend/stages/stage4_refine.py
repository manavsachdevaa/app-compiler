import json
import re
from typing import Any

from llm import generate_json
SYSTEM_PROMPT = """You are a schema consistency engine. You receive a combined app schema and must detect and fix ALL cross-layer inconsistencies.

Return ONLY valid JSON with this structure. No markdown, no preamble.

{
  "database": { ... same structure as input but fixed ... },
  "api": { ... },
  "ui": { ... },
  "auth": { ... },
  "business_logic": {
    "rules": [
      {
        "name": "rule name",
        "type": "premium_gate|role_access|validation|workflow",
        "description": "what this rule enforces",
        "condition": "when this applies",
        "action": "what happens",
        "affected_endpoints": ["/api/v1/..."],
        "affected_ui": ["component_id"]
      }
    ],
    "payment_enabled": true/false,
    "payment_provider": "stripe|null",
    "premium_features": ["list of premium feature names"]
  },
  "repairs_made": ["list of fixes applied"],
  "warnings": ["non-critical issues found"]
}

Cross-layer consistency rules to enforce:
1. DB-API: Every API endpoint's body_params must match fields in the referenced db_table
2. API-UI: Every UI form field's api_field must match a body_param in the linked api_endpoint
3. Role consistency: Roles in UI pages/components must exist in auth.roles
4. Role consistency: Roles in API endpoints must exist in auth.roles
5. FK integrity: All foreign_key references must point to existing tables
6. Auth entity: There must be a users table in DB and /auth/* endpoints in API
7. Premium gating: If payment_enabled, add business_logic rules for premium features
8. Missing endpoints: If a UI component has an api_endpoint, that endpoint must exist

For each inconsistency found:
- Fix it directly in the output
- Log what you fixed in repairs_made
"""

async def refine_schemas(schemas: dict[str, Any], intent: dict, design: dict, model: str) -> dict[str, Any]:
    """Stage 4: Detect and repair cross-layer inconsistencies."""
    
    full_context = {
        "intent": intent,
        "design": design,
        "schemas": schemas
    }
    
    raw = generate_json(
    SYSTEM_PROMPT,
    f"Refine and fix this app schema:\n\n{json.dumps(full_context, indent=2)}"
    )
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    
    return json.loads(raw)
