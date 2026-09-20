import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Element overrides for answer markdown.
 *
 * Defined at module scope so the map is not rebuilt on every streamed token.
 * Block spacing comes from the wrapper's `space-y`, so blocks carry no margins
 * of their own.
 */
const components: Components = {
  p: ({ children }) => <p className="leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  h1: ({ children }) => <h3 className="text-base font-semibold text-ink">{children}</h3>,
  h2: ({ children }) => <h4 className="text-sm font-semibold text-ink">{children}</h4>,
  h3: ({ children }) => <h5 className="text-sm font-semibold text-ink">{children}</h5>,
  h4: ({ children }) => (
    <h6 className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{children}</h6>
  ),
  ul: ({ children }) => <ul className="list-disc space-y-1.5 pl-5 marker:text-ink-faint">{children}</ul>,
  ol: ({ children }) => (
    <ol className="list-decimal space-y-1.5 pl-5 marker:text-ink-faint">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed [&>ul]:mt-1.5 [&>ol]:mt-1.5">{children}</li>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      className="text-accent-soft underline underline-offset-2 hover:text-accent"
    >
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-canvas-sunken px-1.5 py-0.5 font-mono text-[0.8em] text-ink-soft">
      {children}
    </code>
  ),
  pre: ({ children }) => (
    <pre className="overflow-x-auto rounded-lg border border-line bg-canvas-sunken p-3 text-xs [&>code]:bg-transparent [&>code]:p-0">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-line pl-3 text-ink-soft">{children}</blockquote>
  ),
  hr: () => <hr className="border-line" />,
  table: ({ children }) => (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-line bg-canvas-sunken px-2 py-1.5 text-left font-semibold text-ink">
      {children}
    </th>
  ),
  td: ({ children }) => <td className="border border-line px-2 py-1.5 align-top">{children}</td>,
};

/** Render a grounded answer as formatted markdown rather than raw text (FR-14). */
export function AnswerMarkdown({ content }: { content: string }) {
  return (
    <div className="space-y-3 break-words text-sm text-ink-soft">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
