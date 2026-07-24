import { cn } from "@/lib/utils"

interface BrandMarkProps {
  className?: string
}

export function BrandMark({ className }: BrandMarkProps) {
  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-black ring-1 ring-white/10",
        className,
      )}
      aria-hidden="true"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/aura-logo.svg"
        alt=""
        width={48}
        height={48}
        className="pointer-events-none size-[80%] select-none object-contain object-center"
        draggable={false}
      />
    </span>
  )
}
