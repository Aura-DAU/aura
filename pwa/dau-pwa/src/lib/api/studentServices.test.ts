import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "fs";

describe("studentServices server action", () => {
  let fetchStudentServiceDocument: typeof import("./studentServices.action").fetchStudentServiceDocument;
  let getFacultyList: typeof import("./studentServices.action").getFacultyList;
  let getEventsList: typeof import("./studentServices.action").getEventsList;

  beforeEach(async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.resetModules();
    const mod = await import("./studentServices.action");
    fetchStudentServiceDocument = mod.fetchStudentServiceDocument;
    getFacultyList = mod.getFacultyList;
    getEventsList = mod.getEventsList;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchStudentServiceDocument", () => {
    it("should successfully fetch document content on the happy path", async () => {
      vi.spyOn(fs, "existsSync").mockReturnValue(true);
      vi.spyOn(fs, "readFileSync").mockReturnValue(
        "---\ntitle: \"Hostel Guide\"\n---\nHostel Guidelines and Rules."
      );

      const payload = {
        fileName: "hostel_guide.md",
      };

      const result = await fetchStudentServiceDocument(payload);

      expect(result.success).toBe(true);
      expect(result.content).toBe("Hostel Guidelines and Rules.");
    });

    it("should throw validation error when fileName does not end in .md", async () => {
      const payload = {
        fileName: "hostel_guide.txt",
      };

      await expect(fetchStudentServiceDocument(payload)).rejects.toThrow("Invalid input");
    });

    it("should prevent directory traversal and handle file not found safely by returning success false", async () => {
      vi.spyOn(fs, "existsSync").mockReturnValue(false);

      const payload = {
        fileName: "../etc/passwd.md",
      };

      const result = await fetchStudentServiceDocument(payload);
      expect(result.success).toBe(false);
      expect(result.content).toContain("Failed to retrieve document content");
    });
  });

  describe("getFacultyList", () => {
    it("should parse faculty markdown files and return list", async () => {
      vi.spyOn(fs, "existsSync").mockReturnValue(true);
      vi.spyOn(fs, "readdirSync").mockReturnValue(["faculty_aditya.md"] as unknown as fs.Dirent[]);
      vi.spyOn(fs, "readFileSync").mockReturnValue(
        "---\ntitle: \"Dr. Aditya\"\n---\nemail: aditya@dau.ac.in\nFB-301\nspecialization\nMachine Learning\n# Main Content\nAssociate Professor"
      );

      const result = await getFacultyList();

      expect(result).toHaveLength(1);
      expect(result[0].name).toBe("Dr. Aditya");
      expect(result[0].email).toBe("aditya@dau.ac.in");
      expect(result[0].office).toBe("FB-301");
      expect(result[0].specialization).toBe("Machine Learning");
      expect(result[0].designation).toBe("Associate Professor");
    });

    it("should return empty list when directory does not exist", async () => {
      vi.spyOn(fs, "existsSync").mockReturnValue(false);

      const result = await getFacultyList();

      expect(result).toEqual([]);
    });
  });

  describe("getEventsList", () => {
    it("should parse events files and return merged sorted events", async () => {
      vi.spyOn(fs, "existsSync").mockReturnValue(true);
      vi.spyOn(fs, "readdirSync").mockReturnValue(["sports_fest.md"] as unknown as fs.Dirent[]);
      vi.spyOn(fs, "readFileSync").mockReturnValue(
        "---\ntitle: \"Sports Fest\"\nscraped_date: \"2026-06-20\"\n---\nSports fest details."
      );

      const result = await getEventsList();

      expect(result.length).toBeGreaterThan(1);
      const sportsFest = result.find((e) => e.title === "Sports Fest");
      expect(sportsFest).toBeDefined();
      expect(sportsFest?.date).toBe("2026-06-20");
      expect(sportsFest?.category).toBe("Sports Event");
      
      // Check date ordering (newest first)
      for (let i = 0; i < result.length - 1; i++) {
        expect(result[i].date.localeCompare(result[i + 1].date)).toBeGreaterThanOrEqual(0);
      }
    });
  });
});
