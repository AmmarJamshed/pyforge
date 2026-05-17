import { useCallback, useEffect, useState } from 'react';
import {
  createBuildWebSocket,
  fetchSampleCode,
  getDownloadUrl,
  startBuild,
} from './api';
import BuildTerminal from './components/BuildTerminal';
import CodeEditor from './components/CodeEditor';
import TargetSelector from './components/TargetSelector';
import { DEFAULT_SAMPLE, SAMPLES } from './samples';

export default function App() {
  const [code, setCode] = useState(DEFAULT_SAMPLE.code);
  const [target, setTarget] = useState('desktop_windows');
  const [appName, setAppName] = useState(DEFAULT_SAMPLE.appName);
  const [building, setBuilding] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [message, setMessage] = useState('');
  const [logs, setLogs] = useState([]);
  const [downloadReady, setDownloadReady] = useState(false);
  const [artifactName, setArtifactName] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSampleCode()
      .then((data) => {
        if (data?.code) setCode(data.code);
        if (data?.app_name) setAppName(data.app_name);
      })
      .catch(() => {});
  }, []);

  const loadSample = (sampleId) => {
    const sample = SAMPLES[sampleId];
    if (!sample) return;
    setCode(sample.code);
    setAppName(sample.appName);
  };

  const handleBuild = useCallback(async () => {
    setError(null);
    setBuilding(true);
    setLogs([]);
    setJobId(null);
    setStatus('queued');
    setDownloadReady(false);
    setArtifactName(null);

    try {
      const result = await startBuild({ code, target, appName });
      setJobId(result.job_id);
      setStatus(result.status);
      setMessage(result.message || '');

      const ws = createBuildWebSocket(result.job_id);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'log') {
          setLogs((prev) => [...prev, data.line]);
        }
        if (data.type === 'status') {
          setStatus(data.status);
          if (data.message) setMessage(data.message);
          if (data.history) setLogs(data.history);
          if (data.download_ready) setDownloadReady(true);
          if (data.artifact_name) setArtifactName(data.artifact_name);
        }
        if (data.type === 'error') {
          setError(data.message);
        }
      };

      ws.onclose = () => setBuilding(false);
      ws.onerror = () => {
        setError('WebSocket connection failed');
        setBuilding(false);
      };
    } catch (err) {
      setError(err.message);
      setBuilding(false);
      setStatus('failed');
    }
  }, [code, target, appName]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-forge-400 to-forge-700 flex items-center justify-center text-lg font-bold shadow-lg shadow-forge-900/50">
              Py
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white font-sans">
                PyForge
              </h1>
              <p className="text-xs text-slate-500">Python → Native Apps with AI</p>
            </div>
          </div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-slate-400 hover:text-forge-400 transition-colors"
          >
            Open Source
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <section className="mb-8 text-center max-w-2xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-3 font-sans">
            Paste Python. Ship native apps.
          </h2>
          <p className="text-slate-400 text-sm sm:text-base">
            AI analyzes your code, fixes platform issues, and generates build configs (Gemini,
            OpenAI, OpenRouter, Ollama, or Groq). API keys stay on the server.
          </p>
        </section>

        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-sm text-slate-400">
                Sample
                <select
                  className="ml-2 px-3 py-1.5 rounded-md bg-slate-800 border border-slate-600 text-sm text-white"
                  defaultValue="quickcalc"
                  onChange={(e) => loadSample(e.target.value)}
                  disabled={building}
                >
                  {Object.values(SAMPLES).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-slate-400">
                App name
                <input
                  type="text"
                  value={appName}
                  onChange={(e) => setAppName(e.target.value.replace(/[^\w\-]/g, ''))}
                  className="ml-2 px-3 py-1.5 rounded-md bg-slate-800 border border-slate-600 text-sm text-white w-36"
                  maxLength={64}
                />
              </label>
            </div>

            <div className="h-[420px]">
              <CodeEditor value={code} onChange={setCode} readOnly={building} />
            </div>

            <button
              type="button"
              onClick={handleBuild}
              disabled={building || !code.trim()}
              className="w-full sm:w-auto px-8 py-3 rounded-xl bg-gradient-to-r from-forge-500 to-forge-600 hover:from-forge-400 hover:to-forge-500 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-white shadow-lg shadow-forge-900/40 transition-all"
            >
              {building ? 'Building…' : '⚡ Build with AI'}
            </button>

            {error && (
              <p className="text-red-400 text-sm rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2">
                {error}
              </p>
            )}

            {message && !error && (
              <p className="text-slate-400 text-sm">{message}</p>
            )}

            {downloadReady && jobId && (
              <a
                href={getDownloadUrl(jobId)}
                download={artifactName || true}
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-colors"
              >
                ↓ Download {artifactName || 'artifact'}
              </a>
            )}
          </div>

          <aside className="space-y-6">
            <div className="rounded-xl border border-slate-700/80 bg-slate-900/50 p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-3">Build target</h3>
              <TargetSelector value={target} onChange={setTarget} />
            </div>

            <div className="h-[280px]">
              <BuildTerminal lines={logs} status={status} />
            </div>
          </aside>
        </div>
      </main>

      <footer className="border-t border-slate-800 mt-12 py-6 text-center text-xs text-slate-500">
        PyForge — MIT Licensed · Self-hostable · Builds run in isolated Docker containers
      </footer>
    </div>
  );
}
