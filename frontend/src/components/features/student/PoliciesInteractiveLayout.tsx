"use client";

import React, { useState, useEffect } from "react";
import { PolicyMetadata } from "@/lib/utils/courseParser";
import { fetchPolicyContent } from "@/lib/api/policies.action";
import MarkdownRenderer from "./MarkdownRenderer";

interface PoliciesInteractiveLayoutProps {
  initialPolicies: PolicyMetadata[];
}

export default function PoliciesInteractiveLayout({
  initialPolicies,
}: PoliciesInteractiveLayoutProps) {
  const [policies] = useState<PolicyMetadata[]>(initialPolicies);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  // Selection & Details state
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyMetadata | null>(null);
  const [policyContent, setPolicyContent] = useState<string>("");
  const [loadingContent, setLoadingContent] = useState(false);

  // Filter lists based on inputs
  const filteredPolicies = policies.filter((policy) => {
    const matchesSearch = policy.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || policy.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleSelectPolicy = async (policy: PolicyMetadata) => {
    setSelectedPolicy(policy);
    setLoadingContent(true);
    try {
      const response = await fetchPolicyContent({ fileName: policy.fileName });
      if (response.success) {
        setPolicyContent(response.content);
      } else {
        setPolicyContent("Failed to load policy details.");
      }
    } catch (err) {
      console.error(err);
      setPolicyContent("An error occurred while fetching academic policy.");
    } finally {
      setLoadingContent(false);
    }
  };

  // Automatically select first policy on desktop if none selected
  useEffect(() => {
    if (filteredPolicies.length > 0 && !selectedPolicy && window.innerWidth >= 768) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleSelectPolicy(filteredPolicies[0]);
    }
  }, [filteredPolicies, selectedPolicy]);

  // Extract unique categories for filter pills
  const categories = ["All", ...Array.from(new Set(policies.map((p) => p.category)))];

  // PDF Viewer Simulation states
  const [zoom, setZoom] = useState(100);
  const [fitWidth, setFitWidth] = useState(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 10, 50));
  const handleZoomReset = () => setZoom(100);

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-210px)] min-h-[500px]">
      {/* Master List Pane (Left, 4 Cols) */}
      <div className="md:col-span-4 flex flex-col bg-white border border-[#E2E8F0] rounded-[24px] overflow-hidden h-full shadow-sm">
        {/* Search and Filters Header */}
        <div className="p-4 border-b border-[#E2E8F0] bg-slate-50/50 space-y-3">
          {/* Search bar */}
          <div className="relative">
            <svg
              className="absolute left-3.5 top-3 w-4 h-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search handbook..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-[#E2E8F0] rounded-[16px] pl-10 pr-4 py-2.5 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E8400C] focus:ring-1 focus:ring-[#E8400C]/20 transition-all duration-200"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-full text-[10px] font-black tracking-wider uppercase whitespace-nowrap transition-all duration-200 ${
                  selectedCategory === cat
                    ? "bg-[#E8400C] text-white shadow-md shadow-[#E8400C]/15"
                    : "bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable Policy Cards list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filteredPolicies.length > 0 ? (
            filteredPolicies.map((policy) => {
              const isSelected = selectedPolicy?.id === policy.id;

              return (
                <button
                  key={policy.id}
                  onClick={() => handleSelectPolicy(policy)}
                  className={`w-full text-left p-4 rounded-[16px] transition-all duration-200 border ${
                    isSelected
                      ? "bg-orange-50/80 border-orange-200 text-[#E8400C] shadow-sm font-bold border-l-4 border-l-[#E8400C] pl-3.5"
                      : "bg-white border-transparent hover:bg-slate-50 hover:border-slate-100 text-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[9px] font-black tracking-wide uppercase text-[#E8400C]">
                      {policy.category}
                    </span>
                  </div>
                  <h3 className={`text-xs font-black line-clamp-2 ${
                    isSelected ? "text-[#E8400C]" : "text-slate-900"
                  }`}>
                    {policy.title}
                  </h3>
                </button>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-center p-4">
              <svg
                className="w-8 h-8 text-slate-300 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-xs text-slate-500 font-bold">No policies found</p>
            </div>
          )}
        </div>
      </div>

      {/* Detail Pane (Right, 8 Cols) */}
      <div className="md:col-span-8 flex flex-col h-full overflow-hidden bg-slate-900 rounded-[24px] border border-slate-800 shadow-xl">
        {selectedPolicy ? (
          <>
            {/* Dynamic CSS for beautiful PDF-like printing */}
            <style>{`
              @media print {
                body {
                  background-color: white !important;
                  color: black !important;
                }
                /* Hide everything in layout except the specific PDF content sheet */
                div:not(#printable-pdf-document), 
                main, 
                aside, 
                nav, 
                button, 
                header {
                  display: none !important;
                }
                #printable-pdf-document {
                  display: block !important;
                  position: absolute;
                  left: 0;
                  top: 0;
                  width: 100% !important;
                  max-width: 100% !important;
                  border: none !important;
                  box-shadow: none !important;
                  padding: 0 !important;
                  margin: 0 !important;
                }
              }
            `}</style>

            {/* Premium Adobe-Style Dark PDF Reader Toolbar */}
            <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 text-slate-200 shrink-0 select-none">
              {/* Left Side: Document Icon & Name */}
              <div className="flex items-center gap-2.5">
                <div className="bg-[#E8400C] text-white text-[8px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
                  PDF
                </div>
                <span className="text-xs font-mono font-bold text-slate-300 tracking-tight max-w-[150px] sm:max-w-xs truncate">
                  {selectedPolicy.fileName.replace(/\.md$/, ".pdf").toLowerCase()}
                </span>
              </div>

              {/* Middle Section: Zoom Controls */}
              <div className="flex items-center gap-3">
                <button
                  onClick={handleZoomOut}
                  className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                  title="Zoom Out"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
                  </svg>
                </button>
                
                <button 
                  onClick={handleZoomReset}
                  className="text-[10px] font-mono font-black tracking-wider bg-slate-900 px-2 py-0.5 rounded border border-slate-700 text-slate-300 hover:text-white"
                  title="Reset Zoom"
                >
                  {zoom}%
                </button>

                <button
                  onClick={handleZoomIn}
                  className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                  title="Zoom In"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                </button>

                <div className="h-4 w-px bg-slate-700 mx-1 hidden sm:block" />

                <button
                  onClick={() => setFitWidth(!fitWidth)}
                  className={`p-1 rounded hover:bg-slate-700 transition-colors hidden sm:block ${
                    fitWidth ? "text-primary-dau" : "text-slate-400 hover:text-slate-100"
                  }`}
                  title="Fit to Width"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-5V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                  </svg>
                </button>
              </div>

              {/* Right Side: Print & View Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.print()}
                  className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                  title="Print Specification"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                  </svg>
                </button>

                <button
                  onClick={() => window.open(selectedPolicy.filePath, "_blank")}
                  className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                  title="Open Source Markdown"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Document Canvas Frame (Simulates dark gray workspace background) */}
            <div className="flex-1 overflow-y-auto p-6 bg-slate-800 scrollbar-thin scrollbar-thumb-slate-700">
              {loadingContent ? (
                <div className="space-y-6 animate-pulse max-w-[760px] mx-auto bg-white border border-slate-200 rounded p-8 sm:p-12 min-h-[800px]">
                  <div className="h-7 bg-slate-100 rounded w-1/3" />
                  <div className="space-y-2">
                    <div className="h-4 bg-slate-100 rounded w-full" />
                    <div className="h-4 bg-slate-100 rounded w-5/6" />
                    <div className="h-4 bg-slate-100 rounded w-4/5" />
                  </div>
                  <div className="h-6 bg-slate-100 rounded w-1/4 mt-8" />
                  <div className="h-24 bg-slate-50 rounded border border-slate-100 w-full" />
                </div>
              ) : (
                /* High-fidelity simulated A4 PDF Page Sheet */
                <div
                  id="printable-pdf-document"
                  className="mx-auto bg-white border border-slate-900/10 shadow-2xl p-8 sm:p-14 relative min-h-[1050px] transition-all duration-200 select-text"
                  style={{
                    width: fitWidth ? "100%" : `${720 * (zoom / 100)}px`,
                    fontFamily: "Georgia, serif",
                  }}
                >
                  {/* Elegant Academic Header Watermark */}
                  <div className="border-b border-slate-200 pb-3.5 mb-10 flex justify-between items-center text-[9px] text-slate-400 font-bold uppercase tracking-widest select-none">
                    <span className="text-[#E8400C] tracking-wide">Dhirubhai Ambani University</span>
                    <span>Official Registry &amp; Regulation Handbook</span>
                  </div>

                  {/* Handbook Content with serif document typeface styles */}
                  <div className="prose prose-slate max-w-none text-slate-800 text-[13px] leading-relaxed">
                    <MarkdownRenderer content={policyContent} />
                  </div>

                  {/* Elegant Academic Footer Watermark */}
                  <div className="mt-14 pt-3.5 border-t border-slate-100 flex justify-between items-center text-[8px] text-slate-400 font-bold uppercase tracking-widest select-none">
                    <span>DAU Handbook Division &copy; {new Date().getFullYear()}</span>
                    <span>Official Copy (1 / 1 Pages)</span>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-950 text-slate-400 select-none">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-full mb-4">
              <svg className="w-10 h-10 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-base font-black text-white mb-1">Academic Regulation Archive</h3>
            <p className="text-xs text-slate-500 font-medium max-w-sm leading-relaxed">
              Select any policy handbook guideline or code of conduct from the list on the left to examine its official regulation specifications.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
