import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeSanitize, { defaultSchema } from "rehype-sanitize"
import { CodeBlock } from "@/components/ui/code-block"

import { Citation } from "@/lib/chat-types"
import { useDocumentViewer } from "@/hooks/use-document-viewer"

// Allow fragment-only hrefs (#citation-N) through the sanitizer.
const sanitizeSchema = {
  ...defaultSchema,
  protocols: {
    ...defaultSchema.protocols,
    href: [...(defaultSchema.protocols?.href ?? []), "#"],
  },
}

interface MarkdownContentProps {
  content: string
  citations?: Citation[]
}

function InlineCitation({ index, citation }: { index: number; citation: Citation }) {
  const { prefetchDocument, openDocument } = useDocumentViewer()
  const hasSource = Boolean(citation.path)

  if (!hasSource) {
    return (
      <span className="inline-flex items-center justify-center rounded-full bg-theme-gray/80 px-1.5 py-0.5 text-[10px] font-medium text-neutral-400 mx-0.5">
        {index}
      </span>
    )
  }

  const viewerTarget = {
    path: citation.path!,
    title: citation.title ?? citation.file,
    startLine: citation.startLine,
    endLine: citation.endLine,
  }

  return (
    <button
      type="button"
      onMouseEnter={() => {
        prefetchDocument(viewerTarget)
        openDocument(viewerTarget)
      }}
      onClick={() => openDocument(viewerTarget)}
      className="inline-flex items-center justify-center rounded-full bg-theme-gray px-1.5 py-0.5 text-[10px] font-medium text-theme-yellow hover:bg-theme-gray-light hover:text-neutral-100 transition-colors mx-0.5 cursor-pointer"
      aria-label={`View source: ${citation.title ?? citation.file}`}
    >
      {index}
    </button>
  )
}

/** Walk React children, splitting text nodes that contain [N] citation references. */
function processCitationChildren(
  children: React.ReactNode,
  citations: Citation[] | undefined,
): React.ReactNode {
  if (!citations || citations.length === 0) return children

  return React.Children.map(children, (child) => {
    if (typeof child !== "string") return child

    // Split on [1], [2], etc.  Keep delimiters via capture group.
    const parts = child.split(/(\[\d+\])/)
    if (parts.length === 1) return child // no citations found

    return parts.map((part, i) => {
      const match = /^\[(\d+)\]$/.exec(part)
      if (!match) return part
      const idx = parseInt(match[1], 10)
      const citation = citations[idx - 1]
      if (!citation) return part
      return <InlineCitation key={`cit-${idx}-${i}`} index={idx} citation={citation} />
    })
  })
}

function MarkdownContentInner({ content, citations }: MarkdownContentProps) {
  return (
    <div className="chat-v2-prose prose prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
        components={{
          // Process inline [N] citations inside paragraph text.
          p({ children, ...props }) {
            return <p {...props}>{processCitationChildren(children, citations)}</p>
          },
          li({ children, ...props }) {
            return <li {...props}>{processCitationChildren(children, citations)}</li>
          },
          td({ children, ...props }) {
            return <td {...props}>{processCitationChildren(children, citations)}</td>
          },
          // Also handle any that survived as markdown links (backup).
          a({ href, children, ...props }) {
            if (href?.startsWith("#citation-")) {
              const index = parseInt(href.replace("#citation-", ""), 10)
              const citation = citations?.[index - 1]
              if (citation) {
                return <InlineCitation index={index} citation={citation} />
              }
            }
            return (
              <a href={href} {...props} target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            )
          },
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "")
            const text = String(children).replace(/\n$/, "")
            const isMultiline = text.includes("\n") || Boolean(match)

            if (!isMultiline) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            }

            return <CodeBlock code={text} language={match?.[1]} />
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export const MarkdownContent = React.memo(MarkdownContentInner)

