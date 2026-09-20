"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getKnowledgeIndex } from "@/lib/api";
import { useChat } from "@/lib/useChat";
import { useIngestion, startIngestion } from "@/lib/ingestion";
import { STARTER_QUESTIONS } from "@/lib/starters";
import { validateFile } from "@/lib/validation";
import { UploadDropzone } from "@/components/documents/UploadDropzone";
import type { Citation, KnowledgeIndex } from "@/lib/types";
import { ChatInputBar } from "./ChatInputBar";
import { MessageThread } from "./MessageThread";
import { CitationPanel } from "./CitationPanel";

export function ChatPanel({ indexId, initialQuestion = "" }: { indexId: string; initialQuestion?: string }) {
  const [index, setIndex] = useState<KnowledgeIndex | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const [selection, setSelection] = useState<{ citations: Citation[]; position: number } | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const job = useIngestion(indexId);
  const { messages, isSending, sendMessage, clearConversation } = useChat(indexId);
  useEffect(() => {
    let active = true;
    setError(null);
    getKnowledgeIndex(indexId).then((data) => { if (active) setIndex(data); }).catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : "Could not load index."); });
    return () => { active = false; };
  }, [indexId, job, reload]);
  useEffect(() => {
    if (!job?.pending) return;
    const guard = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [job?.pending]);
  const ready = !!index && !error && !job?.pending && index.document_count > 0;
  return <div className="relative flex h-dvh w-full overflow-hidden bg-canvas-raised">
    <div className={`flex min-w-0 flex-1 flex-col ${selection ? "hidden md:flex" : ""}`}>
      <header className="flex items-center gap-3 border-b border-line px-4 py-4 sm:px-6"><Link href="/" aria-label="Back to knowledge library" className="btn-ghost px-3">←</Link><Link href={`/indexes/${encodeURIComponent(indexId)}`} className="min-w-0 flex-1"><h1 className="truncate text-sm font-semibold">{index?.name ?? "Knowledge index"} <span className="text-ink-muted">⌄</span></h1><p className="mt-1 text-xs text-ink-muted">{index ? `${index.document_count} documents` : "Loading…"}</p></Link><button onClick={() => { clearConversation(); setSelection(null); }} disabled={isSending || !messages.length} className="btn-ghost px-3" aria-label="Start new chat">+ <span className="hidden sm:inline">New chat</span></button></header>
      {error && <div role="alert" className="p-4 text-sm text-danger">{error}<button className="btn-ghost ml-2" onClick={() => setReload((value) => value + 1)}>Retry</button></div>}
      {job?.pending && <p role="status" className="border-b border-line bg-accent-faint p-4 text-sm text-accent-soft">Indexing your documents… You can ask questions when they are ready. Keep this tab open.</p>}
      {job?.error && <p role="alert" className="p-4 text-sm text-danger">{job.error} Add your files again to retry.</p>}
      {job?.result && <div role="status" className="border-b border-line p-4 text-xs text-ink-muted">{job.result.ingested} of {job.result.total} documents indexed.{job.result.results.filter((file) => file.status === "failed").map((file, position) => <p key={position} className="mt-2 text-danger">{file.filename}: {file.error}</p>)}</div>}
      {index && !job?.pending && (index.document_count === 0 || job?.error || !!job?.result?.failed) && <div className="mx-auto max-h-[40dvh] w-full max-w-3xl overflow-y-auto p-4"><UploadDropzone onFilesAdded={(files) => { const invalid = files.map(validateFile).find(Boolean); setUploadError(invalid ?? null); if (!invalid && files.length) startIngestion(indexId, files); }} />{uploadError && <p role="alert" className="mt-2 text-sm text-danger">{uploadError}</p>}</div>}
      {messages.length ? <MessageThread messages={messages} onCitation={(citations, position) => setSelection({ citations, position })} /> : <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-6 py-8 text-center"><span className="mb-5 text-3xl text-accent-soft">✧</span><h2 className="text-xl font-semibold">Ask your knowledge</h2><p className="mb-7 mt-2 text-sm text-ink-muted">Explore your documents, with sources for every answer.</p><div className="w-full max-w-md space-y-2">{STARTER_QUESTIONS.map((question) => <button key={question} disabled={!ready || isSending} onClick={() => void sendMessage(question)} className="w-full rounded-xl border border-line p-3 text-left text-sm text-ink-soft hover:border-accent disabled:opacity-40">{question}</button>)}</div></div>}
      <ChatInputBar initialValue={initialQuestion} onSend={sendMessage} disabled={!ready || isSending} />
    </div>
    {selection && <CitationPanel {...selection} onNavigate={(position) => setSelection({ ...selection, position })} onClose={() => setSelection(null)} />}
  </div>;
}
