import asyncio
import json
import shutil
import tarfile
import tempfile
from pathlib import Path

from app.config import settings
from app.models import AIProcessedCode, BuildTarget
from app.services.job_manager import BuildJob


def _write_project(workspace: Path, processed: AIProcessedCode, app_name: str) -> Path:
    entry = processed.entry_point or "main.py"
    (workspace / entry).write_text(processed.code, encoding="utf-8")
    for rel_path, content in processed.config_files.items():
        dest = workspace / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    manifest = {
        "app_name": app_name,
        "entry_point": entry,
        "target": "build",
    }
    (workspace / "pyforge_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return workspace


def _create_build_context(workspace: Path) -> Path:
    archive = workspace.parent / f"{workspace.name}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(workspace, arcname="project")
    return archive


async def _stream_docker_logs(
    job: BuildJob,
    proc: asyncio.subprocess.Process,
) -> tuple[int, str]:
    assert proc.stdout is not None
    stderr_data: list[str] = []
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip()
        if text:
            job.append_log(text)
    await proc.wait()
    if proc.stderr:
        err = await proc.stderr.read()
        if err:
            stderr_data.append(err.decode("utf-8", errors="replace"))
    return proc.returncode or 0, "".join(stderr_data)


def _image_for_target(target: BuildTarget) -> str:
    if target == BuildTarget.ANDROID_APK:
        return settings.android_image
    return settings.desktop_image


def _container_script(target: BuildTarget) -> str:
    if target == BuildTarget.ANDROID_APK:
        return "/scripts/build_android.sh"
    if target in (BuildTarget.DESKTOP_WINDOWS, BuildTarget.DESKTOP_MAC, BuildTarget.DESKTOP_LINUX):
        return "/scripts/build_desktop.sh"
    return "/scripts/build_ios.sh"


async def run_docker_build(
    job: BuildJob,
    processed: AIProcessedCode,
    app_name: str,
    target: BuildTarget,
) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=f"pyforge_{job.job_id}_"))
    try:
        _write_project(workspace, processed, app_name)
        archive = _create_build_context(workspace)

        artifacts_host = Path(settings.artifacts_dir) / job.job_id
        artifacts_host.mkdir(parents=True, exist_ok=True)

        image = _image_for_target(target)
        script = _container_script(target)
        platform_flag: list[str] = []
        if target == BuildTarget.DESKTOP_WINDOWS:
            platform_flag = ["--platform", "linux/amd64"]

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            *platform_flag,
            "-v",
            f"{archive}:/build/context.tar.gz:ro",
            "-v",
            f"{artifacts_host.resolve()}:/output",
            "-e",
            f"BUILD_TARGET={target.value}",
            "-e",
            f"APP_NAME={app_name}",
            image,
            "bash",
            script,
        ]

        job.append_log(f"Starting isolated build container: {image}")
        proc = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        returncode, stderr = await asyncio.wait_for(
            _stream_docker_logs(job, proc),
            timeout=settings.build_timeout_seconds,
        )

        if returncode != 0:
            raise RuntimeError(f"Build container failed (exit {returncode}): {stderr[:2000]}")

        artifacts = list(artifacts_host.glob("*"))
        binaries = [p for p in artifacts if p.is_file() and p.suffix.lower() in (".exe", ".apk", ".ipa", "", ".bin")]
        if not binaries:
            binaries = [p for p in artifacts if p.is_file()]

        if not binaries:
            raise RuntimeError("Build completed but no artifact was produced.")

        artifact = binaries[0]
        job.artifact_path = artifact
        job.artifact_name = artifact.name
        job.append_log(f"Artifact ready: {artifact.name}")
        return artifact
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
        archive_path = workspace.parent / f"{workspace.name}.tar.gz"
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
