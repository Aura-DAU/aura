import React from "react";

export default function TimetableLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="h-8 bg-surface-elevated rounded-lg w-1/3 mb-2" />
          <div className="h-4 bg-surface-elevated rounded w-1/2" />
        </div>
        <div className="h-10 bg-surface-elevated rounded-xl w-40" />
      </div>

      {/* Grid Skeleton */}
      <div className="bg-surface-dau/20 border border-border-dau rounded-2xl h-[400px] w-full" />
    </div>
  );
}
