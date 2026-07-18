import { BrandMark } from "@/components/ui/brand-mark"

interface StreamingIndicatorProps {
  thinkingStep?: string
}

export function StreamingIndicator({ thinkingStep }: StreamingIndicatorProps) {
  return (
    <div className="flex items-start gap-3">
      <BrandMark className="mt-0.5 size-8 text-sm" />
      <div className="flex items-center gap-3 pt-1.5">
        <div className="flex items-center gap-1" aria-hidden="true">
          <span className="size-2 animate-bounce rounded-full bg-theme-red [animation-delay:-0.3s]" />
          <span className="size-2 animate-bounce rounded-full bg-theme-yellow [animation-delay:-0.15s]" />
          <span className="size-2 animate-bounce rounded-full bg-theme-red" />
        </div>
        {thinkingStep ? (
          <span className="text-sm text-neutral-400">{thinkingStep}</span>
        ) : null}
        <span className="sr-only">AURA is responding</span>
      </div>
    </div>
  )
}
