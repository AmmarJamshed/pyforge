import { useEffect, useRef } from 'react';

export default function BuildTerminal({ lines, status }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  const statusColor = {
    queued: 'text-slate-400',
    ai_processing: 'text-amber-400',
    building: 'text-forge-400',
    completed: 'text-emerald-400',
    failed: 'text-red-400',
  }[status] || 'text-slate-400';

  return (
    <div className="flex flex-col h-full min-h-[200px] rounded-lg border border-slate-700/80 bg-slate-900/90 overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-700/60 bg-slate-800/80">
        <span className="w-3 h-3 rounded-full bg-red-500/80" />
        <span className="w-3 h-3 rounded-full bg-amber-500/80" />
        <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
        <span className="ml-2 text-xs font-medium text-slate-400 font-display">
          build output
        </span>
        {status && (
          <span className={`ml-auto text-xs font-mono uppercase ${statusColor}`}>
            {status.replace('_', ' ')}
          </span>
        )}
      </div>
      <pre className="flex-1 overflow-auto p-3 text-xs font-display text-slate-300 leading-relaxed">
        {lines.length === 0 ? (
          <span className="text-slate-500">Waiting for build logs...</span>
        ) : (
          lines.map((line, i) => (
            <div key={i} className="whitespace-pre-wrap break-all">
              {line}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </pre>
    </div>
  );
}
