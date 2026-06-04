import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// We test the module after setting env so imports resolve correctly
describe("callRagPipeline", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
    global.fetch = vi.fn();
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  const validRequest = {
    message: "What is the hostel curfew?",
    history: [],
    student_profile: {
      name: "Test Student",
      branch: "ICT",
      year: "1st Year",
      semester: "Sem I",
      interests: "Coding",
    },
  };

  it("should throw when FASTAPI_RAG_URL is not set", async () => {
    delete process.env.FASTAPI_RAG_URL;
    const { callRagPipeline } = await import("./ragClient");
    await expect(callRagPipeline(validRequest)).rejects.toThrow(
      "FASTAPI_RAG_URL is not configured."
    );
  });

  it("should return RagChatResponse on a successful 200 response", async () => {
    process.env.FASTAPI_RAG_URL = "http://localhost:8000";
    const mockResponse = {
      success: true,
      content: "Hostel curfew is 10 PM.",
      citations: [{ title: "Hostel Rules (Student Services)", file: "hostel_rules.md" }],
    };
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => mockResponse,
    } as Response);

    const { callRagPipeline } = await import("./ragClient");
    const result = await callRagPipeline(validRequest);

    expect(result.success).toBe(true);
    expect(result.content).toBe("Hostel curfew is 10 PM.");
    expect(result.citations).toHaveLength(1);
  });

  it("should throw on non-2xx HTTP status", async () => {
    process.env.FASTAPI_RAG_URL = "http://localhost:8000";
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => ({}),
    } as Response);

    const { callRagPipeline } = await import("./ragClient");
    await expect(callRagPipeline(validRequest)).rejects.toThrow(
      "FastAPI returned HTTP 500"
    );
  });

  it("should throw when fetch itself throws (network error)", async () => {
    process.env.FASTAPI_RAG_URL = "http://localhost:8000";
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error("Network error"));

    const { callRagPipeline } = await import("./ragClient");
    await expect(callRagPipeline(validRequest)).rejects.toThrow("Network error");
  });
});
