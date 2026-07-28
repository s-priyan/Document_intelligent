"use client";

import { useEffect, useRef } from "react";

import { SparkleIcon } from "@/components/ui/Icons";
import type { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

interface MessageThreadProps {
  messages: ChatMessage[];
}

/** Scrollable, auto-following list of chat turns with an empty state (FR-14). */
export function MessageThread({ messages }: MessageThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-faint text-accent">
          <SparkleIcon className="h-7 w-7" />
        </span>
        <div>
          <p className="text-base font-medium text-ink">Ask anything about your documents</p>
          <p className="mt-1 text-sm text-ink-muted">
            Answers are grounded in your uploaded files, with sources you can trace.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-5 overflow-y-auto px-4 py-6 sm:px-6">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
