import time
import json
import asyncio
from typing import Any
from pipeline import AppCompilerPipeline

REAL_PROMPTS = [
    "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
    "Create an e-commerce platform with product listings, shopping cart, checkout with Stripe, order tracking, and admin panel.",
    "Build a project management tool like Trello with boards, cards, lists, team members, due dates, and file attachments.",
    "Create a booking system for a medical clinic with patient management, appointment scheduling, doctor profiles, and email reminders.",
    "Build a learning management system with courses, lessons, quizzes, student progress tracking, and certificate generation.",
    "Create a SaaS analytics dashboard with multi-tenant support, custom charts, data export, team collaboration, and usage billing.",
    "Build a job board platform where companies post jobs, candidates apply, and admins moderate listings with subscription plans.",
    "Create a restaurant management system with menu management, table reservations, order processing, and kitchen display.",
    "Build a social media platform with user profiles, posts, comments, likes, followers, and content moderation.",
    "Create a freelance marketplace where clients post projects and freelancers bid, with escrow payments and reviews.",
]

EDGE_CASES = [
    # Vague
    "Build me an app",
    "I need a website with users and stuff",
    # Conflicting
    "Build a public app where all users can see everything but also has private user data and GDPR compliance.",
    "Create a free platform with premium features where all features are also free for all users.",
    # Incomplete
    "Build something like Airbnb",
    "Create an app with login and dashboard",
    # Over-specified
    "Build a CRM with 50 custom fields per contact, 200 API endpoints, real-time collaboration, AI-powered suggestions, blockchain audit trail, AR/VR interface, and quantum encryption.",
    # Ambiguous roles
    "Build a platform for teachers and students but also parents can login sometimes.",
    # Contradictory auth
    "Create an app that doesn't require login but has personalized dashboards for each user.",
    # Missing core entity
    "Build a payment processing system with invoices, subscriptions, and billing history.",
]

class EvalRunner:
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model

    async def _run_single(self, prompt: str, label: str) -> dict[str, Any]:
        pipeline = AppCompilerPipeline(model=self.model)
        start = time.time()
        retries = 0
        success = False
        failure_type = None
        output = None
        repairs = []
        warnings = []

        try:
            result = await pipeline.run(prompt)
            success = True
            output = result
            retries = result.get("meta", {}).get("retries", 0)
            repairs = result.get("meta", {}).get("repairs", [])
            warnings = result.get("meta", {}).get("warnings", [])
        except Exception as e:
            failure_type = classify_failure(str(e))
            warnings = [str(e)]

        latency = round((time.time() - start) * 1000)

        return {
            "label": label,
            "prompt": prompt[:100] + ("..." if len(prompt) > 100 else ""),
            "success": success,
            "latency_ms": latency,
            "retries": retries,
            "repairs_count": len(repairs),
            "warnings_count": len(warnings),
            "failure_type": failure_type,
            "output_summary": summarize_output(output) if output else None,
        }

    async def run(self, run_type: str = "all") -> dict[str, Any]:
        prompts = []
        
        if run_type in ("all", "real"):
            prompts += [(p, f"real_{i+1}") for i, p in enumerate(REAL_PROMPTS)]
        if run_type in ("all", "edge"):
            prompts += [(p, f"edge_{i+1}") for i, p in enumerate(EDGE_CASES)]

        results = []
        # Run sequentially to avoid rate limits
        for prompt, label in prompts:
            r = await self._run_single(prompt, label)
            results.append(r)
            await asyncio.sleep(1)  # small delay between runs

        return compute_metrics(results)


def classify_failure(error: str) -> str:
    e = error.lower()
    if "json" in e or "parse" in e or "decode" in e:
        return "invalid_json"
    if "timeout" in e or "time" in e:
        return "timeout"
    if "rate" in e or "limit" in e:
        return "rate_limit"
    if "key" in e or "field" in e:
        return "missing_field"
    if "schema" in e or "mismatch" in e:
        return "schema_mismatch"
    return "unknown"


def summarize_output(output: dict) -> dict:
    if not output:
        return {}
    return {
        "app_name": output.get("app", {}).get("name", ""),
        "tables": len(output.get("database", {}).get("tables", [])),
        "endpoints": len(output.get("api", {}).get("endpoints", [])),
        "pages": len(output.get("ui", {}).get("pages", [])),
        "roles": len(output.get("auth", {}).get("roles", [])),
        "business_rules": len(output.get("business_logic", {}).get("rules", [])),
    }


def compute_metrics(results: list[dict]) -> dict[str, Any]:
    total = len(results)
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    
    real_results = [r for r in results if r["label"].startswith("real_")]
    edge_results = [r for r in results if r["label"].startswith("edge_")]

    failure_types: dict[str, int] = {}
    for r in failures:
        ft = r.get("failure_type", "unknown")
        failure_types[ft] = failure_types.get(ft, 0) + 1

    avg_latency = sum(r["latency_ms"] for r in results) / total if total else 0
    avg_retries = sum(r["retries"] for r in results) / total if total else 0
    avg_repairs = sum(r["repairs_count"] for r in results) / total if total else 0

    return {
        "summary": {
            "total_prompts": total,
            "success_count": len(successes),
            "failure_count": len(failures),
            "success_rate_pct": round(len(successes) / total * 100, 1) if total else 0,
            "real_success_rate_pct": round(
                len([r for r in real_results if r["success"]]) / len(real_results) * 100, 1
            ) if real_results else 0,
            "edge_success_rate_pct": round(
                len([r for r in edge_results if r["success"]]) / len(edge_results) * 100, 1
            ) if edge_results else 0,
            "avg_latency_ms": round(avg_latency),
            "avg_retries": round(avg_retries, 2),
            "avg_repairs_per_run": round(avg_repairs, 2),
            "failure_types": failure_types,
        },
        "results": results,
        "cost_analysis": {
            "note": "Approximate. Claude Sonnet 4 pricing.",
            "avg_tokens_per_run_estimate": 8000,
            "cost_per_run_usd_estimate": 0.024,
            "total_cost_usd_estimate": round(total * 0.024, 3),
        }
    }
