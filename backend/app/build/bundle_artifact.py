import shutil
import zipfile
from pathlib import Path

from app.models import AIProcessedCode


def create_source_bundle(
    workspace: Path,
    processed: AIProcessedCode,
    app_name: str,
    output_dir: Path,
) -> Path:
    entry = processed.entry_point or "main.py"
    (workspace / entry).write_text(processed.code, encoding="utf-8")
    for rel_path, content in processed.config_files.items():
        dest = workspace / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")

    readme = workspace / "PYFORGE_README.txt"
    readme.write_text(
        f"PyForge AI-prepared project: {app_name}\n\n"
        "Cloud hosting cannot run Docker builds. This bundle contains AI-fixed code "
        "and config files. Build locally with Docker Compose or a VPS — see README.\n",
        encoding="utf-8",
    )

    zip_path = output_dir / f"{app_name}-pyforge-bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in workspace.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(workspace))
    shutil.rmtree(workspace, ignore_errors=True)
    return zip_path
