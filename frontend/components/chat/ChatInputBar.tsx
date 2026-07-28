"use client";

import { useCallback, useRef, useState } from "react";

import { SendIcon, SpinnerIcon } from "@/components/ui/Icons";

interface ChatInputBarProps {
  onSend: (question: string) => void;
  disabled?: boolean;
}

/** Auto-growing chat composer; Enter sends, Shift+Enter inserts a newline (FR-14). */
export function ChatInputBar({ onSend, disabled }: ChatInputBarProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) {
      return;
    }
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, []);

  const submit = useCallback(() => {
    const trimmed = value.trim();
    if (trimmed.length === 0 || disabled) {
      return;
    }
    onSend(trimmed);
    setValue("");
    requestAnimationFrame(resize);
  }, [value, disabled, onSend, resize]);

  return (
    <div className="border-t border-line bg-canvas-raised px-4 py-3 sm:px-6">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-card border border-line bg-canvas px-3 py-2 shadow-soft focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/25">
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={(event) => {
            setValue(event.target.value);
            resize();
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              submit();
            }
          }}
          placeholder={"Ask a question about your documents\u2026"}
          className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm text-ink placeholder:text-ink-faint focus:outline-none"
          aria-label="Message"
        />
        <button
          type="button"
          onClick={submit}
          disabled={disabled || value.trim().length === 0}
          aria-label="Send message"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
        >
          {disabled ? (
            <SpinnerIcon className="h-4 w-4" />
          ) : (
            <SendIcon className="h-4 w-4" />
          )}
        </button>
      </div>
    </div>
  );
}
