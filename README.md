# ⚡ App Compiler — Natural Language → Executable App Config

**AI Engineer Internship Demo Task**

Converts natural language app descriptions into complete, validated, cross-layer consistent app configurations — like a compiler, but for software generation.

---

# 🏗️ Architecture Overview

```text
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
│  Stage 3: Schema Generation (4 parallel calls) │
│  ├── DB Schema (tables, fields, FK, indexes)   │
│  ├── API Schema (endpoints, params, roles)     │
│  ├── UI Schema (pages, components, fields)     │
│  └── Auth Schema (roles, permissions, JWT)     │
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

# 📁 Project Structure

```text
app-compiler/
├── backend/
│   ├── main.py
│   ├── pipeline.py
│   ├── eval_runner.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── stages/
│   │   ├── stage1_intent.py
│   │   ├── stage2_design.py
│   │   ├── stage3_schemas.py
│   │   └── stage4_refine.py
│   ├── validators/
│   │   └── validator.py
│   └── schemas/
│       └── app_schema.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

---

# 🛠️ Tech Stack

### Frontend

* React
* Vite

### Backend

* FastAPI
* Pydantic

### AI

* Google Gemini 2.5 Flash

### Infrastructure

* Docker
* Docker Compose

---

# 🚀 Quick Start

## Option 1: Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `.env`

```env
GEMINI_API_KEY=your_api_key_here
```

Run:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

---

## Option 2: Docker Compose

```env
GEMINI_API_KEY=your_api_key_here
```

```bash
docker-compose up --build
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:3000
```

---

# 📤 API Reference

## POST /compile

Compile a prompt into a full app configuration.

Request:

```json
{
  "prompt": "Build a CRM with login, contacts, dashboard, role-based access..."
}
```

Response:

```json
{
  "app": {},
  "database": {},
  "api": {},
  "ui": {},
  "auth": {},
  "business_logic": {}
}
```

---

## POST /compile/stream

Server-Sent Events (SSE) streaming endpoint.

Emits:

```text
start
stage
stage_complete
validation_complete
complete
error
```

---

## POST /eval

Run evaluation suite.

```json
{
  "run_type": "all"
}
```

Available:

```text
all
real
edge
```

---

# 🛡️ Validation + Repair Engine

The engine automatically detects and repairs:

| Issue                  | Action                     |
| ---------------------- | -------------------------- |
| Invalid JSON syntax    | Gemini-powered JSON repair |
| Missing id fields      | Auto-add                   |
| Missing timestamps     | Auto-add                   |
| Missing auth endpoints | Auto-inject                |
| Missing login page     | Auto-inject                |
| Broken FK references   | Auto-fix                   |
| Undefined roles        | Warning                    |
| API/DB mismatches      | Warning                    |
| Missing default role   | Auto-assign                |
| Missing admin role     | Auto-inject                |

---

# 📊 Evaluation Framework

20 benchmark prompts:

* 10 real-world product requests
* 10 edge-case prompts

Metrics tracked:

* ✅ Success Rate
* ⏱️ Average Latency
* 🔄 Average Retries
* 🔧 Average Repairs
* ❌ Failure Breakdown
* 💰 Estimated Cost

Failure categories:

```text
invalid_json
timeout
rate_limit
missing_field
schema_mismatch
```

---

# ⚖️ Cost vs Quality Tradeoffs

| Factor          | Decision                |
| --------------- | ----------------------- |
| Model           | Gemini 2.5 Flash        |
| Architecture    | 4-stage pipeline        |
| Retry Strategy  | Maximum 3 retries       |
| Repair Strategy | Surgical repair         |
| Streaming       | SSE                     |
| Schema Limits   | Token-capped generation |

Gemini 2.5 Flash was selected for its balance of:

* Structured JSON generation
* Low latency
* Low operational cost
* Reliable multi-step reasoning

---

# 🔑 Key Design Decisions

### Multi-Stage Architecture

A single prompt approach was intentionally avoided.

Each stage focuses on a specific responsibility:

1. Intent Extraction
2. System Design
3. Schema Generation
4. Refinement

This improves:

* Accuracy
* Validation
* Auditability
* Repairability

---

### Validation Before Refinement

The validator runs between Stage 3 and Stage 4.

This ensures refinement operates only on already-valid schemas.

---

### Surgical Repair Strategy

Instead of rerunning the entire pipeline:

* Missing fields are injected
* Broken references are repaired
* Invalid JSON is fixed

This reduces latency and cost.

---

### Strong Typing

Pydantic models enforce:

* Schema correctness
* Runtime validation
* Type safety

---

### Explicit Assumptions

Any ambiguity detected in the prompt is documented as an assumption in the generated output.

This makes the system transparent and auditable.

---

# 🎯 Example Output

The final generated configuration includes:

* Application Metadata
* Database Schema
* API Schema
* UI Schema
* Authentication Schema
* Business Logic Rules
* Validation Metadata
* Repair Logs
* Performance Metrics

All outputs are cross-layer validated before being returned.

---

# 📄 License

Built as an AI Engineer Internship Demo Project showcasing:

* LLM Orchestration
* Multi-Agent Style Pipelines
* Schema Generation
* Validation Systems
* Full-Stack Engineering
* Production-Oriented AI Architecture
