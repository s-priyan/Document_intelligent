"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ArrowLeftIcon, TrashIcon } from "@/components/ui/Icons";
import { getKnowledgeIndex } from "@/lib/api";
import { useChat } from "@/lib/useChat";
import type { KnowledgeIndex } from "@/lib/types";
import { ChatInputBar } from "./ChatInputBar";
import { MessageThread } from "./MessageThread";

interface ChatPanelProps {
  indexId: string;
}

type LoadState = "loading" | "ready" | "missing";

/** Screen 2: conversational UI over a knowledge index (FR-14/FR-15/FR-18). */
export function ChatPanel({ indexId }: ChatPanelProps) {
  const [index, setIndex] = useState<KnowledgeIndex | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const { messages, isSending, sendMessage, clearConversation } = useChat(indexId);

  useEffect(() => {
    let active = true;
    getKnowledgeIndex(indexId)
      .then((data) => {
        if (active) {
          setIndex(data);
          setLoadState("ready");
        }
      })
      .catch(() => {
        if (active) {
          setLoadState("missing");
        }
      });
    return () => {
      active = false;
    };
  }, [indexId]);

  if (loadState === "missing") {
    return <MissingIndex indexId={indexId} />;
  }

  return (
    <div className="mx-auto flex h-dvh w-full max-w-3xl flex-col">
      <header className="flex items-center gap-3 border-b border-line bg-canvas-raised px-4 py-3 sm:px-6">
        <Link
          href="/"
          aria-label="Back to documents"
          className="flex h-9 w-9 items-center justify-center rounded-full text-ink-muted transition-colors hover:bg-canvas-sunken hover:text-ink"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-sm font-semibold text-ink">
            {index?.name ?? indexId}
          </h1>
          <p className="text-xs text-ink-muted">
            {loadState === "loading"
              ? "Loading\u2026"
              : `${index?.document_count ?? 0} document(s)`}
          </p>
        </div>
        <button
          type="button"
          onClick={clearConversation}
          disabled={messages.length === 0 || isSending}
          className="btn-ghost px-3 py-2 text-xs"
        >
          <TrashIcon className="h-4 w-4" />
          New chat
        </button>
      </header>

      <MessageThread messages={messages} />

      <ChatInputBar onSend={sendMessage} disabled={isSending} />
    </div>
  );
}

/** Fallback shown when the requested index does not exist (route guard). */
function MissingIndex({ indexId }: { indexId: string }) {
  return (
    <div className="mx-auto flex h-dvh w-full max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <h1 className="text-lg font-semibold text-ink">Knowledge index not found</h1>
      <p className="text-sm text-ink-muted">
        The index <span className="font-medium text-ink">{indexId}</span> does not
        exist. It may have been removed, or the id is incorrect.
      </p>
      <Link href="/" className="btn-primary">
        <ArrowLeftIcon className="h-4 w-4" />
        Back to documents
      </Link>
    </div>
  );
}
