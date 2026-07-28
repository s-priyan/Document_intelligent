"use client";

import { AlertIcon, FileIcon, TrashIcon } from "@/components/ui/Icons";
import { formatFileSize } from "@/lib/format";
import type { StagedFile } from "./types";

interface StagedFileListProps {
  files: StagedFile[];
  onRemove: (id: string) => void;
  disabled?: boolean;
}

/** Presentational list of staged documents with per-file removal (client-side). */
export function StagedFileList({ files, onRemove, disabled }: StagedFileListProps) {
  if (files.length === 0) {
    return null;
  }

  return (
    <ul className="flex flex-col gap-2" aria-label="Staged documents">
      {files.map(({ id, file, error }) => (
        <li
          key={id}
          className={[
            "flex items-center gap-3 rounded-xl border px-3 py-2.5",
            error ? "border-danger/40 bg-danger/5" : "border-line bg-canvas-raised",
          ].join(" ")}
        >
          <span
            className={[
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
              error ? "bg-danger/10 text-danger" : "bg-canvas-sunken text-ink-muted",
            ].join(" ")}
          >
            {error ? <AlertIcon className="h-5 w-5" /> : <FileIcon className="h-5 w-5" />}
          </span>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-ink">{file.name}</p>
            <p className={`text-xs ${error ? "text-danger" : "text-ink-muted"}`}>
              {error ?? formatFileSize(file.size)}
            </p>
          </div>

          <button
            type="button"
            onClick={() => onRemove(id)}
            disabled={disabled}
            aria-label={`Remove ${file.name}`}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-ink-muted transition-colors hover:bg-canvas-sunken hover:text-danger disabled:cursor-not-allowed disabled:opacity-50"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}
