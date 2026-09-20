"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { createKnowledgeIndex } from "@/lib/api";
import { startIngestion } from "@/lib/ingestion";
import { validateFile } from "@/lib/validation";
import { UploadDropzone } from "./UploadDropzone";
import { StagedFileList } from "./StagedFileList";
import type { StagedFile } from "./types";

export function NewIndexModal({ onClose }: { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const router = useRouter();
  const [name, setName] = useState("");
  const [files, setFiles] = useState<StagedFile[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.showModal();
    dialog.current?.querySelector<HTMLInputElement>("#index-name")?.focus();
    return () => previous?.focus();
  }, []);
  async function create() {
    if (busy || !name.trim() || !files.length || files.some((file) => file.error)) return;
    setBusy(true); setError(null);
    try {
      const index = await createKnowledgeIndex(name.trim());
      startIngestion(index.id, files.map((entry) => entry.file));
      router.push(`/chat/${encodeURIComponent(index.id)}`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not create index."); setBusy(false); }
  }
  return <dialog ref={dialog} aria-labelledby="new-index-title" onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }} className="w-[calc(100%-2rem)] max-w-lg rounded-3xl border border-line-strong bg-canvas p-6 text-ink shadow-raised backdrop:bg-black/60 backdrop:backdrop-blur-sm">
    <form onSubmit={(e) => { e.preventDefault(); void create(); }}>
      <header className="mb-6 flex items-center justify-between"><h2 id="new-index-title" className="text-lg font-semibold">New knowledge index</h2><button type="button" disabled={busy} onClick={onClose} aria-label="Close new index" className="btn-ghost px-3">×</button></header>
      <label htmlFor="index-name" className="text-xs uppercase tracking-wider text-ink-muted">Name</label>
      <input autoFocus id="index-name" required maxLength={100} value={name} onChange={(e) => setName(e.target.value)} disabled={busy} placeholder="e.g. Q3 policy pack" className="field mb-4 mt-2" />
      <UploadDropzone disabled={busy} onFilesAdded={(added) => setFiles((previous) => {
        const seen = new Set(previous.map(({ file }) => `${file.name}:${file.size}:${file.lastModified}`));
        return [...previous, ...added.filter((file) => { const key = `${file.name}:${file.size}:${file.lastModified}`; if (seen.has(key)) return false; seen.add(key); return true; }).map((file) => ({ id: crypto.randomUUID(), file, error: validateFile(file) }))];
      })} />
      <div className="mt-4 max-h-48 overflow-y-auto"><StagedFileList files={files} disabled={busy} onRemove={(id) => setFiles((previous) => previous.filter((file) => file.id !== id))} /></div>
      {error && <p role="alert" className="mt-3 text-sm text-danger">{error}</p>}
      <footer className="mt-5 flex justify-end gap-2"><button type="button" onClick={onClose} disabled={busy} className="btn-ghost">Cancel</button><button disabled={busy || !name.trim() || !files.length || files.some((file) => file.error)} className="btn-primary">{busy ? "Creating…" : "Create and chat"}</button></footer>
    </form>
  </dialog>;
}
