"use client";

import { useEffect, useRef } from "react";

import { SparkleIcon } from "@/components/ui/Icons";
import type { ChatMessage, Citation } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

interface MessageThreadProps {
  messages: ChatMessage[];
  onCitation: (citations: Citation[], position: number) => void;
}

/** How close to the bottom the reader must be for the thread to keep following. */
const NEAR_BOTTOM_PX = 80;

/** How long after a reader gesture to distrust scroll events queued before it. */
const GESTURE_SETTLE_MS = 150;

/** Scrollable, auto-following list of chat turns with an empty state (FR-14). */
export function MessageThread({ messages, onCitation }: MessageThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const followRef = useRef(true);
  const gestureAtRef = useRef(0);

  useEffect(() => {
    if (!followRef.current) {
      return;
      // The reader scrolled up to catch up; streaming must not yank them back.
    }
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  /**
   * Resume following once the reader comes back to the bottom.
   *
   * This only ever re-attaches. Scroll events are coalesced to one per frame,
   * so a fast turn can append several tokens in the frame after an auto-scroll
   * and the resulting event reports a large gap while still legitimately
   * following; treating that as intent to leave would stall mid-answer.
   */
  const resumeFollow = (event: React.UIEvent<HTMLDivElement>): void => {
    if (performance.now() - gestureAtRef.current < GESTURE_SETTLE_MS) {
      return;
      // An auto-scroll queued just before the gesture still reports the old
      // position, which would re-attach the thread the reader just left.
    }

    const { scrollHeight, scrollTop, clientHeight } = event.currentTarget;
    if (scrollHeight - scrollTop - clientHeight < NEAR_BOTTOM_PX) {
      followRef.current = true;
    }
  };

  /**
   * Detach as soon as the reader drags the thread away from the live end.
   *
   * Wheel and touch events fire synchronously, ahead of any render, so they
   * capture the intent before a token arriving in the same frame can scroll
   * back down and make the coalesced scroll event look like "still at bottom".
   */
  const pauseFollow = (container: HTMLDivElement): void => {
    gestureAtRef.current = performance.now();
    if (container.scrollTop > 0) {
      followRef.current = false;
    }
    // At the very top there is nothing to pull away from, so stay attached.
  };

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
    <div
      className="min-h-0 flex-1 overflow-y-auto"
      onScroll={resumeFollow}
      onWheel={(event) => {
        if (event.deltaY < 0) {
          pauseFollow(event.currentTarget);
        }
      }}
      onTouchMove={(event) => pauseFollow(event.currentTarget)}
    >
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} onCitation={onCitation} />
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
