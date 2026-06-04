import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "fs";
import { callClaude } from "@/lib/ai/aiClient";

// Mock the AI client
vi.mock("@/lib/ai/aiClient", () => ({
  callClaude: vi.fn(),
}));

describe("askAura server action", () => {
  const originalEnv = process.env;
  let askAura: typeof import("./chat.action").askAura;

  beforeEach(async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.resetModules();
    const mod = await import("./chat.action");
    askAura = mod.askAura;
    
    process.env = { ...originalEnv };
    
    // Stub fs functions
    vi.spyOn(fs, "existsSync").mockReturnValue(true);
    vi.spyOn(fs, "readdirSync").mockImplementation((dirPath) => {
      if (typeof dirPath === "string" && dirPath.includes("student_services")) {
        return ["hostel_rules.md"] as unknown as fs.Dirent[];
      }
      return [] as unknown as fs.Dirent[];
    });
    vi.spyOn(fs, "readFileSync").mockReturnValue(
      "---\ntitle: \"Hostel Curfew Rules\"\n---\nHostel curfew timing is 10 PM. Students must register leaves online."
    );
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  it("should return validation error when input is invalid (empty message)", async () => {
    const payload = {
      message: "",
      history: [],
      studentProfile: {
        name: "Test Student",
        branch: "ICT",
        year: "1st Year",
        semester: "Sem I",
        interests: "Coding",
      },
    };

    const result = await askAura(payload);

    expect(result.success).toBe(false);
    expect(result.content).toContain("Invalid input");
    expect(result.citations).toEqual([]);
  });

  it("should successfully run offline fallback matching when ANTHROPIC_API_KEY is not set", async () => {
    process.env.ANTHROPIC_API_KEY = ""; // No API key -> offline fallback mode

    const payload = {
      message: "What is the hostel curfew timing?",
      history: [],
      studentProfile: {
        name: "Test Student",
        branch: "ICT",
        year: "1st Year",
        semester: "Sem I",
        interests: "Coding",
      },
    };

    const result = await askAura(payload);

    expect(result.success).toBe(true);
    expect(result.content).toContain("AURA Offline Assistant");
    expect(result.content).toContain("Hostel Curfew Rules");
    expect(result.content).toContain("timing is 10 PM");
    expect(result.citations).toHaveLength(1);
    expect(result.citations[0].title).toContain("Hostel Curfew Rules");
    expect(result.citations[0].file).toBe("hostel_rules.md");
  });

  it("should call callClaude when ANTHROPIC_API_KEY is configured", async () => {
    process.env.ANTHROPIC_API_KEY = "test-anthropic-key";
    
    const mockClaudeResponse = {
      success: true,
      content: "According to the hostel rules, the curfew is 10 PM.",
    };
    vi.mocked(callClaude).mockResolvedValue(mockClaudeResponse);

    const payload = {
      message: "What is the hostel curfew timing?",
      history: [],
      studentProfile: {
        name: "Test Student",
        branch: "ICT",
        year: "1st Year",
        semester: "Sem I",
        interests: "Coding",
      },
    };

    const result = await askAura(payload);

    expect(result.success).toBe(true);
    expect(result.content).toBe(mockClaudeResponse.content);
    expect(result.citations).toHaveLength(1);
    expect(vi.mocked(callClaude)).toHaveBeenCalled();
  });

  it("should gracefully handle callClaude failures", async () => {
    process.env.ANTHROPIC_API_KEY = "test-anthropic-key";
    
    vi.mocked(callClaude).mockResolvedValue({
      success: false,
      content: "Failed to connect to Claude AI services.",
    });

    const payload = {
      message: "What is the hostel curfew timing?",
      history: [],
      studentProfile: {
        name: "Test Student",
        branch: "ICT",
        year: "1st Year",
        semester: "Sem I",
        interests: "Coding",
      },
    };

    const result = await askAura(payload);

    expect(result.success).toBe(false);
    expect(result.content).toBe("Failed to connect to Claude AI services.");
  });
});
