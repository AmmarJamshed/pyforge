const API_BASE = import.meta.env.VITE_API_URL ?? '';

function toWebSocketBase(url) {
  if (!url) return url;
  return url.replace(/^https:\/\//i, 'wss://').replace(/^http:\/\//i, 'ws://').replace(/\/$/, '');
}

function wsUrl(jobId) {
  const configured = import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_URL;
  if (configured) {
    const base = toWebSocketBase(configured.replace(/\/$/, ''));
    return `${base}/ws/build/${jobId}`;
  }
  if (import.meta.env.DEV) {
    return `ws://${window.location.hostname}:8000/ws/build/${jobId}`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/build/${jobId}`;
}

export async function fetchSampleCode() {
  const res = await fetch(`${API_BASE}/api/sample-code`);
  if (!res.ok) throw new Error('Failed to load sample code');
  return res.json();
}

export async function startBuild({ code, target, appName }) {
  const res = await fetch(`${API_BASE}/api/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, target, app_name: appName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = typeof err.detail === 'string' ? err.detail : 'Build request failed';
    throw new Error(detail);
  }
  return res.json();
}

export async function getBuildStatus(jobId) {
  const res = await fetch(`${API_BASE}/api/build/${jobId}`);
  if (!res.ok) throw new Error('Failed to fetch build status');
  return res.json();
}

export function getDownloadUrl(jobId) {
  return `${API_BASE}/api/build/${jobId}/download`;
}

export function createBuildWebSocket(jobId) {
  return new WebSocket(wsUrl(jobId));
}
