import React from "react";
import { PolicyMetadata } from "@/lib/utils/courseParser";

interface PolicyListProps {
  policies: PolicyMetadata[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
  categories: string[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
  selectedPolicy: PolicyMetadata | null;
  onSelectPolicy: (policy: PolicyMetadata) => void;
}

export default function PolicyList({
  policies,
  searchQuery,
  onSearchChange,
  categories,
  selectedCategory,
  onSelectCategory,
  selectedPolicy,
  onSelectPolicy,
}: PolicyListProps) {
  return (
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
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-white border border-[#E2E8F0] rounded-[16px] pl-10 pr-4 py-2.5 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-primary-dau focus:ring-1 focus:ring-primary-dau/20 transition-all duration-200"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => onSelectCategory(cat)}
              className={`px-3 py-1.5 rounded-full text-[10px] font-black tracking-wider uppercase whitespace-nowrap transition-all duration-200 ${
                selectedCategory === cat
                  ? "bg-primary-dau text-white shadow-md shadow-primary-dau/15"
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
        {policies.length > 0 ? (
          policies.map((policy) => {
            const isSelected = selectedPolicy?.id === policy.id;

            return (
              <button
                key={policy.id}
                type="button"
                onClick={() => onSelectPolicy(policy)}
                className={`w-full text-left p-4 rounded-[16px] transition-all duration-200 border ${
                  isSelected
                    ? "bg-orange-50/80 border-orange-200 text-primary-dau shadow-sm font-bold border-l-4 border-l-primary-dau pl-3.5"
                    : "bg-white border-transparent hover:bg-slate-50 hover:border-slate-100 text-slate-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-[9px] font-black tracking-wide uppercase text-primary-dau">
                    {policy.category}
                  </span>
                </div>
                <h3 className={`text-xs font-black line-clamp-2 ${
                  isSelected ? "text-primary-dau" : "text-slate-900"
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
  );
}
