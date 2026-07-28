"use client";

import { useEffect, useRef, useState } from "react";

import { CheckIcon, ChevronDownIcon, SpinnerIcon } from "@/components/ui/Icons";
import type { KnowledgeIndex } from "@/lib/types";

interface KnowledgeIndexSelectorProps {
  indexes: KnowledgeIndex[];
  isLoading: boolean;
  error: string | null;
  selectedId: string | null;
  onSelect: (indexId: string) => void;
}

/** Claude-themed dropdown for picking an existing knowledge index (uses GET /knowledge-indexes). */
export function KnowledgeIndexSelector({
  indexes,
  isLoading,
  error,
  selectedId,
  onSelect,
}: KnowledgeIndexSelectorProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    function onClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  const selected = indexes.find((index) => index.id === selectedId) ?? null;
  const isEmpty = !isLoading && !error && indexes.length === 0;
  const disabled = isLoading || isEmpty || error !== null;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex w-full items-center gap-2 rounded-xl border border-line bg-canvas px-4 py-2.5 text-left text-sm text-ink transition-colors hover:border-line-strong focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <span className="flex-1 truncate">
          {isLoading
            ? "Loading indexes\u2026"
            : error
              ? "Could not load indexes"
              : isEmpty
                ? "No knowledge indexes yet"
                : (selected?.name ?? "Select a knowledge index\u2026")}
        </span>
        {isLoading ? (
          <SpinnerIcon className="h-4 w-4 text-ink-faint" />
        ) : (
          <ChevronDownIcon
            className={`h-4 w-4 text-ink-muted transition-transform ${open ? "rotate-180" : ""}`}
          />
        )}
      </button>

      {open && !disabled ? (
        <ul
          role="listbox"
          className="absolute z-10 mt-1.5 max-h-64 w-full overflow-y-auto rounded-xl border border-line bg-canvas-raised p-1 shadow-raised animate-fade-in-up"
        >
          {indexes.map((index) => {
            const isSelected = index.id === selectedId;
            return (
              <li key={index.id} role="option" aria-selected={isSelected}>
                <button
                  type="button"
                  onClick={() => {
                    onSelect(index.id);
                    setOpen(false);
                  }}
                  className={[
                    "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                    isSelected ? "bg-accent-faint text-accent" : "text-ink hover:bg-canvas-sunken",
                  ].join(" ")}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{index.name}</span>
                    <span className="block truncate text-xs text-ink-muted">
                      {index.document_count} document{index.document_count === 1 ? "" : "s"}
                    </span>
                  </span>
                  {isSelected ? <CheckIcon className="h-4 w-4 shrink-0" /> : null}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}

      {error ? <p className="mt-1.5 text-xs text-danger">{error}</p> : null}
    </div>
  );
}
