"use client";
import Link from "next/link";
import { useState } from "react";
import { useKnowledgeIndexes } from "@/lib/useKnowledgeIndexes";
import { NewIndexModal } from "./NewIndexModal";

export function DocumentManager() {
  const { indexes, isLoading, error, reload } = useKnowledgeIndexes();
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const filtered = indexes.filter((index) => index.name.toLowerCase().includes(search.toLowerCase()));
  return <section className="surface mx-auto min-h-[70dvh] w-full max-w-5xl p-6 sm:p-9">
    <header className="mb-7 flex items-center justify-between gap-4"><div><p className="mb-2 text-xs uppercase tracking-widest text-ink-muted">Chat with your docs</p><h1 className="text-2xl font-semibold">Your knowledge</h1></div><button className="btn-primary shrink-0" onClick={() => setCreating(true)}>+ New index</button></header>
    <input aria-label="Search indexes" type="search" placeholder="Search knowledge indexes" value={search} onChange={(e) => setSearch(e.target.value)} className="field mb-6" />
    {isLoading ? <p role="status" className="text-sm text-ink-muted">Loading your knowledge…</p> : error ? <div role="alert" className="text-sm text-danger">{error}<button onClick={() => void reload()} className="btn-ghost ml-3">Retry</button></div> : filtered.length ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {filtered.map((index) => <Link key={index.id} href={`/indexes/${encodeURIComponent(index.id)}`} className="group flex min-h-36 flex-col justify-between gap-6 rounded-2xl border border-line bg-canvas p-5 transition hover:border-accent hover:bg-accent-faint"><h2 className="break-words font-semibold">{index.name}</h2><p className="text-xs leading-6 text-ink-muted">{index.document_count} {index.document_count === 1 ? "document" : "documents"}<br />Created {new Date(index.created_at).toLocaleDateString()}</p></Link>)}
    </div> : <div className="py-20 text-center"><h2 className="font-medium">{search ? "No matching indexes" : "Your knowledge starts here"}</h2><p className="mt-2 text-sm text-ink-muted">{search ? "Try another index name." : "Create an index and add documents to start asking questions."}</p></div>}
    {creating && <NewIndexModal onClose={() => setCreating(false)} />}
  </section>;
}
