import React from "react";

export default function CalendarLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="h-8 bg-surface-elevated rounded-lg w-1/3 mb-2" />
          <div className="h-4 bg-surface-elevated rounded w-1/2" />
        </div>
        <div className="flex gap-2">
          <div className="h-8 bg-surface-elevated rounded-full w-12" />
          <div className="h-8 bg-surface-elevated rounded-full w-16" />
        </div>
      </div>

      {/* Timeline skeleton */}
      <div className="space-y-6 ml-4">
        <div className="h-32 bg-surface-dau/20 border border-border-dau rounded-2xl w-full" />
        <div className="h-32 bg-surface-dau/20 border border-border-dau rounded-2xl w-full" />
      </div>
    </div>
  );
}
