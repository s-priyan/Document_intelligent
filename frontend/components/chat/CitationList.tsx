"use client";
import type { Citation } from "@/lib/types";
export function CitationList({ citations, onSelect }: { citations: Citation[]; onSelect: (citations: Citation[], position: number) => void }) {
  if (!citations.length) return null;
  return <div className="mt-4 border-t border-line pt-3"><button onClick={() => onSelect(citations, 0)} className="text-xs font-medium text-accent-soft">▧ {citations.length} source excerpt{citations.length === 1 ? "" : "s"}</button><div className="mt-2 flex flex-wrap gap-2">{citations.map((citation, position) => <button key={position} onClick={() => onSelect(citations, position)} className="max-w-full truncate rounded-lg border border-line bg-canvas px-2 py-1 text-xs text-ink-soft hover:border-accent" aria-label={`View source ${position + 1}: ${citation.source}`}><span className="mr-2 text-accent-soft">{position + 1}</span>{citation.section || citation.source}</button>)}</div></div>;
}
