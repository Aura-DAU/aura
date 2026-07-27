import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

interface AuroraBackgroundProps {
  children?: ReactNode
  className?: string
  /** Fade the aurora toward a soft focal point with a radial mask. */
  showRadialGradient?: boolean
}

/**
 * Minimal ambient aurora backdrop — a soft, slowly drifting warm brand haze
 * (`.aurora-layer` in globals.css), kept behind its children via an isolated
 * stacking context. Deliberately restrained; most of the surface stays black.
 */
export function AuroraBackground({
  children,
  className,
  showRadialGradient = true,
}: AuroraBackgroundProps) {
  return (
    <div className={cn("relative isolate overflow-hidden", className)}>
      <div
        aria-hidden="true"
        className={cn("aurora-layer -z-10", showRadialGradient && "aurora-layer--mask")}
      />
      {children}
    </div>
  )
}
