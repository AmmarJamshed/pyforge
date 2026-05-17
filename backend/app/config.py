from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # AI provider: groq | openai | openrouter | ollama | gemini
    ai_provider: str = "groq"
    ai_max_input_chars: int = 8000

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-70b-versatile"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    artifacts_dir: str = "/app/artifacts"
    artifact_ttl_seconds: int = 3600

    docker_network: str = "pyforge_default"
    desktop_image: str = "pyforge-builder-desktop:latest"
    android_image: str = "pyforge-builder-android:latest"

    max_code_length: int = 100_000
    build_timeout_seconds: int = 1800

    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:80"

    # False on Render/Railway etc. (no Docker socket). Ships AI-prepared source ZIP instead.
    docker_builds_enabled: bool = True


settings = Settings()
