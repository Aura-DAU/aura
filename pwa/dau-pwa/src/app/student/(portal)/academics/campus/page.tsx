"use client";

import React, { useState, useEffect } from "react";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";

const EMERGENCY_FALLBACK = `### emergency contacts
- **Security Main Gate:** +91 79 6826 1700
- **Ambulance (Campus):** +91 79 6826 1702
- **Medical Center Doctor:** +91 98250 XXXXX
- **Anti-Ragging Helpline:** 1800-180-5522`;

const MEDICAL_FALLBACK = `### medical assistance sop
1. Students should visit the Campus Dispensary located in the student service block for basic consultations.
2. In case of emergency, notify the resident warden or security guard immediately.
3. Ambulance will transport the student to the nearest partner hospital (Apollo/Shalby).`;

export default function CampusServicesPage() {
  const [emergencyContent, setEmergencyContent] = useState("");
  const [medicalContent, setMedicalContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"navigation" | "shuttle" | "emergency" | "medical">("navigation");

  useEffect(() => {
    async function loadData() {
      try {
        const [emRes, medRes] = await Promise.all([
          fetchStudentServiceDocument({ fileName: "emergency_contact_details.md" }),
          fetchStudentServiceDocument({ fileName: "medical_assistance_sop.md" }),
        ]);

        if (emRes.success && emRes.content) {
          setEmergencyContent(emRes.content);
        } else {
          setEmergencyContent(EMERGENCY_FALLBACK);
        }

        if (medRes.success && medRes.content) {
          setMedicalContent(medRes.content);
        } else {
          setMedicalContent(MEDICAL_FALLBACK);
        }
      } catch {
        setEmergencyContent(EMERGENCY_FALLBACK);
        setMedicalContent(MEDICAL_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const shuttleSchedule = [
    { route: "DAU Campus to Gandhinagar Sector 21", timing: "08:15 AM, 01:30 PM, 05:45 PM, 08:30 PM", type: "Daily Shuttle" },
    { route: "DAU Campus to Ahmedabad (Kalupur Station)", timing: "07:00 AM, 02:00 PM, 06:15 PM", type: "Friday / Sunday Only" },
    { route: "DAU Campus to Infocity Circle", timing: "Every 30 minutes from 06:00 PM to 10:30 PM", type: "Daily Shuttle" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Campus Services & Navigation
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access campus maps, transport/shuttle timetables, dispensary SOPs, and emergency helpline contact numbers.
        </p>
      </div>

      {/* Campus Navigation Tabs */}
      <div className="flex border-b border-border-dau overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab("navigation")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "navigation"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Campus Maps & Library
        </button>
        <button
          onClick={() => setActiveTab("shuttle")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "shuttle"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Transport & Shuttles
        </button>
        <button
          onClick={() => setActiveTab("emergency")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "emergency"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Emergency Contacts
        </button>
        <button
          onClick={() => setActiveTab("medical")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "medical"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Medical SOP
        </button>
      </div>

      {/* Tab Contents */}
      <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
        {activeTab === "navigation" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
                  Library Hours (RC)
                </h2>
                <div className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 space-y-3">
                  <div className="flex justify-between text-xs font-medium text-slate-700">
                    <span>Weekdays (Mon - Fri)</span>
                    <span className="font-bold">09:00 AM - Midnight</span>
                  </div>
                  <div className="flex justify-between text-xs font-medium text-slate-700">
                    <span>Saturdays</span>
                    <span className="font-bold">09:00 AM - 09:00 PM</span>
                  </div>
                  <div className="flex justify-between text-xs font-medium text-slate-700">
                    <span>Sundays / Holidays</span>
                    <span className="font-bold">10:00 AM - 06:00 PM</span>
                  </div>
                  <div className="flex justify-between text-xs font-medium text-[#E8400C] bg-orange-50 p-2.5 rounded-lg">
                    <span>Exam Weeks</span>
                    <span className="font-black">24 Hours Open</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
                  Campus Facilities
                </h2>
                <div className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 space-y-3">
                  <div className="text-xs font-medium text-slate-700">
                    <strong className="text-slate-900 block mb-0.5">Dispensary:</strong> Student Services Block (24/7 doctor on call).
                  </div>
                  <div className="text-xs font-medium text-slate-700">
                    <strong className="text-slate-900 block mb-0.5">Cafeteria & Food Court:</strong> open 07:00 AM to 11:30 PM.
                  </div>
                  <div className="text-xs font-medium text-slate-700">
                    <strong className="text-slate-900 block mb-0.5">Sports Complex:</strong> open 06:00 AM - 09:00 AM &amp; 04:00 PM - 09:00 PM.
                  </div>
                </div>
              </div>
            </div>

            {/* Simulated interactive map section */}
            <div className="border border-border-dau rounded-2xl p-6 bg-slate-950 text-white flex flex-col items-center justify-center min-h-[220px]">
              <svg className="w-12 h-12 text-[#E8400C] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <h3 className="text-sm font-bold text-white mb-1">Interactive Campus Navigation Map</h3>
              <p className="text-xs text-slate-400 font-medium max-w-sm text-center mb-4 leading-relaxed">
                Explore classroom blocks, lab numbers, hostels, administration wings, and canteen hubs.
              </p>
              <a
                href="https://www.daiict.ac.in"
                target="_blank"
                rel="noreferrer"
                className="bg-[#E8400C] text-white text-xs font-black py-2.5 px-6 rounded-xl hover:bg-[#D7380A] shadow-md shadow-[#E8400C]/20 transition-all duration-150"
              >
                Open Google Maps Campus Location
              </a>
            </div>
          </div>
        )}

        {activeTab === "shuttle" && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
              Campus Shuttle Schedules
            </h2>
            <div className="border border-border-dau rounded-2xl overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse text-xs sm:text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-border-dau">
                    <th className="px-4 py-3 font-bold text-slate-900 uppercase">Route Details</th>
                    <th className="px-4 py-3 font-bold text-slate-900 uppercase">Departure Timings</th>
                    <th className="px-4 py-3 font-bold text-slate-900 uppercase">Service Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {shuttleSchedule.map((shuttle, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-4 py-3.5 font-bold text-slate-800">{shuttle.route}</td>
                      <td className="px-4 py-3.5 text-slate-600 font-medium font-mono">{shuttle.timing}</td>
                      <td className="px-4 py-3.5">
                        <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded bg-orange-50 border border-orange-200/50 text-[#E8400C]">
                          {shuttle.type}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === "emergency" && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
              Emergency Contact Handbooks
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={emergencyContent} />
              </div>
            )}
          </div>
        )}

        {activeTab === "medical" && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
              Standard Medical Assistance SOP
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={medicalContent} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
