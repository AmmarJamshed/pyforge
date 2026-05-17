import platform
import tempfile
from pathlib import Path

from app.build.bundle_artifact import create_source_bundle
from app.build.docker_runner import run_docker_build
from app.config import settings
from app.models import BuildStatus, BuildTarget
from app.services.groq_service import process_code_with_ai
from app.services.job_manager import BuildJob, job_manager


async def execute_build_pipeline(
    job: BuildJob,
    code: str,
    target: BuildTarget,
    app_name: str,
) -> None:
    try:
        job.status = BuildStatus.AI_PROCESSING
        job.message = "Analyzing and fixing code with Groq AI..."
        job.append_log("Sending code to Groq for analysis...")

        processed = await process_code_with_ai(code, target, app_name)
        job.append_log(f"AI processing complete: {processed.notes[:500]}")

        if target == BuildTarget.IOS_IPA and platform.system() != "Darwin":
            job.status = BuildStatus.FAILED
            job.message = (
                "iOS IPA builds require a macOS host with Xcode and kivy-ios toolchain. "
                "Self-host PyForge on macOS for iOS targets."
            )
            job.append_log(job.message)
            return

        if not settings.docker_builds_enabled:
            job.status = BuildStatus.BUILDING
            job.message = "Cloud mode: packaging AI-prepared source bundle..."
            job.append_log(
                "Docker builds are disabled on this host. Creating downloadable source ZIP "
                "(build APK/EXE locally with Docker Compose on a VPS)."
            )
            workspace = Path(tempfile.mkdtemp(prefix=f"pyforge_bundle_{job.job_id}_"))
            out_dir = Path(settings.artifacts_dir) / job.job_id
            out_dir.mkdir(parents=True, exist_ok=True)
            artifact = create_source_bundle(workspace, processed, app_name, out_dir)
            job.artifact_path = artifact
            job.artifact_name = artifact.name
            job.append_log(f"Bundle ready: {artifact.name}")
        else:
            job.status = BuildStatus.BUILDING
            job.message = "Running sandboxed build..."
            job.append_log(f"Launching Docker build for target: {target.value}")
            await run_docker_build(job, processed, app_name, target)

        job.status = BuildStatus.COMPLETED
        job.message = "Build completed successfully."
        job.append_log("Build finished. Download your artifact from the UI.")
    except Exception as exc:
        job.status = BuildStatus.FAILED
        job.message = str(exc)
        job.append_log(f"ERROR: {exc}")


def schedule_build(job: BuildJob, code: str, target: BuildTarget, app_name: str) -> None:
    import asyncio

    asyncio.create_task(execute_build_pipeline(job, code, target, app_name))
