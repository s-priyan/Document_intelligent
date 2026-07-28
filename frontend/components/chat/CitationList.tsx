"use client";

import { useState } from "react";

import { ChevronDownIcon, FileIcon } from "@/components/ui/Icons";
import { formatCitationLabel } from "@/lib/format";
import type { Citation } from "@/lib/types";

interface CitationListProps {
  citations: Citation[];
}

/**
 * Expandable citation list for an assistant answer (FR-11, FR-17).
 *
 * Each entry surfaces the source location (source, section, start index) plus a
 * text snippet from the grounding chunk, so the user can trace an answer back to
 * its source. The list is expanded by default so sources are easy to notice, and
 * can be collapsed via the header toggle to reduce clutter.
 */
export function CitationList({ citations }: CitationListProps) {
  const [open, setOpen] = useState(true);

  if (citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 border-t border-line pt-2.5">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-accent transition-colors hover:text-accent/80"
      >
        <FileIcon className="h-3.5 w-3.5 shrink-0" />
        {citations.length} source{citations.length > 1 ? "s" : ""}
        <ChevronDownIcon
          className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open ? (
        <ul className="mt-2 flex flex-col gap-1.5 animate-fade-in-up">
          {citations.map((citation, index) => (
            <li
              key={`${citation.source}-${citation.start_index ?? index}`}
              className="flex items-start gap-2 rounded-lg border border-line bg-canvas px-2.5 py-2 text-xs text-ink-soft"
            >
              <span
                className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-accent-faint text-[10px] font-semibold text-accent"
                aria-hidden
              >
                {index + 1}
              </span>
              <div className="min-w-0">
                <p className="truncate font-medium text-ink">
                  {formatCitationLabel(citation.source, citation.section)}
                </p>
                {citation.snippet ? (
                  <p className="mt-1 italic leading-relaxed text-ink-soft">
                    &ldquo;{citation.snippet}&rdquo;
                  </p>
                ) : null}
                {citation.start_index !== null ? (
                  <p className="mt-1 text-ink-faint">Location: {citation.start_index}</p>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
