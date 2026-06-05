from llm import generate_json
import json
import re
from typing import Any


SYSTEM_PROMPT = """You are an intent extraction engine for a software compiler system.

Your ONLY job: parse a natural language app description into a structured JSON object.

Return ONLY valid JSON. No markdown, no explanation, no preamble. Just JSON.

Output schema:
{
  "app_name": "string - inferred app name",
  "app_type": "string - e.g. CRM, ecommerce, dashboard, social, booking, etc.",
  "description": "string - 1-2 sentence summary",
  "entities": ["list of core data entities e.g. User, Contact, Order, Product"],
  "features": ["list of features e.g. login, dashboard, payments, role-based access"],
  "roles": ["list of user roles e.g. admin, user, manager, guest"],
  "auth_required": true/false,
  "payments_required": true/false,
  "payment_provider": "stripe | paypal | null",
  "premium_plan": true/false,
  "analytics_required": true/false,
  "ambiguities": ["list of unclear or underspecified requirements"],
  "assumptions": ["list of reasonable assumptions made to fill gaps"]
}

Rules:
- If something is unclear, add it to ambiguities
- Make reasonable assumptions and document them
- Always extract at minimum: entities, features, roles
- If no roles mentioned, default to ["admin", "user"]
- If auth not mentioned but app has users, assume auth_required: true
"""

async def extract_intent(prompt: str, model: str) -> dict[str, Any]:
    """Stage 1: Extract structured intent from natural language prompt."""
    
    # response = client.messages.create(
    #     model=model,
    #     max_tokens=1500,
    #     system=SYSTEM_PROMPT,
    #     messages=[
    #         {"role": "user", "content": f"Extract intent from this app description:\n\n{prompt}"}
    #     ]
    # )
    
    # raw = response.content[0].text.strip()

    raw = generate_json(
    SYSTEM_PROMPT,
    f"Extract intent from this app description:\n\n{prompt}"
)
    
    # Strip markdown fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()
    
    return json.loads(raw)
