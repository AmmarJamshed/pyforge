# PyForge

**PyForge** is an open-source, self-hostable web application that turns Python scripts into downloadable native apps — Windows EXE, macOS app, Linux binary, Android APK, or iOS IPA — using **Groq AI** for code analysis and **Docker-isolated** build workers.

[![MIT License](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)

## Features

- **Monaco code editor** — paste Python, pick a target, click **Build with AI**
- **Groq-powered pipeline** — fixes platform issues, adds imports/entry points, generates `buildozer.spec`, PyInstaller specs, etc.
- **Live build logs** — WebSocket streaming to the UI
- **Sandboxed builds** — each job runs in an ephemeral Docker container (never on the host Python directly)
- **Temporary artifacts** — downloads expire after 1 hour (configurable)
- **Server-side API key** — `GROQ_API_KEY` is never sent to the browser

## Architecture

```
┌─────────────┐     HTTP/WS      ┌──────────────────┐     Groq API
│   React     │ ◄──────────────► │  FastAPI Backend │
│  Frontend   │                  │  (orchestrator)  │
└─────────────┘                  └────────┬─────────┘
                                          │ docker run (per job)
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │   Desktop    │    │   Android    │    │  iOS (macOS  │
            │  PyInstaller │    │  Buildozer   │    │   host only) │
            └──────────────┘    └──────────────┘    └──────────────┘
```

1. User submits code + target platform.
2. Backend calls Groq (`llama-3.3-70b-versatile` with fallback to `mixtral-8x7b-32768`).
3. AI returns build-ready code + config files.
4. Backend packs sources, mounts into a **builder image**, streams stdout to WebSocket.
5. Artifact is served from `/api/build/{id}/download` until TTL cleanup.

## Requirements

- Docker & Docker Compose
- Groq API key ([console.groq.com](https://console.groq.com))
- **iOS IPA**: macOS host with Xcode + [kivy-ios](https://github.com/kivy/kivy-ios) (documented limitation)

## Quick start (Docker Compose)

```bash
git clone <your-repo-url> pyforge
cd pyforge

# Configure secrets (see .env.example)
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...

# Build builder images + stack
docker compose build
docker compose up -d

# Open UI
# http://localhost:3000
# API: http://localhost:8000/docs
```

### Default `.env`

A sample `GROQ_API_KEY` may be present in `.env` for local testing. **Replace it before any public deployment** and never commit `.env` (it is gitignored).

## Local development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export GROQ_API_KEY=your_key
export ARTIFACTS_DIR=./artifacts
mkdir -p artifacts

# Build worker images first
docker build -t pyforge-builder-desktop:latest build-containers/desktop
docker build -t pyforge-builder-android:latest build-containers/android

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173 (proxies /api and /ws to :8000)
```

## Build targets

| Target | Worker image | Output |
|--------|--------------|--------|
| `desktop_windows` | `pyforge-builder-desktop` | `.exe` (via PyInstaller on Linux) |
| `desktop_mac` | `pyforge-builder-desktop` | macOS binary* |
| `desktop_linux` | `pyforge-builder-desktop` | Linux executable |
| `android_apk` | `pyforge-builder-android` | `.apk` (Buildozer; first run is slow) |
| `ios_ipa` | macOS host | `.ipa` — **requires Darwin backend** |

\*Cross-compiling macOS apps from Linux containers is limited; for production macOS builds, run the backend on macOS.

## Security

- User code executes **only inside** short-lived builder containers.
- Backend mounts Docker socket to spawn builders — lock down host access in production.
- Artifacts auto-delete after `ARTIFACT_TTL_SECONDS` (default 3600).
- Rate limiting and auth are not included; add a reverse proxy (nginx, Caddy) for public instances.

## Environment variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key (server only) |
| `GROQ_MODEL` | Primary model |
| `GROQ_FALLBACK_MODEL` | Fallback if primary unavailable |
| `ARTIFACTS_DIR` | Host path for build outputs |
| `ARTIFACT_TTL_SECONDS` | Seconds before job/artifact cleanup |
| `BUILD_TIMEOUT_SECONDS` | Max build duration |
| `CORS_ORIGINS` | Comma-separated frontend origins |

## Project structure

```
pyforge/
├── docker-compose.yml
├── .env.example
├── README.md
├── LICENSE
├── .github/workflows/ci.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── services/groq_service.py
│   │   ├── services/job_manager.py
│   │   └── build/
│   └── build-containers/
│       ├── desktop/
│       └── android/
└── frontend/
    ├── Dockerfile
    ├── src/
    └── public/
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/build` | Start build `{ code, target, app_name }` |
| `GET` | `/api/build/{id}` | Job status |
| `GET` | `/api/build/{id}/download` | Download artifact |
| `WS` | `/ws/build/{id}` | Live logs + status |

## License

MIT — see [LICENSE](LICENSE).

## Contributing

PRs welcome. Run CI locally:

```bash
cd backend && pip install -r requirements.txt && python -m compileall app
cd frontend && npm install && npm run build
docker compose build
```
