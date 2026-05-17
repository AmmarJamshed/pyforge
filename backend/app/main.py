import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.build.pipeline import schedule_build
from app.config import settings
from app.demo_samples import DEFAULT_SAMPLE, SAMPLES
from app.models import BuildJobResponse, BuildRequest, BuildStatus
from app.services.ai_service import ai_configured
from app.services.job_manager import job_manager

SAMPLE_CODE = SAMPLES[DEFAULT_SAMPLE]["code"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(job_manager.run_periodic_cleanup())
    Path(settings.artifacts_dir).mkdir(parents=True, exist_ok=True)
    yield
    cleanup_task.cancel()


app = FastAPI(
    title="PyForge API",
    description="AI-powered Python to native app builder",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "ai_provider": settings.ai_provider,
        "ai_configured": ai_configured(),
        "groq_configured": bool(settings.groq_api_key),
    }


@app.get("/api/ai-providers")
async def ai_providers():
    return {
        "current": settings.ai_provider,
        "configured": ai_configured(),
        "options": [
            {"id": "gemini", "name": "Google Gemini", "env": ["GEMINI_API_KEY"], "note": "Free tier at aistudio.google.com"},
            {"id": "openrouter", "name": "OpenRouter", "env": ["OPENAI_API_KEY", "OPENAI_MODEL"], "note": "Many models, some free"},
            {"id": "openai", "name": "OpenAI", "env": ["OPENAI_API_KEY"], "note": "GPT-4o-mini etc."},
            {"id": "ollama", "name": "Ollama (local)", "env": ["OPENAI_BASE_URL"], "note": "Free, self-hosted only"},
            {"id": "groq", "name": "Groq", "env": ["GROQ_API_KEY"], "note": "Fast; strict free-tier token limits"},
        ],
    }


@app.get("/api/sample-code")
async def sample_code(sample: str = DEFAULT_SAMPLE):
    entry = SAMPLES.get(sample) or SAMPLES[DEFAULT_SAMPLE]
    return {
        "code": entry["code"],
        "app_name": entry["app_name"],
        "name": entry["name"],
        "sample_id": sample if sample in SAMPLES else DEFAULT_SAMPLE,
    }


@app.get("/api/samples")
async def list_samples():
    return {
        "samples": [
            {"id": sid, "name": meta["name"], "app_name": meta["app_name"]}
            for sid, meta in SAMPLES.items()
        ]
    }


@app.post("/api/build", response_model=BuildJobResponse)
async def start_build(request: BuildRequest):
    if len(request.code) > settings.max_code_length:
        raise HTTPException(status_code=400, detail="Code exceeds maximum length.")

    if not ai_configured():
        raise HTTPException(
            status_code=503,
            detail=f"AI provider '{settings.ai_provider}' is not configured. Set API keys on the server.",
        )

    job = job_manager.create_job(request.target)
    job.append_log(f"Build queued: {request.target.value} / {request.app_name}")
    schedule_build(job, request.code, request.target, request.app_name)

    return BuildJobResponse(job_id=job.job_id, status=job.status, message=job.message)


@app.get("/api/build/{job_id}")
async def get_build_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "message": job.message,
        "artifact_name": job.artifact_name,
        "download_ready": job.status == BuildStatus.COMPLETED and job.artifact_path is not None,
    }


@app.get("/api/build/{job_id}/download")
async def download_artifact(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != BuildStatus.COMPLETED or not job.artifact_path or not job.artifact_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not available.")

    return FileResponse(
        path=job.artifact_path,
        filename=job.artifact_name or job.artifact_path.name,
        media_type="application/octet-stream",
    )


@app.websocket("/ws/build/{job_id}")
async def build_logs_websocket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    job, queue = job_manager.subscribe_logs(job_id)
    if not job:
        await websocket.send_json({"type": "error", "message": "Job not found."})
        await websocket.close()
        return

    try:
        await websocket.send_json({
            "type": "status",
            "status": job.status,
            "message": job.message,
            "history": job.get_logs(),
        })

        while True:
            if job.status in (BuildStatus.COMPLETED, BuildStatus.FAILED):
                try:
                    line = await asyncio.wait_for(queue.get(), timeout=0.5)
                    await websocket.send_json({"type": "log", "line": line})
                except asyncio.TimeoutError:
                    pass
                await websocket.send_json({
                    "type": "status",
                    "status": job.status,
                    "message": job.message,
                    "download_ready": job.status == BuildStatus.COMPLETED,
                    "artifact_name": job.artifact_name,
                })
                break

            try:
                line = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json({"type": "log", "line": line})
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "status",
                    "status": job.status,
                    "message": job.message,
                })
    except WebSocketDisconnect:
        pass
    finally:
        job_manager.unsubscribe_logs(job_id, queue)
