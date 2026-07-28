"use client";

/**
 * Chat session hook (FR-15, FR-18).
 *
 * Holds the active conversation in memory: the ordered list of turns and the
 * backend-issued `session_id`, which doubles as the LangGraph `thread_id`. The
 * session id is assigned from the first response and reused for every follow-up
 * so the backend retains multi-turn context. No persistence / DB is used.
 */

import { useCallback, useRef, useState } from "react";

import { ApiError, queryKnowledgeIndex } from "./api";
import type { ChatMessage } from "./types";

/** Generate a stable client-side id for a rendered message. */
function createMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export interface UseChatResult {
  messages: ChatMessage[];
  isSending: boolean;
  sessionId: string | null;
  sendMessage: (question: string) => Promise<void>;
  clearConversation: () => void;
}

/** Manage the chat thread and session lifecycle for a single knowledge index. */
export function useChat(indexId: string): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const sessionIdRef = useRef<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (question: string): Promise<void> => {
      const trimmed = question.trim();
      if (trimmed.length === 0 || isSending) {
        return;
        // Guard: ignore empty submissions and re-entrant sends.
      }

      const userMessage: ChatMessage = {
        id: createMessageId(),
        role: "user",
        content: trimmed,
      };
      const pendingId = createMessageId();
      const pendingMessage: ChatMessage = {
        id: pendingId,
        role: "assistant",
        content: "",
        pending: true,
      };
      setMessages((prev) => [...prev, userMessage, pendingMessage]);
      setIsSending(true);

      try {
        const response = await queryKnowledgeIndex(
          indexId,
          trimmed,
          sessionIdRef.current,
        );
        sessionIdRef.current = response.session_id;
        setSessionId(response.session_id);
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingId
              ? {
                  ...message,
                  content: response.answer,
                  citations: response.citations,
                  pending: false,
                }
              : message,
          ),
        );
      } catch (error) {
        const detail =
          error instanceof ApiError
            ? error.message
            : "Something went wrong while answering.";
        setMessages((prev) =>
          prev.map((message) =>
            message.id === pendingId
              ? { ...message, content: detail, pending: false, error: true }
              : message,
          ),
        );
      } finally {
        setIsSending(false);
      }
    },
    [indexId, isSending],
  );

  const clearConversation = useCallback((): void => {
    sessionIdRef.current = null;
    setSessionId(null);
    setMessages([]);
  }, []);

  return { messages, isSending, sessionId, sendMessage, clearConversation };
}
