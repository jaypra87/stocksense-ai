"use client";

import ReactMarkdown, { type Components } from "react-markdown";

// The model writes light markdown (bold, lists, the odd table). Mapped onto
// the app's type scale instead of the browser defaults.
const components: Components = {
  p: ({ children }) => <p className="my-1.5 leading-relaxed first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-1.5 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-1.5 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  h1: ({ children }) => <p className="my-1.5 font-semibold">{children}</p>,
  h2: ({ children }) => <p className="my-1.5 font-semibold">{children}</p>,
  h3: ({ children }) => <p className="my-1.5 font-semibold">{children}</p>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-accent underline underline-offset-4"
    >
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">{children}</code>
  ),
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border-b border-border py-1 pr-3 text-left font-semibold">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border-b border-border py-1 pr-3 tabular-nums">{children}</td>
  ),
};

export function Markdown({ text }: { text: string }) {
  return <ReactMarkdown components={components}>{text}</ReactMarkdown>;
}
