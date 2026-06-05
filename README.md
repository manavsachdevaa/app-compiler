# ⚡ App Compiler — Natural Language → Executable App Config

> **AI Engineer Internship Demo Task**
> Converts natural language app descriptions into complete, validated, cross-layer consistent app configurations — like a compiler, but for software generation.

---

## 🏗️ Architecture Overview

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Stage 1: Intent Extraction                     │
│  - Parses NL → structured intent JSON           │
│  - Extracts: entities, features, roles, flags   │
│  - Documents ambiguities + assumptions          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  Stage 2: System Design                         │
│  - Intent → full system architecture            │
│  - Defines: entities, relations, flows          │
│  - Builds: role access matrix                   │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  Stage 3: Schema Generation (4 parallel calls)  │
│  ├── DB Schema (tables, fields, FK, indexes)    │
│  ├── API Schema (endpoints, params, roles)      │
│  ├── UI Schema (pages, components, fields)      │
│  └── Auth Schema (roles, permissions, JWT)      │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  Validation + Repair Engine                     │
│  ├── JSON repair (syntax errors)                │
│  ├── Missing required fields auto-fill          │
│  ├── FK integrity checks                        │
│  ├── Cross-layer field mapping validation       │
│  └── Auth role consistency enforcement          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│  Stage 4: Refinement Layer                      │
│  - Cross-layer consistency resolution           │
│  - Business logic rule generation               │
│  - Premium gating / role access rules           │
│  - Logs all repairs made                        │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
        Final AppConfig JSON (validated)
```

---

## 📁 Project Structure

```
app-compiler/
├── backend/
│   ├── main.py                  # FastAPI server
│   ├── pipeline.py              # 4-stage pipeline orchestrator
│   ├── eval_runner.py           # Evaluation framework (20 test cases)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── stages/
│   │   ├── stage1_intent.py     # NL → structured intent
│   │   ├── stage2_design.py     # Intent → system architecture
│   │   ├── stage3_schemas.py    # Generate DB/API/UI/Auth schemas
│   │   └── stage4_refine.py     # Cross-layer consistency + business logic
│   ├── validators/
│   │   └── validator.py         # Validation + auto-repair engine
│   └── schemas/
│       └── app_schema.py        # Pydantic models for strict typing
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Full React UI
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

## 🚀 Quick Start

### Option 1: Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Option 2: Docker Compose
```bash
export ANTHROPIC_API_KEY=your_key_here
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## 📤 API Reference

### `POST /compile`
Compile a prompt into a full app config (synchronous).

```json
{
  "prompt": "Build a CRM with login, contacts, dashboard, role-based access..."
}
```

**Response:** Full `AppConfig` JSON

### `POST /compile/stream`
Server-sent events streaming version. Emits stage-by-stage progress.

**Event types:** `start`, `stage`, `stage_complete`, `validation_complete`, `complete`, `error`

### `POST /eval`
Run the evaluation suite.

```json
{ "run_type": "all" }  // "all" | "real" | "edge"
```

---

## 🔍 Output Schema

```json
{
  "app": {
    "name": "CRM Pro",
    "description": "...",
    "entities": ["User", "Contact", "Deal"],
    "features": ["login", "dashboard", "payments"],
    "assumptions": ["Stripe used for payments", ...]
  },
  "database": {
    "tables": [
      {
        "name": "users",
        "fields": [
          { "name": "id", "type": "uuid", "primary_key": true },
          { "name": "email", "type": "string", "unique": true },
          { "name": "role", "type": "enum", "enum_values": ["admin", "user"] },
          ...
        ],
        "relations": ["User has_many Contacts"]
      }
    ]
  },
  "api": {
    "base_path": "/api/v1",
    "endpoints": [
      {
        "method": "POST",
        "path": "/auth/login",
        "auth_required": false,
        "body_params": [{"name": "email", "type": "string"}, ...],
        "response_fields": ["token", "user"],
        "db_table": "users"
      }
    ]
  },
  "ui": {
    "pages": [
      {
        "name": "Dashboard",
        "route": "/dashboard",
        "auth_required": true,
        "roles": ["admin", "user"],
        "components": [
          {
            "id": "contacts_table",
            "type": "table",
            "api_endpoint": "/api/v1/contacts",
            "roles": ["admin", "user"]
          }
        ]
      }
    ]
  },
  "auth": {
    "strategy": "jwt",
    "roles": [
      {
        "name": "admin",
        "permissions": [{ "resource": "*", "actions": ["*"] }]
      }
    ]
  },
  "business_logic": {
    "rules": [
      {
        "name": "premium_gate_analytics",
        "type": "premium_gate",
        "condition": "user.plan !== 'premium'",
        "action": "redirect_to_upgrade"
      }
    ],
    "payment_enabled": true,
    "payment_provider": "stripe"
  },
  "meta": {
    "stage_latencies_ms": {
      "stage1_intent": 820,
      "stage2_design": 1240,
      "stage3_schemas": 3100,
      "validation": 12,
      "stage4_refine": 1800
    },
    "retries": 0,
    "repairs": ["Added missing 'id' field to table contacts", ...],
    "warnings": [],
    "success": true
  }
}
```

---

## 🛡️ Validation + Repair Engine

The engine catches and fixes these automatically:

| Issue | Action |
|-------|--------|
| Invalid JSON syntax | Claude-powered JSON repair |
| Missing `id`, `created_at`, `updated_at` fields | Auto-add to every table |
| Missing `/auth/login`, `/auth/register` endpoints | Auto-inject |
| Missing `/login` page in UI | Auto-inject |
| Malformed FK references (`table` → `table.id`) | Auto-fix |
| Undefined roles on pages/components | Warning logged |
| API params not matching DB fields | Warning logged |
| No default role set | Auto-assign |
| Missing admin role | Auto-inject |

---

## 📊 Evaluation Framework

20 test cases: 10 real product prompts + 10 edge cases (vague, conflicting, incomplete, over-specified).

**Tracked metrics:**
- ✅ Success rate (overall, real, edge)
- ⏱️ Average latency (ms)
- 🔄 Average retries per run
- 🔧 Average repairs per run
- ❌ Failure type breakdown (invalid_json, timeout, rate_limit, missing_field, schema_mismatch)
- 💰 Estimated cost per run

---

## ⚖️ Cost vs Quality Tradeoffs

| Factor | Decision |
|--------|----------|
| Model | Claude Sonnet 4 — best balance of quality + speed vs Opus |
| Stage count | 4 separate calls — better than 1 (quality) but fewer than 6+ (cost) |
| Max retries | 3 — handles transient failures without runaway cost |
| Repair strategy | Surgical repair (fix specific layer) vs full retry (expensive) |
| Streaming | SSE streaming — better UX, same cost |
| Schema size | Capped at 4000 tokens per stage — prevents runaway generation |

**Estimated cost per compile:** ~$0.024 (8K tokens avg × Sonnet pricing)

---

## 🔑 Key Design Decisions

1. **Single prompt = rejected.** The task explicitly requires multi-stage. Each stage has a focused system prompt that produces a smaller, verifiable artifact.

2. **Validator runs between Stage 3 and Stage 4.** This means Stage 4 (refinement) operates on already-clean schemas, reducing hallucination surface area.

3. **Repair is surgical, not brute-force.** When a field is missing, we add it. We don't re-run the whole pipeline.

4. **Pydantic for type safety.** `AppConfig` and all sub-schemas are Pydantic models, providing runtime validation with zero extra prompting.

5. **Assumptions are documented.** Every ambiguity is turned into a documented assumption in the output, making the system auditable.
