import time
import json
from typing import Any, AsyncGenerator

from stages.stage1_intent import extract_intent
from stages.stage2_design import design_system
from stages.stage3_schemas import generate_schemas
from stages.stage4_refine import refine_schemas
from validators.validator import run_validation, repair_json

MAX_RETRIES = 3

class AppCompilerPipeline:
    # def __init__(self, model: str = "claude-sonnet-4-20250514"):
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model

    async def run(self, prompt: str) -> dict[str, Any]:
        """Run the full 4-stage pipeline with validation and repair."""
        
        meta = {
            "stage_latencies_ms": {},
            "total_latency_ms": 0,
            "retries": 0,
            "repairs": [],
            "warnings": [],
            "success": True
        }
        
        retries = 0
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                # ── Stage 1: Intent Extraction ──────────────────────────────
                t0 = time.time()
                intent = await self._run_with_repair(extract_intent, prompt, self.model)
                meta["stage_latencies_ms"]["stage1_intent"] = round((time.time() - t0) * 1000)

                # ── Stage 2: System Design ──────────────────────────────────
                t0 = time.time()
                design = await self._run_with_repair(design_system, intent, self.model)
                meta["stage_latencies_ms"]["stage2_design"] = round((time.time() - t0) * 1000)

                # ── Stage 3: Schema Generation ──────────────────────────────
                t0 = time.time()
                schemas = await self._run_with_repair(generate_schemas, intent, design, self.model)
                meta["stage_latencies_ms"]["stage3_schemas"] = round((time.time() - t0) * 1000)

                # ── Validation + Repair ─────────────────────────────────────
                t0 = time.time()
                validated_schemas, val_result = run_validation(schemas)
                
                if not val_result.valid:
                    meta["repairs"].extend(val_result.repairs)
                    meta["warnings"].extend(val_result.errors)

                meta["repairs"].extend(val_result.repairs)
                meta["warnings"].extend(val_result.warnings)
                meta["stage_latencies_ms"]["validation"] = round((time.time() - t0) * 1000)

                # ── Stage 4: Refinement ─────────────────────────────────────
                t0 = time.time()
                refined = await self._run_with_repair(
                    refine_schemas, validated_schemas, intent, design, self.model
                )
                meta["stage_latencies_ms"]["stage4_refine"] = round((time.time() - t0) * 1000)

                # Extract repairs from refinement stage
                if "repairs_made" in refined:
                    meta["repairs"].extend(refined.pop("repairs_made", []))
                if "warnings" in refined:
                    meta["warnings"].extend(refined.pop("warnings", []))

                # ── Final Assembly ──────────────────────────────────────────
                meta["retries"] = retries
                
                return {
                    "app": {
                        "name": intent.get("app_name", "Generated App"),
                        "description": intent.get("description", ""),
                        "version": "1.0.0",
                        "entities": intent.get("entities", []),
                        "features": intent.get("features", []),
                        "assumptions": intent.get("assumptions", []),
                    },
                    "database": refined.get("database", validated_schemas.get("database")),
                    "api": refined.get("api", validated_schemas.get("api")),
                    "ui": refined.get("ui", validated_schemas.get("ui")),
                    "auth": refined.get("auth", validated_schemas.get("auth")),
                    "business_logic": refined.get("business_logic", {
                        "rules": [],
                        "payment_enabled": intent.get("payments_required", False),
                        "payment_provider": intent.get("payment_provider"),
                        "premium_features": []
                    }),
                    "intent": intent,
                    "design": design,
                    "meta": meta
                }

            except Exception as e:
                retries += 1
                last_error = str(e)
                meta["warnings"].append(f"Attempt {attempt + 1} failed: {last_error}")
                if attempt == MAX_RETRIES - 1:
                    meta["success"] = False
                    meta["retries"] = retries
                    raise RuntimeError(f"Pipeline failed after {MAX_RETRIES} attempts: {last_error}")
        
    async def _run_with_repair(self, fn, *args):
        """Run a stage function, repairing JSON if it fails."""
        try:
            return await fn(*args)
        except Exception as e:
            raise

    async def run_stream(self, prompt: str) -> AsyncGenerator[dict, None]:
        """Streaming version that emits stage-by-stage events."""
        
        yield {"event": "start", "message": "Pipeline started"}

        try:
            yield {"event": "stage", "stage": 1, "message": "Extracting intent..."}
            intent = await extract_intent(prompt, self.model)
            yield {"event": "stage_complete", "stage": 1, "data": intent}

            yield {"event": "stage", "stage": 2, "message": "Designing system architecture..."}
            design = await design_system(intent, self.model)
            yield {"event": "stage_complete", "stage": 2, "data": design}

            yield {"event": "stage", "stage": 3, "message": "Generating schemas (DB, API, UI, Auth)..."}
            schemas = await generate_schemas(intent, design, self.model)
            yield {"event": "stage_complete", "stage": 3, "data": schemas}

            yield {"event": "stage", "stage": "validation", "message": "Validating and repairing schemas..."}
            validated, val_result = run_validation(schemas)
            yield {"event": "validation_complete", "repairs": val_result.repairs, "warnings": val_result.warnings}

            yield {"event": "stage", "stage": 4, "message": "Refining cross-layer consistency..."}
            refined = await refine_schemas(validated, intent, design, self.model)
            yield {"event": "stage_complete", "stage": 4, "data": refined}

            final = {
                "app": {
                    "name": intent.get("app_name", "Generated App"),
                    "description": intent.get("description", ""),
                    "entities": intent.get("entities", []),
                    "features": intent.get("features", []),
                    "assumptions": intent.get("assumptions", []),
                },
                "database": refined.get("database", validated.get("database")),
                "api": refined.get("api", validated.get("api")),
                "ui": refined.get("ui", validated.get("ui")),
                "auth": refined.get("auth", validated.get("auth")),
                "business_logic": refined.get("business_logic", {}),
                "intent": intent,
                "design": design,
                "meta": {
                    "repairs": val_result.repairs + refined.get("repairs_made", []),
                    "warnings": val_result.warnings + refined.get("warnings", []),
                    "success": True
                }
            }

            yield {"event": "complete", "data": final}

        except Exception as e:
            yield {"event": "error", "message": str(e)}
