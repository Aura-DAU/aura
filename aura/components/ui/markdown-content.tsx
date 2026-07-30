import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeSanitize from "rehype-sanitize"
import { CodeBlock } from "@/components/ui/code-block"

interface MarkdownContentProps {
  content: string
}

function MarkdownContentInner({ content }: MarkdownContentProps) {
  return (
    <div className="chat-v2-prose prose prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
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
