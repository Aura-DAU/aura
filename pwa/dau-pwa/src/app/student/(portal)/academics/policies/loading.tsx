import React from "react";

export default function PoliciesLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="border-b border-border-dau pb-4">
        <div className="h-8 bg-surface-elevated rounded-lg w-1/4 mb-2" />
        <div className="h-4 bg-surface-elevated rounded w-1/2" />
      </div>

      {/* Grid Layout of Master-Detail Panel Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-190px)] min-h-[500px]">
        {/* Left Side List Skeleton */}
        <div className="md:col-span-4 flex flex-col bg-surface-dau/20 border border-border-dau rounded-2xl p-4 space-y-4">
          <div className="h-10 bg-surface-elevated rounded-xl w-full" />
          <div className="flex gap-2">
            <div className="h-6 bg-surface-elevated rounded-full w-12" />
            <div className="h-6 bg-surface-elevated rounded-full w-20" />
            <div className="h-6 bg-surface-elevated rounded-full w-16" />
          </div>
          <div className="flex-1 space-y-2 mt-4">
            <div className="h-16 bg-surface-elevated/60 rounded-xl w-full" />
            <div className="h-16 bg-surface-elevated/60 rounded-xl w-full" />
            <div className="h-16 bg-surface-elevated/60 rounded-xl w-full" />
            <div className="h-16 bg-surface-elevated/60 rounded-xl w-full" />
          </div>
        </div>

        {/* Right Side Content Skeleton */}
        <div className="md:col-span-8 bg-surface-dau/20 border border-border-dau rounded-2xl p-8 space-y-6 flex flex-col justify-center items-center">
          <div className="w-12 h-12 rounded-full bg-surface-elevated flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-text-muted animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <div className="h-4 bg-surface-elevated rounded w-1/3" />
          <div className="h-3 bg-surface-elevated rounded w-1/2" />
        </div>
      </div>
    </div>
  );
}
