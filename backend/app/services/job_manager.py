import asyncio
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from app.config import settings
from app.models import BuildStatus, BuildTarget


@dataclass
class BuildJob:
    job_id: str
    target: BuildTarget
    status: BuildStatus = BuildStatus.QUEUED
    message: str = ""
    artifact_path: Optional[Path] = None
    artifact_name: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    log_subscribers: list[asyncio.Queue[str]] = field(default_factory=list)
    _log_history: list[str] = field(default_factory=list)

    def append_log(self, line: str) -> None:
        stamped = f"[{time.strftime('%H:%M:%S')}] {line}"
        self._log_history.append(stamped)
        for queue in self.log_subscribers:
            try:
                queue.put_nowait(stamped)
            except asyncio.QueueFull:
                pass

    def get_logs(self) -> list[str]:
        return list(self._log_history)


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, BuildJob] = {}
        self._lock = asyncio.Lock()
        Path(settings.artifacts_dir).mkdir(parents=True, exist_ok=True)

    def create_job(self, target: BuildTarget) -> BuildJob:
        job_id = str(uuid.uuid4())
        job = BuildJob(job_id=job_id, target=target)
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[BuildJob]:
        return self._jobs.get(job_id)

    def subscribe_logs(self, job_id: str) -> tuple[Optional[BuildJob], asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=500)
        job = self.get_job(job_id)
        if job:
            for line in job.get_logs():
                queue.put_nowait(line)
            job.log_subscribers.append(queue)
        return job, queue

    def unsubscribe_logs(self, job_id: str, queue: asyncio.Queue[str]) -> None:
        job = self.get_job(job_id)
        if job and queue in job.log_subscribers:
            job.log_subscribers.remove(queue)

    async def cleanup_expired(self) -> None:
        now = time.time()
        expired: list[str] = []
        for job_id, job in self._jobs.items():
            if now - job.created_at > settings.artifact_ttl_seconds:
                expired.append(job_id)
                if job.artifact_path and job.artifact_path.exists():
                    try:
                        job.artifact_path.unlink()
                    except OSError:
                        pass
        for job_id in expired:
            del self._jobs[job_id]

    async def run_periodic_cleanup(self) -> None:
        while True:
            await self.cleanup_expired()
            await asyncio.sleep(300)


job_manager = JobManager()
