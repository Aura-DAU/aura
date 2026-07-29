import { cn } from "@/lib/utils"

interface BrandMarkProps {
  className?: string
  /** When true, renders the brand mark with the same warm glow highlight
   *  that the AnimatedBrandMark produces on hover — used during AI streaming. */
  isActive?: boolean
}

export function BrandMark({ className, isActive }: BrandMarkProps) {
  return (
    <span
      className={cn(
        // aspect-square guarantees a 1:1 ratio so rounded-full always renders as a perfect circle
        "relative inline-flex shrink-0 aspect-square items-center justify-center overflow-hidden rounded-full bg-black ring-1 ring-white/10 transition-[box-shadow] duration-500",
        isActive && "brand-mark-active ring-theme-red/40",
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
        className={cn(
          "pointer-events-none size-[80%] select-none object-contain object-center transition-transform duration-500",
          isActive && "scale-[1.08]",
        )}
        draggable={false}
      />
    </span>
  )
}
