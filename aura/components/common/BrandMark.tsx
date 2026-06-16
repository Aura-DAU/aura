import { cn } from "@/lib/utils"

interface BrandMarkProps {
  className?: string
}

export function BrandMark({ className }: BrandMarkProps) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow font-semibold text-black",
        className,
      )}
      aria-hidden="true"
    >
      A
    </span>
  )
}
