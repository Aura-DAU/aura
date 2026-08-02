"use client"

import { useEffect } from "react"
import { motion, stagger, useAnimate } from "framer-motion"

interface TextGenerateEffectProps {
  words: string
  className?: string
  /** Blur-in each word (Aceternity default); disable for a plain fade. */
  filter?: boolean
  duration?: number
}

/**
 * Aceternity "Text Generate Effect": staggers each word in with a fade + blur,
 * evoking a model composing its reply. Colour is inherited, so a gradient
 * text class on the caller styles the whole phrase as one continuous fill.
 */
export function TextGenerateEffect({
  words,
  className,
  filter = true,
  duration = 0.6,
}: TextGenerateEffectProps) {
  const [scope, animate] = useAnimate()
  const wordsArray = words.split(" ")

  useEffect(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    animate(
      "span",
      { opacity: 1, filter: filter ? "blur(0px)" : "none" },
      { duration: reduced ? 0 : duration, delay: reduced ? 0 : stagger(0.12) },
    )
  }, [words, animate, duration, filter])

  return (
    <span ref={scope} className={className}>
      {wordsArray.map((word, index) => (
        <motion.span
          key={`${word}-${index}`}
          className="opacity-0"
          style={{ filter: filter ? "blur(8px)" : "none" }}
        >
          {word}
          {index < wordsArray.length - 1 ? " " : ""}
        </motion.span>
      ))}
    </span>
  )
}
