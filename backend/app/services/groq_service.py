import json
import re

from groq import Groq

from app.config import settings
from app.models import AIProcessedCode, BuildTarget

SYSTEM_PROMPT = """You are PyForge, an expert Python packaging assistant.
Analyze the user's Python code and prepare it for building a native application.

You MUST respond with valid JSON only (no markdown fences), using this exact schema:
{
  "code": "<complete build-ready Python source>",
  "entry_point": "<filename e.g. main.py>",
  "config_files": {
    "<relative/path>": "<file contents>"
  },
  "notes": "<brief explanation of changes made>"
}

Rules:
- Fix platform incompatibilities for the target.
- Ensure a proper if __name__ == '__main__' entry when needed.
- Add missing imports.
- For desktop targets: include a PyInstaller .spec file in config_files.
- For android_apk: include buildozer.spec and any required supporting files.
- For ios_ipa: include kivy-ios oriented configs (note macOS requirement in notes).
- Keep code self-contained; no network calls unless present in original.
- Do not include secrets or API keys.
"""

TARGET_HINTS = {
    BuildTarget.DESKTOP_WINDOWS: "Windows desktop EXE via PyInstaller (onefile, console=False if GUI).",
    BuildTarget.DESKTOP_MAC: "macOS desktop app via PyInstaller.",
    BuildTarget.DESKTOP_LINUX: "Linux desktop binary via PyInstaller.",
    BuildTarget.ANDROID_APK: "Android APK via Buildozer/Kivy. Include buildozer.spec.",
    BuildTarget.IOS_IPA: "iOS IPA via kivy-ios. Include toolchain hints in config_files.",
}


def _parse_ai_response(text: str) -> AIProcessedCode:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    data = json.loads(cleaned)
    return AIProcessedCode(
        code=data["code"],
        entry_point=data.get("entry_point", "main.py"),
        config_files=data.get("config_files", {}),
        notes=data.get("notes", ""),
    )


async def process_code_with_ai(code: str, target: BuildTarget, app_name: str) -> AIProcessedCode:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on the server.")

    client = Groq(api_key=settings.groq_api_key)
    user_message = (
        f"App name: {app_name}\n"
        f"Target platform: {target.value}\n"
        f"Build instructions: {TARGET_HINTS[target]}\n\n"
        f"User Python code:\n```python\n{code}\n```"
    )

    # Only currently supported Groq models (llama3-70b-8192 is decommissioned).
    default_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "llama-3.1-8b-instant",
    ]
    deprecated = {"llama3-70b-8192", "llama3-8b-8192"}

    candidates = [
        settings.groq_model,
        settings.groq_fallback_model,
        *default_models,
    ]
    models = [m for m in dict.fromkeys(c for c in candidates if c) if m not in deprecated]

    last_error: Exception | None = None

    for model in models:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.2,
                max_tokens=8192,
            )
            content = completion.choices[0].message.content or ""
            return _parse_ai_response(content)
        except Exception as exc:
            err = str(exc).lower()
            if "decommissioned" in err or "model_decommissioned" in err:
                continue
            last_error = exc
            continue

    raise RuntimeError(f"Groq API failed for all models: {last_error}")
