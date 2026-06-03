"use client";

import React, { useState, useEffect } from "react";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";

const IEEE_FALLBACK = `### ieee student branch
- **Convenor:** Dr. Sanjay Srivastava
- **Focus:** Technical workshops, IEEE conferences, student projects, hackathons.
- **Join Process:** Register online at the start of the academic year.`;

const ECELL_FALLBACK = `### entrepreneurship cell
- **Convenor:** Prof. Manish K. Gupta
- **Focus:** Startup bootcamps, B-plan competitions, incubation support.
- **Join Process:** Open enrollment for all interested students.`;

export default function ClubsPage() {
  const [ieeeContent, setIeeeContent] = useState("");
  const [ecellContent, setEcellContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedClub, setSelectedClub] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [ieeeRes, ecellRes] = await Promise.all([
          fetchStudentServiceDocument({ fileName: "ieee_student_branch.md" }),
          fetchStudentServiceDocument({ fileName: "entrepreneurship_cell.md" }),
        ]);

        if (ieeeRes.success && ieeeRes.content) {
          setIeeeContent(ieeeRes.content);
        } else {
          setIeeeContent(IEEE_FALLBACK);
        }

        if (ecellRes.success && ecellRes.content) {
          setEcellContent(ecellRes.content);
        } else {
          setEcellContent(ECELL_FALLBACK);
        }
      } catch {
        setIeeeContent(IEEE_FALLBACK);
        setEcellContent(ECELL_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const clubs = [
    {
      id: "ieee",
      name: "IEEE Student Branch",
      type: "Technical",
      desc: "Promoting technological excellence, research papers, and technical events in electronics, CS, and AI.",
      logoBg: "bg-blue-100 text-blue-600 border-blue-200",
      content: ieeeContent,
    },
    {
      id: "ecell",
      name: "Entrepreneurship Cell (E-Cell)",
      type: "Technical & Management",
      desc: "Fostering startup ideas, business incubation, entrepreneurship bootcamps, and funding panels.",
      logoBg: "bg-emerald-100 text-emerald-600 border-emerald-200",
      content: ecellContent,
    },
    {
      id: "gdg",
      name: "Google Developer Groups (GDG)",
      type: "Technical",
      desc: "Google developer technologies, android hackathons, flutter bootcamps, and cloud studies.",
      logoBg: "bg-amber-100 text-amber-600 border-amber-200",
      content: "### Google Developer Groups\n\nGoogle Developer Groups (GDG) at DAU is a community for students interested in Google's developer technologies.\n\n- **Activities:** DevFest, Android bootcamps, Flutter study jams, Cloud study tracks.\n- **Faculty Mentor:** Dr. Amit Bhatt",
    },
    {
      id: "dance",
      name: "Dance Club (D-Club)",
      type: "Cultural",
      desc: "Expressing creativity through classical, contemporary, and hip-hop dance choreographies at events.",
      logoBg: "bg-purple-100 text-purple-600 border-purple-200",
      content: "### Dance Club\n\nThe Dance Club is a vibrant cultural wing of the university.\n\n- **Activities:** Annual Navratri Garba (Tarang), Synapse dance faceoffs, choreo workshops.\n- **Join:** Auditions are held in August.",
    },
    {
      id: "music",
      name: "Music Club (M-Club)",
      type: "Cultural",
      desc: "Uniting vocalists and instrumentalists for classical, fusion, rock band covers, and jam sessions.",
      logoBg: "bg-rose-100 text-rose-600 border-rose-200",
      content: "### Music Club\n\nM-Club is a haven for musicians and music lovers.\n\n- **Activities:** Open mic sessions, band wars, unplugged nights, classical music concerts.\n- **Join:** Auditions are held in August.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Student Clubs
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Discover student clubs, technical chapters, cultural communities, and sports leagues at Dhirubhai Ambani University.
        </p>
      </div>

      {/* Clubs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clubs.map((club, idx) => (
          <div
            key={idx}
            className="bg-white border border-border-dau rounded-3xl p-6 hover:shadow-xl hover:shadow-slate-100 hover:-translate-y-0.5 transition-all duration-200 flex flex-col justify-between"
          >
            <div>
              <div className="flex justify-between items-start mb-4">
                <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded bg-slate-50 border border-slate-100 text-slate-500">
                  {club.type}
                </span>
              </div>
              <h3 className="text-sm font-black text-slate-900 mb-2 leading-tight">
                {club.name}
              </h3>
              <p className="text-[10px] text-slate-500 font-medium leading-relaxed">
                {club.desc}
              </p>
            </div>

            <button
              onClick={() => setSelectedClub(club.id)}
              className="w-full mt-5 bg-[#E8400C] text-white hover:bg-[#D7380A] text-[10px] font-black uppercase py-2.5 px-4 rounded-xl shadow-md shadow-[#E8400C]/10 transition-all duration-150 text-center"
            >
              Explore Club Details
            </button>
          </div>
        ))}
      </div>

      {/* Club Details Modal Dialog */}
      {selectedClub && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-xl w-full max-h-[80vh] overflow-hidden flex flex-col border border-border-dau shadow-2xl">
            {/* Modal Header */}
            <div className="p-6 border-b border-border-dau bg-slate-50/50 flex justify-between items-start">
              <div>
                <h2 className="text-base font-black text-slate-900 leading-tight">
                  {clubs.find((c) => c.id === selectedClub)?.name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedClub(null)}
                className="p-1 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l18 18" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loading ? (
                <div className="space-y-3 animate-pulse">
                  <div className="h-4 bg-slate-100 rounded w-full" />
                  <div className="h-4 bg-slate-100 rounded w-5/6" />
                </div>
              ) : (
                <div className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-700">
                  <MarkdownRenderer content={clubs.find((c) => c.id === selectedClub)?.content || ""} />
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border-dau bg-slate-50/50 flex justify-end">
              <button
                onClick={() => setSelectedClub(null)}
                className="bg-[#E8400C] text-white text-[10px] font-black uppercase py-2.5 px-6 rounded-xl hover:bg-[#D7380A] transition-colors"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
