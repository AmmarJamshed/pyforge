import json
import re

import httpx
from groq import Groq

from app.config import settings
from app.models import AIProcessedCode, BuildTarget
from app.services.ai_prompts import SYSTEM_PROMPT, build_user_message


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


def _truncate_code(code: str) -> str:
    limit = settings.ai_max_input_chars
    if len(code) <= limit:
        return code
    return code[:limit] + "\n# ... truncated for AI context limit ...\n"


async def _chat_openai_compatible(
    messages: list[dict[str, str]],
    *,
    api_key: str,
    base_url: str,
    models: list[str],
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=120.0) as client:
        for model in models:
            if not model:
                continue
            body = {
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 4096,
            }
            try:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
            except Exception as exc:
                last_error = exc
                continue
    raise RuntimeError(f"OpenAI-compatible API failed: {last_error}")


async def _chat_groq(messages: list[dict[str, str]], models: list[str]) -> str:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    client = Groq(api_key=settings.groq_api_key)
    deprecated = {"llama3-70b-8192", "llama3-8b-8192", "llama-3.1-8b-instant"}
    last_error: Exception | None = None
    for model in [m for m in models if m and m not in deprecated]:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=4096,
            )
            return completion.choices[0].message.content or ""
        except Exception as exc:
            err = str(exc).lower()
            if "decommissioned" in err or "model_decommissioned" in err:
                continue
            last_error = exc
            continue
    raise RuntimeError(f"Groq API failed: {last_error}")


async def _chat_gemini(messages: list[dict[str, str]], model: str) -> str:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")
    combined = "\n\n".join(f"{m['role']}: {m['content']}" for m in messages)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={settings.gemini_api_key}"
    )
    body = {
        "contents": [{"parts": [{"text": combined}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _provider_models() -> tuple[str, list[str], str | None, str | None]:
    """Returns (provider_label, model_list, openai_key, openai_base_url)."""
    p = settings.ai_provider.lower().strip()

    if p == "groq":
        return (
            "Groq",
            [
                settings.groq_model,
                settings.groq_fallback_model,
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
            ],
            None,
            None,
        )
    if p == "openai":
        return ("OpenAI", [settings.openai_model], settings.openai_api_key, "https://api.openai.com/v1")
    if p == "openrouter":
        return (
            "OpenRouter",
            [settings.openai_model, "meta-llama/llama-3.1-8b-instruct:free"],
            settings.openai_api_key,
            "https://openrouter.ai/api/v1",
        )
    if p == "ollama":
        return (
            "Ollama",
            [settings.openai_model, "llama3.1", "codellama"],
            settings.openai_api_key or "ollama",
            settings.openai_base_url or "http://host.docker.internal:11434/v1",
        )
    if p == "gemini":
        return ("Gemini", [settings.gemini_model], None, None)

    raise ValueError(
        f"Unknown AI_PROVIDER '{settings.ai_provider}'. "
        "Use: groq, openai, openrouter, ollama, gemini"
    )


def ai_configured() -> bool:
    p = settings.ai_provider.lower().strip()
    if p == "groq":
        return bool(settings.groq_api_key)
    if p == "gemini":
        return bool(settings.gemini_api_key)
    return bool(settings.openai_api_key)


async def process_code_with_ai(code: str, target: BuildTarget, app_name: str) -> AIProcessedCode:
    if not ai_configured():
        raise ValueError(
            f"AI not configured for provider '{settings.ai_provider}'. "
            "Set the API key in server environment variables."
        )

    code = _truncate_code(code)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(code, target, app_name)},
    ]

    label, models, oa_key, oa_base = _provider_models()
    models = list(dict.fromkeys(m for m in models if m))

    if settings.ai_provider.lower() == "groq":
        content = await _chat_groq(messages, models)
    elif settings.ai_provider.lower() == "gemini":
        content = await _chat_gemini(messages, models[0])
    else:
        content = await _chat_openai_compatible(
            messages,
            api_key=oa_key or "",
            base_url=oa_base or settings.openai_base_url,
            models=models,
        )

    return _parse_ai_response(content)


def provider_display_name() -> str:
    label, _, _, _ = _provider_models()
    return label
