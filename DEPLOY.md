# Deploy PyForge Online

## Option A — Render (recommended, free tier)

Full UI + Groq AI works on the free tier. Native APK/EXE builds need a VPS (Docker); cloud mode ships an **AI-prepared ZIP** instead.

### Steps

1. **Push to GitHub**
   ```bash
   cd pyforge
   git init -b main
   git add .
   git commit -m "PyForge initial release"
   ```
   Create a repo at [github.com/new](https://github.com/new) named `pyforge`, then:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/pyforge.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - **New → Blueprint**
   - Connect your GitHub repo and select `render.yaml`
   - When prompted, set **`GROQ_API_KEY`** (your Groq key from [console.groq.com](https://console.groq.com))
   - Click **Apply**

3. **URLs** (after ~5–10 min build)
   - Frontend: `https://pyforge-web.onrender.com` (name may vary)
   - API: `https://pyforge-api.onrender.com`
   - Docs: `https://pyforge-api.onrender.com/docs`

4. **CORS** (if the UI cannot reach the API)
   In Render → `pyforge-api` → Environment → add:
   ```
   CORS_ORIGINS=https://pyforge-web.onrender.com
   ```
   Use your actual frontend URL.

---

## Option B — VPS (full Docker builds: APK / EXE)

Use any Ubuntu 22.04+ server (DigitalOcean, Hetzner, Oracle Free Tier).

```bash
ssh user@your-server
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
git clone https://github.com/YOUR_USERNAME/pyforge.git
cd pyforge
cp .env.example .env
nano .env   # set GROQ_API_KEY
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Point a domain at the server and set `DOMAIN=pyforge.example.com` in `.env` for HTTPS (Caddy).

---

## Option C — Local tunnel (instant demo, temporary URL)

```powershell
# Terminal 1
cd pyforge\backend
pip install -r requirements.txt
$env:GROQ_API_KEY="your-key"
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2
cd pyforge\frontend
npm run dev

# Terminal 3
npx localtunnel --port 5173
```

Share the `*.loca.lt` URL (temporary; not for production).

---

## Environment variables (production)

| Variable | Render | VPS |
|----------|--------|-----|
| `GROQ_API_KEY` | Required | Required |
| `DOCKER_BUILDS_ENABLED` | `false` (default) | `true` |
| `CORS_ORIGINS` | Frontend URL | Your domain(s) |

**Rotate your Groq API key** if it was ever shared publicly.
