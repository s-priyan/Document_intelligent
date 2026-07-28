/** Three-dot "assistant is thinking" animation shown while awaiting an answer. */
export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1" aria-label="Assistant is typing">
      {[0, 1, 2].map((index) => (
        <span
          key={index}
          className="h-2 w-2 rounded-full bg-ink-faint animate-typing-bounce"
          style={{ animationDelay: `${index * 0.15}s` }}
        />
      ))}
    </div>
  );
}
