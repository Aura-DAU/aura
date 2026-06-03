import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchCourseContent } from "./courses.action";
import { getDocumentContent } from "@/lib/utils/courseParser";

vi.mock("@/lib/utils/courseParser", () => ({
  getDocumentContent: vi.fn(),
}));

describe("fetchCourseContent server action", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should successfully fetch course content on the happy path", async () => {
    const mockContent = "# Calculus Course Policy\nThis is course content.";
    vi.mocked(getDocumentContent).mockReturnValue(mockContent);

    const payload = {
      fileName: "course_policy_sc107_calculus.md",
    };

    const result = await fetchCourseContent(payload);

    expect(result.success).toBe(true);
    expect(result.content).toBe(mockContent);
    expect(getDocumentContent).toHaveBeenCalledWith(payload.fileName);
  });

  it("should throw an error for invalid input filename pattern", async () => {
    const payload = {
      fileName: "academic_policy_sc107.md", // Invalid prefix
    };

    await expect(fetchCourseContent(payload)).rejects.toThrow("Invalid input");
  });

  it("should throw an error for non-markdown filename extensions", async () => {
    const payload = {
      fileName: "course_policy_sc107.txt", // Invalid extension
    };

    await expect(fetchCourseContent(payload)).rejects.toThrow("Invalid input");
  });

  it("should return success: false when getDocumentContent throws an error", async () => {
    vi.mocked(getDocumentContent).mockImplementation(() => {
      throw new Error("File read error");
    });

    const payload = {
      fileName: "course_policy_sc107_calculus.md",
    };

    const result = await fetchCourseContent(payload);

    expect(result.success).toBe(false);
    expect(result.content).toContain("Failed to retrieve course content");
  });
});
