import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchPolicyContent } from "./policies.action";
import { getDocumentContent } from "@/lib/utils/courseParser";

vi.mock("@/lib/utils/courseParser", () => ({
  getDocumentContent: vi.fn(),
}));

describe("fetchPolicyContent server action", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should successfully fetch policy content on the happy path", async () => {
    const mockContent = "# Attendance Policy\nThis is policy content.";
    vi.mocked(getDocumentContent).mockReturnValue(mockContent);

    const payload = {
      fileName: "academic_policy_attendance.md",
    };

    const result = await fetchPolicyContent(payload);

    expect(result.success).toBe(true);
    expect(result.content).toBe(mockContent);
    expect(getDocumentContent).toHaveBeenCalledWith(payload.fileName);
  });

  it("should throw an error for invalid input filename pattern", async () => {
    const payload = {
      fileName: "course_policy_attendance.md", // Invalid prefix
    };

    await expect(fetchPolicyContent(payload)).rejects.toThrow("Invalid input");
  });

  it("should throw an error for non-markdown filename extensions", async () => {
    const payload = {
      fileName: "academic_policy_attendance.txt", // Invalid extension
    };

    await expect(fetchPolicyContent(payload)).rejects.toThrow("Invalid input");
  });

  it("should return success: false when getDocumentContent throws an error", async () => {
    vi.mocked(getDocumentContent).mockImplementation(() => {
      throw new Error("File read error");
    });

    const payload = {
      fileName: "academic_policy_attendance.md",
    };

    const result = await fetchPolicyContent(payload);

    expect(result.success).toBe(false);
    expect(result.content).toContain("Failed to retrieve academic policy content");
  });
});
