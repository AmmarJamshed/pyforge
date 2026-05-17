from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class BuildTarget(str, Enum):
    DESKTOP_WINDOWS = "desktop_windows"
    DESKTOP_MAC = "desktop_mac"
    DESKTOP_LINUX = "desktop_linux"
    ANDROID_APK = "android_apk"
    IOS_IPA = "ios_ipa"


class BuildRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100_000)
    target: BuildTarget
    app_name: str = Field(default="MyApp", min_length=1, max_length=64)


class BuildStatus(str, Enum):
    QUEUED = "queued"
    AI_PROCESSING = "ai_processing"
    BUILDING = "building"
    COMPLETED = "completed"
    FAILED = "failed"


class BuildJobResponse(BaseModel):
    job_id: str
    status: BuildStatus
    message: Optional[str] = None


class AIProcessedCode(BaseModel):
    code: str
    config_files: dict[str, str]
    notes: str
    entry_point: str = "main.py"
