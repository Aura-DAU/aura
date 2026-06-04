"use client";

import React, { useState, useEffect } from "react";
import { PolicyMetadata } from "@/lib/utils/courseParser";
import { fetchPolicyContent } from "@/lib/api/policies.action";
import PolicyList from "./PolicyList";
import PolicyDetailViewer from "./PolicyDetailViewer";

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

  // PDF Viewer Simulation states
  const [zoom, setZoom] = useState(100);
  const [fitWidth, setFitWidth] = useState(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 10, 50));
  const handleZoomReset = () => setZoom(100);
  const handleToggleFitWidth = () => setFitWidth((prev) => !prev);

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

  useEffect(() => {
    if (filteredPolicies.length > 0 && !selectedPolicy && window.innerWidth >= 768) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleSelectPolicy(filteredPolicies[0]);
    }
  }, [filteredPolicies, selectedPolicy]);

  // Extract unique categories for filter pills
  const categories = ["All", ...Array.from(new Set(policies.map((p) => p.category)))];

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-210px)] min-h-[500px]">
      <PolicyList
        policies={filteredPolicies}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        categories={categories}
        selectedCategory={selectedCategory}
        onSelectCategory={setSelectedCategory}
        selectedPolicy={selectedPolicy}
        onSelectPolicy={handleSelectPolicy}
      />

      <div className="md:col-span-8 flex flex-col h-full overflow-hidden bg-slate-900 rounded-[24px] border border-slate-800 shadow-xl">
        {selectedPolicy ? (
          <PolicyDetailViewer
            policy={selectedPolicy}
            content={policyContent}
            loading={loadingContent}
            zoom={zoom}
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onZoomReset={handleZoomReset}
            fitWidth={fitWidth}
            onToggleFitWidth={handleToggleFitWidth}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-950 text-slate-400 select-none">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-full mb-4">
              <svg className="w-10 h-10 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-base font-black text-white mb-1">Academic Regulation Archive</h3>
            <p className="text-xs text-slate-505 font-medium max-w-sm leading-relaxed">
              Select any policy handbook guideline or code of conduct from the list on the left to examine its official regulation specifications.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
