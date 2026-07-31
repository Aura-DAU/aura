import { describe, it, expect } from "vitest"
import { computeHistoryTailStart } from "../hooks/use-aura-chat"

describe("computeHistoryTailStart (MEM-03)", () => {
  it("never skips past priorSummaryCount even when the window is full", () => {
    // 40 prior messages, only the first 10 summarised → the old MAX_TAIL_TURNS=16
    // clamp would have started at index 24 and dropped turns 10–23.
    expect(computeHistoryTailStart(10, 40)).toBe(10)
  })

  it("starts at priorSummaryCount when the unsummarised span fits", () => {
    expect(computeHistoryTailStart(4, 12)).toBe(4)
  })

  it("sends the full transcript when nothing has been summarised yet", () => {
    expect(computeHistoryTailStart(0, 30)).toBe(0)
  })

  it("clamps a summary pointer that overshoots the transcript", () => {
    expect(computeHistoryTailStart(99, 5)).toBe(5)
  })

  it("handles an empty transcript", () => {
    expect(computeHistoryTailStart(0, 0)).toBe(0)
  })
})
