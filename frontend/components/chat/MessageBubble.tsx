import { AlertIcon, SparkleIcon } from "@/components/ui/Icons";
import type { ChatMessage, Citation } from "@/lib/types";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { CitationList } from "./CitationList";
import { TypingIndicator } from "./TypingIndicator";

interface MessageBubbleProps {
  message: ChatMessage;
  onCitation: (citations: Citation[], position: number) => void;
}

/** A single chat turn: right-aligned user bubble or left-aligned assistant answer (FR-14). */
export function MessageBubble({ message, onCitation }: MessageBubbleProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-fade-in-up">
        <div className="max-w-[85%] rounded-bubble rounded-br-md bg-accent px-4 py-2.5 text-sm leading-relaxed text-white shadow-soft">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 animate-fade-in-up">
      <span
        className={[
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          message.error ? "bg-danger/10 text-danger" : "bg-accent-faint text-accent",
        ].join(" ")}
        aria-hidden
      >
        {message.error ? <AlertIcon className="h-4 w-4" /> : <SparkleIcon className="h-4 w-4" />}
      </span>

      <div className="min-w-0 max-w-[85%] rounded-bubble rounded-tl-md border border-line bg-canvas-raised px-4 py-3 shadow-soft">
        {message.pending && message.content.length === 0 ? (
          <TypingIndicator />
        ) : (
          <>
            {message.error ? (
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-danger">
                {message.content}
              </p>
            ) : (
              <AnswerMarkdown content={message.content} />
            )}
            {!message.pending && message.citations ? (
              <CitationList citations={message.citations} onSelect={onCitation} />
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
