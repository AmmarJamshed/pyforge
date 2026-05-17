from app.models import BuildTarget

# Compact prompt to stay under free-tier TPM limits (Groq, etc.)
SYSTEM_PROMPT = """You are PyForge. Return ONLY valid JSON (no markdown):
{"code":"...","entry_point":"main.py","config_files":{},"notes":"..."}
Fix platform issues, add entry point if missing. Desktop: include .spec in config_files.
Android: buildozer.spec. iOS: note macOS required. No secrets in output."""

TARGET_HINTS = {
    BuildTarget.DESKTOP_WINDOWS: "Windows EXE, PyInstaller onefile.",
    BuildTarget.DESKTOP_MAC: "macOS app, PyInstaller.",
    BuildTarget.DESKTOP_LINUX: "Linux binary, PyInstaller.",
    BuildTarget.ANDROID_APK: "Android APK, buildozer.spec.",
    BuildTarget.IOS_IPA: "iOS IPA, kivy-ios, macOS host.",
}


def build_user_message(code: str, target: BuildTarget, app_name: str) -> str:
    return (
        f"app={app_name} target={target.value} hint={TARGET_HINTS[target]}\n"
        f"```python\n{code}\n```"
    )
