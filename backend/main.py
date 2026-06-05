from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import time
import json
import asyncio

from pipeline import AppCompilerPipeline
from eval_runner import EvalRunner

app = FastAPI(title="App Compiler API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompileRequest(BaseModel):
    prompt: str
    # model: Optional[str] = "claude-sonnet-4-20250514"
    model: Optional[str] = "gemini-2.5-flash"

class EvalRequest(BaseModel):
    run_type: Optional[str] = "all"  # "all", "real", "edge"

@app.post("/compile")
async def compile_app(request: CompileRequest):
    if not request.prompt or len(request.prompt.strip()) < 5:
        raise HTTPException(status_code=400, detail="Prompt too short or empty")
    
    pipeline = AppCompilerPipeline(model=request.model)
    start = time.time()
    
    result = await pipeline.run(request.prompt)
    result["meta"]["total_latency_ms"] = round((time.time() - start) * 1000)
    
    return result

@app.post("/compile/stream")
async def compile_app_stream(request: CompileRequest):
    pipeline = AppCompilerPipeline(model=request.model)
    
    async def generate():
        async for event in pipeline.run_stream(request.prompt):
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0)
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/eval")
async def run_eval(request: EvalRequest):
    runner = EvalRunner()
    results = await runner.run(request.run_type)
    return results

@app.get("/health")
async def health():
    return {"status": "ok", "service": "app-compiler"}
