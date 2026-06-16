import React from "react";
import { ChatMessage } from "@/app/api/chat.service";

interface MessageItemProps {
  msg: ChatMessage;
  userInitial: string;
}

function sanitizeUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === "https:" || parsed.protocol === "http:") return url;
    return null;
  } catch {
    return null;
  }
}



const BOLD_RE = /^\*\*(.+?)\*\*$/;           // **text**
const SOURCE_RE = /^\[Source:\s*([^\]]{1,200})\]$/; // [Source: …] — capped at 200
const MDLINK_RE = /^\[([^\]]{1,200})\]\(([^)]{1,500})\)$/; // [label](url)
const HTTP_RE = /^https?:\/\//;
const EMAIL_RE = /^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}$/; // RFC 5321 max lengths

// Tokeniser: split on bold, source-tags, markdown links, URLs, emails — separately,
// in bounded passes so no single regex drives the whole parse.
function parseInline(text: string): React.ReactNode[] {
  const cleaned = text.replace(/\[at\]/gi, "@").replace(/\[dot\]/gi, ".");

  // Stage 1: split on **bold** tokens (bounded lazy .+? is safe here — no nesting)
  const boldSplit = cleaned.split(/(\*\*[^*]{0,500}\*\*)/g);

  const nodes: React.ReactNode[] = [];

  boldSplit.forEach((chunk, i) => {
    if (BOLD_RE.test(chunk)) {
      nodes.push(
        <strong key={`b-${i}`} className="font-semibold text-brand-700">
          {chunk.slice(2, -2)}
        </strong>
      );
      return;
    }

    // Stage 2: tokenise the remaining plain text for links / emails
    // Split on: [Source:…], [label](url), raw https?:// URLs, emails
    const linkTokens = chunk.split(
      /(\[Source:[^\]]{0,200}\]|\[[^\]]{0,200}\]\([^)]{0,500}\)|https?:\/\/[^\s,)]{1,2048}|[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255})/g
    );

    linkTokens.forEach((part, j) => {
      const key = `${i}-${j}`;

      // [Source: …]
      const srcM = part.match(SOURCE_RE);
      if (srcM) {
        nodes.push(
          <span
            key={key}
            className="inline-flex items-center px-1.5 py-0.5 rounded-md text-[12px] font-medium bg-slate-100 text-slate-500 ml-1.5 border border-slate-200"
          >
            Source: {srcM[1]}
          </span>
        );
        return;
      }

      // [label](url) — markdown link
      const mdM = part.match(MDLINK_RE);
      if (mdM) {
        const safe = sanitizeUrl(mdM[2]);
        if (safe) {
          nodes.push(
            <a key={key} href={safe} target="_blank" rel="noopener noreferrer"
              className="text-brand-600 hover:text-brand-700 underline font-medium break-all">
              {mdM[1]}
            </a>
          );
        } else {
          nodes.push(<span key={key}>{part}</span>);
        }
        return;
      }

      // Raw https?:// URL
      if (HTTP_RE.test(part)) {
        const safe = sanitizeUrl(part);
        if (safe) {
          nodes.push(
            <a key={key} href={safe} target="_blank" rel="noopener noreferrer"
              className="text-brand-600 hover:text-brand-700 underline font-medium break-all">
              {part}
            </a>
          );
        } else {
          nodes.push(<span key={key}>{part}</span>);
        }
        return;
      }

      // Email address
      if (EMAIL_RE.test(part) && !part.includes(" ")) {
        nodes.push(
          <a key={key} href={`mailto:${part}`}
            className="text-brand-600 hover:text-brand-700 underline">
            {part}
          </a>
        );
        return;
      }

      nodes.push(part);
    });
  });

  return nodes;
}

function parseMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];
  let listKey = 0;

  const flushList = () => {
    if (currentList.length > 0) {
      elements.push(
        <ul key={`list-${listKey++}`} className="list-disc pl-5 mb-4 space-y-1">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed === "") { flushList(); continue; }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushList();
      const level = headingMatch[1].length;
      const content = headingMatch[2];
      const parsedContent = parseInline(content);
      switch (level) {
        case 1: elements.push(<h1 key={`h1-${i}`} className="text-lg font-bold mt-6 mb-3 text-slate-900">{parsedContent}</h1>); break;
        case 2: elements.push(<h2 key={`h2-${i}`} className="text-base font-bold mt-5 mb-2.5 text-slate-900">{parsedContent}</h2>); break;
        case 3: elements.push(<h3 key={`h3-${i}`} className="text-sm font-semibold mt-4 mb-2 text-slate-900">{parsedContent}</h3>); break;
        default: elements.push(<h4 key={`h4-${i}`} className="text-sm font-semibold mt-3 mb-1.5 text-slate-900">{parsedContent}</h4>);
      }
      continue;
    }

    const listMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
    if (listMatch) {
      currentList.push(
        <li key={`li-${i}`} className="text-slate-600 text-sm sm:text-base">
          {parseInline(listMatch[2])}
        </li>
      );
      continue;
    }

    flushList();
    elements.push(
      <p key={`p-${i}`} className="mb-3 text-slate-600 text-sm sm:text-base leading-relaxed">
        {parseInline(line)}
      </p>
    );
  }

  flushList();
  return elements;
}

function formatTimestamp(ts?: number): string {
  if (!ts) return "";
  return new Date(ts).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function CopyButton({ content }: { content: string }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      const safeToCopy = content
        .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "")
        .replace(/\u202E|\u200F|\u200B/g, "");
      await navigator.clipboard.writeText(safeToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable — silently ignore.
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="inline-flex items-center gap-1 text-[12px] text-slate-400 hover:text-slate-600 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
      title="Copy response"
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          Copied
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <rect x="8" y="8" width="12" height="12" rx="1.5" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M16 8V5.5A1.5 1.5 0 0014.5 4h-9A1.5 1.5 0 004 5.5v9A1.5 1.5 0 005.5 16H8" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

const MessageItem = React.memo(function MessageItem({ msg, userInitial }: MessageItemProps) {
  const isAssistant = msg.role === "assistant";
  const timeLabel = formatTimestamp(msg.timestamp);

  return (
    <div className="flex gap-4 group">
      <div
        className={`w-8 h-8 rounded-md flex items-center justify-center font-semibold text-xs shrink-0 select-none ${isAssistant
            ? "bg-brand-600 text-white"
            : "bg-slate-100 text-slate-600 border border-slate-200"
          }`}
      >
        {isAssistant ? "A" : userInitial}
      </div>

      <div className="flex-1 space-y-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-400">{isAssistant ? "AURA" : "You"}</span>
          {timeLabel && <span className="text-[12px] text-slate-400">{timeLabel}</span>}
        </div>
        <div
          className={`max-w-none leading-relaxed ${isAssistant
              ? "text-slate-700 space-y-3"
              : "text-slate-700 font-medium text-sm sm:text-base whitespace-pre-wrap"
            }`}
        >
          {isAssistant ? parseMarkdown(msg.content) : msg.content}
        </div>
        {isAssistant && (
          <div className="pt-1">
            <CopyButton content={msg.content} />
          </div>
        )}
      </div>
    </div>
  );
});

export default MessageItem;