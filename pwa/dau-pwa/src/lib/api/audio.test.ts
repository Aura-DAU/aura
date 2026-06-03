import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { transcribeAudio } from "./audio.action";

describe("transcribeAudio server action", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv, GROQ_API_KEY: "test-api-key" };
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  it("should successfully transcribe audio on the happy path", async () => {
    const mockResponseText = { text: "Hello, this is a test transcription." };
    
    // Mock global fetch
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponseText,
    });
    vi.stubGlobal("fetch", mockFetch);

    const payload = {
      audioBase64: "dGVzdC1hdWRpby1kYXRh", // base64 encoded "test-audio-data"
      filename: "test.webm",
    };

    const result = await transcribeAudio(payload);

    expect(result.success).toBe(true);
    expect(result.text).toBe(mockResponseText.text);
    expect(mockFetch).toHaveBeenCalledWith(
      "https://api.groq.com/openai/v1/audio/transcriptions",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer test-api-key",
        }),
      })
    );
  });

  it("should return failure when input validation fails (empty audioBase64)", async () => {
    const payload = {
      audioBase64: "", // Invalid: empty string
      filename: "test.webm",
    };

    const result = await transcribeAudio(payload);

    expect(result.success).toBe(false);
    expect(result.error).toContain("Invalid input");
  });

  it("should return failure when GROQ_API_KEY is not configured", async () => {
    process.env.GROQ_API_KEY = ""; // Invalid: not set

    const payload = {
      audioBase64: "dGVzdC1hdWRpby1kYXRh",
      filename: "test.webm",
    };

    const result = await transcribeAudio(payload);

    expect(result.success).toBe(false);
    expect(result.error).toContain("GROQ_API_KEY is not configured");
  });

  it("should return failure when Groq API returns non-OK status", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => "Unauthorized API Key",
    });
    vi.stubGlobal("fetch", mockFetch);

    const payload = {
      audioBase64: "dGVzdC1hdWRpby1kYXRh",
      filename: "test.webm",
    };

    const result = await transcribeAudio(payload);

    expect(result.success).toBe(false);
    expect(result.error).toContain("returned status code 401");
  });

  it("should return failure when a network or parsing error occurs", async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error("Network Error"));
    vi.stubGlobal("fetch", mockFetch);

    const payload = {
      audioBase64: "dGVzdC1hdWRpby1kYXRh",
      filename: "test.webm",
    };

    const result = await transcribeAudio(payload);

    expect(result.success).toBe(false);
    expect(result.error).toContain("Network Error");
  });
});
