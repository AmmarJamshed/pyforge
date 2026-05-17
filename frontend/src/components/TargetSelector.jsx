const TARGETS = [
  { id: 'desktop_windows', label: 'Windows EXE', icon: '🪟', group: 'Desktop' },
  { id: 'desktop_mac', label: 'macOS App', icon: '🍎', group: 'Desktop' },
  { id: 'desktop_linux', label: 'Linux Binary', icon: '🐧', group: 'Desktop' },
  { id: 'android_apk', label: 'Android APK', icon: '🤖', group: 'Mobile' },
  { id: 'ios_ipa', label: 'iOS IPA', icon: '📱', group: 'Mobile', warning: true },
];

export default function TargetSelector({ value, onChange }) {
  const groups = [...new Set(TARGETS.map((t) => t.group))];

  return (
    <div className="space-y-4">
      {groups.map((group) => (
        <div key={group}>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
            {group}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {TARGETS.filter((t) => t.group === group).map((target) => (
              <button
                key={target.id}
                type="button"
                onClick={() => onChange(target.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg border text-left transition-all ${
                  value === target.id
                    ? 'border-forge-500 bg-forge-500/10 ring-1 ring-forge-500/50'
                    : 'border-slate-700/80 bg-slate-800/40 hover:border-slate-600'
                }`}
              >
                <span className="text-xl">{target.icon}</span>
                <span>
                  <span className="block text-sm font-medium text-slate-100">
                    {target.label}
                  </span>
                  {target.warning && (
                    <span className="block text-[10px] text-amber-400/90 mt-0.5">
                      Requires macOS host
                    </span>
                  )}
                </span>
              </button>
            ))}
          </div>
        </div>
      ))}

      {value === 'ios_ipa' && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200/90">
          <strong>iOS limitation:</strong> IPA builds require a macOS machine with Xcode and the
          kivy-ios toolchain. PyForge will prepare configs via AI, but the build must run on macOS.
        </div>
      )}
    </div>
  );
}
