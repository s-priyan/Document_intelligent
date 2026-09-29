"use client";

/** Switches spoken answers on or off, sets playback speed, and stops playback. */
export function VoiceToggle({ enabled, available, speaking, speechRate, onChange, onStop, onCycleRate }: { enabled: boolean; available: boolean; speaking: boolean; speechRate: number; onChange: (enabled: boolean) => void; onStop: () => void; onCycleRate: () => void }) {
  return <div className="flex items-center gap-1">
    <button type="button" role="switch" aria-checked={enabled} disabled={!available} onClick={() => onChange(!enabled)} title={available ? "Read answers aloud" : "Speech is not configured on the server"} aria-label="Read answers aloud" className={`btn-ghost px-3 ${enabled ? "text-accent-soft" : ""} disabled:opacity-40`}>{enabled ? "🔊" : "🔇"} <span className="hidden sm:inline">Voice</span></button>
    {enabled && available && <button type="button" onClick={onCycleRate} title="Playback speed" aria-label={`Playback speed ${speechRate}x`} className="btn-ghost px-3 tabular-nums">{speechRate}×</button>}
    {speaking && <button type="button" onClick={onStop} className="btn-ghost px-3" aria-label="Stop reading aloud">■ <span className="hidden sm:inline">Stop</span></button>}
  </div>;
}
