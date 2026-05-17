# PyForge AI providers

Groq free tier often hits **token-per-minute (TPM)** limits on small models. PyForge supports several backends — pick one via `AI_PROVIDER` on the server.

## Comparison

| Provider | Cost | Best for | Env vars |
|----------|------|----------|----------|
| **Google Gemini** | Free tier | Render / cloud deploy | `AI_PROVIDER=gemini`, `GEMINI_API_KEY` |
| **OpenRouter** | Free + paid models | Cloud, model choice | `AI_PROVIDER=openrouter`, `OPENAI_API_KEY` |
| **OpenAI** | Paid | Production quality | `AI_PROVIDER=openai`, `OPENAI_API_KEY` |
| **Ollama** | Free (local) | VPS / your PC | `AI_PROVIDER=ollama`, `OPENAI_BASE_URL` |
| **Groq** | Free (limited TPM) | Fast tests, small scripts | `AI_PROVIDER=groq`, `GROQ_API_KEY` |

## 1. Google Gemini (recommended for Render)

1. Get a key: [Google AI Studio](https://aistudio.google.com/apikey)
2. On Render → **pyforge-api** → **Environment**:
   ```
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_key_here
   ```
3. Redeploy.

## 2. OpenRouter

1. Sign up: [openrouter.ai](https://openrouter.ai)
2. Create an API key.
3. Environment:
   ```
   AI_PROVIDER=openrouter
   OPENAI_API_KEY=sk-or-v1-...
   OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
   ```

## 3. OpenAI

```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## 4. Ollama (self-hosted, unlimited)

Run on the same machine or LAN as PyForge:

```bash
ollama pull llama3.1
ollama serve
```

Environment:

```
AI_PROVIDER=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1
OPENAI_API_KEY=ollama
```

On Docker Compose, use `http://host.docker.internal:11434/v1` (Windows/Mac).

## 5. Groq (default)

Works for **short** scripts. PyForge trims prompts and skips low-TPM models.

```
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

If you see `413` or `rate_limit_exceeded`, switch to **Gemini** or **OpenRouter**.
