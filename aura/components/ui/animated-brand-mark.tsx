"use client"

import { useRef, useCallback } from "react"
import { gsap } from "gsap"
import { useGSAP } from "@gsap/react"
import { cn } from "@/lib/utils"

interface AnimatedBrandMarkProps {
  className?: string
}

const PARTICLE_COLORS = ["#ff5a41", "#ffcf4a", "#ff8a3d", "#ffe08a"]

// Confetti dots seeded around the mark's centre in the particle SVG's 100×100 viewBox.
// The SVG is inset larger than the disc (see below), so the disc edge sits near radius ~26
// and particles bloom out to ~40–46 — clearly past the disc, still inside the viewBox
// (no clipping). Each dot starts collapsed at the centre and fires outward on hover.
const PARTICLES = Array.from({ length: 14 }, (_, i) => {
  const angle = (i / 14) * Math.PI * 2 - Math.PI / 2
  const dist = i % 2 === 0 ? 40 : 46
  return {
    x: Math.cos(angle) * dist,
    y: Math.sin(angle) * dist,
    r: i % 3 === 0 ? 3.4 : 2.5,
    color: PARTICLE_COLORS[i % PARTICLE_COLORS.length],
  }
})

export function AnimatedBrandMark({ className }: AnimatedBrandMarkProps) {
  const rootRef = useRef<HTMLSpanElement>(null)
  const discRef = useRef<HTMLSpanElement>(null)
  const coreRef = useRef<HTMLImageElement>(null)
  const particlesRef = useRef<(SVGCircleElement | null)[]>([])
  // Handlers live in refs so we never call contextSafe (which closes over
  // element refs) during render — that trips react-hooks/refs.
  const burstRef = useRef<() => void>(() => {})
  const settleRef = useRef<() => void>(() => {})

  useGSAP(
    () => {
      gsap.set(particlesRef.current, {
        transformOrigin: "center center",
        scale: 0,
        opacity: 0,
        x: 0,
        y: 0,
      })

      burstRef.current = () => {
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches
        if (reduced) return

        gsap.to(coreRef.current, {
          scale: 1.08,
          duration: 0.5,
          ease: "back.out(2.4)",
        })
        gsap.to(discRef.current, {
          boxShadow: "0 0 26px -4px rgba(244,80,59,0.55)",
          duration: 0.45,
          ease: "power2.out",
        })

        PARTICLES.forEach((p, i) => {
          const el = particlesRef.current[i]
          if (!el) return
          gsap.killTweensOf(el)
          gsap.fromTo(
            el,
            { x: 0, y: 0, scale: 0, opacity: 0 },
            {
              x: p.x,
              y: p.y,
              scale: 1,
              opacity: 1,
              duration: 0.55,
              ease: "back.out(2.6)",
              delay: i * 0.018,
              onComplete: () => {
                gsap.to(el, {
                  scale: 0.8,
                  opacity: 0.7,
                  duration: 0.8 + (i % 4) * 0.12,
                  ease: "sine.inOut",
                  yoyo: true,
                  repeat: -1,
                })
              },
            },
          )
        })
      }

      settleRef.current = () => {
        gsap.to(coreRef.current, { scale: 1, duration: 0.4, ease: "power3.out" })
        gsap.to(discRef.current, {
          boxShadow: "0 0 0px 0px rgba(244,80,59,0)",
          duration: 0.4,
          ease: "power2.out",
        })
        particlesRef.current.forEach((el) => {
          if (!el) return
          gsap.killTweensOf(el)
          gsap.to(el, { x: 0, y: 0, scale: 0, opacity: 0, duration: 0.3, ease: "power2.in" })
        })
      }
    },
    { scope: rootRef },
  )


  return (
    <span
      ref={rootRef}
      onMouseEnter={() => burstRef.current()}
      onMouseLeave={() => settleRef.current()}
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center rounded-full",
        className,
      )}
      aria-hidden="true"
    >
      <span
        ref={discRef}
        className="absolute inset-0 z-10 flex items-center justify-center overflow-hidden rounded-full border border-white/10 bg-black"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          ref={coreRef}
          src="/aura-logo.svg"
          alt=""
          width={48}
          height={48}
          className="pointer-events-none size-[80%] select-none object-contain object-center"
          draggable={false}
        />
      </span>
      <svg
        viewBox="0 0 100 100"
        className="pointer-events-none absolute -inset-[45%] z-20 overflow-visible [filter:drop-shadow(0_0_2px_rgba(255,150,70,0.55))]"
      >
        {PARTICLES.map((p, i) => (
          <circle
            key={i}
            ref={(el) => {
              particlesRef.current[i] = el
            }}
            cx={50}
            cy={50}
            r={p.r}
            fill={p.color}
          />
        ))}
      </svg>
    </span>
  )
}
