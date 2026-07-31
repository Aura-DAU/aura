import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeSanitize, { defaultSchema } from "rehype-sanitize"
import { CodeBlock } from "@/components/ui/code-block"

import { Citation } from "@/lib/chat-types"
import { useDocumentViewer } from "@/hooks/use-document-viewer"

// Allow fragment-only hrefs (#citation-N) through the sanitizer.
// Also allow className on all elements for our highlight plugin.
const sanitizeSchema = {
  ...defaultSchema,
  protocols: {
    ...defaultSchema.protocols,
    href: [...(defaultSchema.protocols?.href ?? []), "#"],
  },
  attributes: {
    ...defaultSchema.attributes,
    "*": [...(defaultSchema.attributes?.["*"] ?? []), "className", "data-highlighted"],
  }
}

interface MarkdownContentProps {
  content: string
  citations?: Citation[]
  highlightStart?: number
  highlightEnd?: number
  sanitize?: boolean
}



// eslint-disable-next-line @typescript-eslint/no-explicit-any
function shouldHighlight(node: any, highlightStart?: number, highlightEnd?: number) {
  if (!node || !node.position || !highlightStart) return undefined;
  const start = node.position.start.line;
  const end = node.position.end.line;
  const targetEnd = highlightEnd ?? highlightStart;
  if (start <= targetEnd && end >= highlightStart) return "true";
  return undefined;
}

function InlineCitation({ index, citation }: { index: number; citation: Citation }) {
  const { prefetchDocument, openDocument } = useDocumentViewer()
  const hasSource = Boolean(citation.path)
  const hoverTimerRef = React.useRef<NodeJS.Timeout | null>(null)

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
        if (typeof window !== "undefined" && window.innerWidth < 768) return
        prefetchDocument(viewerTarget)
        if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
        hoverTimerRef.current = setTimeout(() => {
          openDocument(viewerTarget)
        }, 1000)
      }}
      onMouseLeave={() => {
        if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
      }}
      onClick={() => {
        window.open(citation.file, "_blank", "noopener,noreferrer")
      }}
      className="inline-flex items-center justify-center rounded-full bg-theme-gray px-1.5 py-0.5 text-[10px] font-medium text-theme-yellow hover:bg-theme-gray-light hover:text-neutral-100 transition-colors mx-0.5 cursor-pointer"
      aria-label={`View source: ${citation.title ?? citation.file}`}
    >
      {index}
    </button>
  )
}

function processCitationChildren(children: React.ReactNode, citations?: Citation[]) {
  if (!citations || citations.length === 0) return children

  return React.Children.map(children, (child, i) => {
    if (typeof child !== "string") return child

    // Regex to match [1], [2], etc.
    const parts = child.split(/(\[\d+\])/g)
    return parts.map((part, idx) => {
      const match = part.match(/^\[(\d+)\]$/)
      if (match) {
        const index = parseInt(match[1], 10)
        const citation = citations[index - 1]
        if (!citation) return part
        return <InlineCitation key={`cit-${idx}-${i}`} index={index} citation={citation} />
      }
      return part
    })
  })
}

function MarkdownContentInner({ content, citations, highlightStart, highlightEnd, sanitize = true }: MarkdownContentProps) {
  const containerRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (highlightStart) {
      // A small timeout ensures the DOM has updated and layout is calculated
      const id = requestAnimationFrame(() => {
        const el = containerRef.current?.querySelector("[data-highlighted='true']")
        if (el) {
          el.scrollIntoView({ block: "center", behavior: "smooth" })
        }
      })
      return () => cancelAnimationFrame(id)
    }
  }, [highlightStart, highlightEnd, content])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const rehypePlugins = sanitize ? [[rehypeSanitize, sanitizeSchema]] as any : []

  return (
    <div ref={containerRef} className="chat-v2-prose prose prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={rehypePlugins}
        components={{
          // Process inline [N] citations inside paragraph text.
          p({ node, children, ...props }) {
            return <p {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)}>{processCitationChildren(children, citations)}</p>
          },
          li({ node, children, ...props }) {
            return <li {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)}>{processCitationChildren(children, citations)}</li>
          },
          td({ node, children, ...props }) {
            return <td {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)}>{processCitationChildren(children, citations)}</td>
          },
          h1: ({ node, ...props }) => <h1 {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          h2: ({ node, ...props }) => <h2 {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          h3: ({ node, ...props }) => <h3 {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          h4: ({ node, ...props }) => <h4 {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          ul: ({ node, ...props }) => <ul {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          ol: ({ node, ...props }) => <ol {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          blockquote: ({ node, ...props }) => <blockquote {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
          table: ({ node, ...props }) => <table {...props} data-highlighted={shouldHighlight(node, highlightStart, highlightEnd)} />,
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

