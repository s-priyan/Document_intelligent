"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { getKnowledgeIndex } from "@/lib/api";
import { useIngestion } from "@/lib/ingestion";
import { STARTER_QUESTIONS } from "@/lib/starters";
import type { KnowledgeIndex } from "@/lib/types";
import { formatFileSize } from "@/lib/format";

export function IndexDetail({ indexId }: { indexId: string }) {
  const [index, setIndex] = useState<KnowledgeIndex | null>(null);
  const [error, setError] = useState<string | null>(null);
  const job = useIngestion(indexId);
  useEffect(() => {
    let active = true;
    getKnowledgeIndex(indexId).then((data) => { if (active) setIndex(data); }).catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : "Could not load index."); });
    return () => { active = false; };
  }, [indexId, job]);
  const chatUrl = `/chat/${encodeURIComponent(indexId)}`;
  return <section className="surface mx-auto min-h-[70dvh] max-w-5xl">
    <header className="flex flex-wrap items-center gap-4 border-b border-line p-6 sm:p-8"><Link href="/" aria-label="Back to knowledge library" className="btn-ghost px-3">←</Link><div className="min-w-0 flex-1"><h1 className="break-words text-xl font-semibold">{index?.name ?? "Knowledge index"}</h1>{index && <p className="mt-2 text-xs text-ink-muted">{index.document_count} document{index.document_count === 1 ? "" : "s"} · Created {new Date(index.created_at).toLocaleDateString()}</p>}</div>{index && <Link href={chatUrl} className="btn-primary">Start chat</Link>}</header>
    {error ? <p role="alert" className="p-8 text-danger">{error}</p> : !index ? <p role="status" className="p-8 text-ink-muted">Loading index…</p> : <div className="grid gap-8 p-6 sm:p-8 md:grid-cols-[1.3fr_1fr]">
      <section><h2 className="mb-4 text-xs uppercase tracking-widest text-ink-muted">Documents</h2>
        {job?.result?.results.some((file) => file.status === "ingested") ? <ul className="space-y-3">{job.result.results.filter((file) => file.status === "ingested").map((file, position) => <li key={position} className="rounded-xl border border-line bg-canvas p-4"><p className="break-words text-sm font-medium">{file.filename}</p><p className="mt-2 text-xs text-ink-muted">{file.size_bytes !== null && `${formatFileSize(file.size_bytes)} · `}{file.chunk_count} chunks</p></li>)}</ul> : <div className="rounded-xl border border-line bg-canvas p-5"><p className="font-medium">{index.document_count} indexed document{index.document_count === 1 ? "" : "s"}</p><p className="mt-2 text-sm leading-relaxed text-ink-muted">{index.document_count ? "Start a chat to explore this collection. Sources appear alongside each answer." : "This index has no indexed documents yet."}</p></div>}
      </section>
      <section><h2 className="mb-4 text-xs uppercase tracking-widest text-ink-muted">Try asking</h2><div className="space-y-3">{STARTER_QUESTIONS.map((question) => <Link key={question} href={`${chatUrl}?question=${encodeURIComponent(question)}`} className="block rounded-xl border border-line p-4 text-sm transition hover:border-accent hover:bg-accent-faint">{question} <span className="text-accent-soft">↗</span></Link>)}</div></section>
    </div>}
  </section>;
}
