"use client";
import { useEffect, useRef } from "react";
import type { Citation } from "@/lib/types";
export function CitationPanel({ citations, position, onNavigate, onClose }: { citations: Citation[]; position: number; onNavigate: (position: number) => void; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    return () => previous?.focus();
  }, []);
  const citation = citations[position];
  return <aside aria-label="Source excerpt" onKeyDown={(event) => { if (event.key === "Escape") onClose(); }} className="absolute inset-0 z-20 flex flex-col border-l border-line bg-canvas md:static md:w-[26rem] md:shrink-0 xl:w-[34rem]">
    <header className="flex items-center gap-1 border-b border-line px-4 py-3"><h2 className="flex-1 text-sm font-semibold" aria-live="polite">Source {position + 1} of {citations.length}</h2><button className="btn-ghost px-3" aria-label="Previous source" disabled={position === 0} onClick={() => onNavigate(position - 1)}>‹</button><button className="btn-ghost px-3" aria-label="Next source" disabled={position === citations.length - 1} onClick={() => onNavigate(position + 1)}>›</button><button ref={closeRef} className="btn-ghost px-3" aria-label="Close source panel" onClick={onClose}>×</button></header>
    <div className="overflow-y-auto p-5"><h3 className="break-words text-sm font-semibold">{citation.section || citation.source}</h3>{citation.section && <p className="mt-3 break-words text-xs text-ink-muted">{citation.source}</p>}{citation.start_index !== null && <p className="mt-3 text-xs text-ink-muted">Character location {citation.start_index}</p>}<p className="mb-3 mt-8 text-xs uppercase tracking-widest text-ink-muted">Source excerpt</p><blockquote className="whitespace-pre-wrap break-words rounded-r-xl border-l-2 border-danger bg-danger/5 p-4 text-sm leading-7 text-ink-soft">{citation.snippet || "No excerpt is available for this source."}</blockquote></div>
  </aside>;
}
