import Editor from '@monaco-editor/react';

export default function CodeEditor({ value, onChange, readOnly = false }) {
  return (
    <div className="monaco-wrapper h-full min-h-[320px] rounded-lg overflow-hidden border border-slate-700/80">
      <Editor
        height="100%"
        defaultLanguage="python"
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? '')}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: "'JetBrains Mono', monospace",
          padding: { top: 12 },
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />
    </div>
  );
}
