import React from "react";

export default function AcademicsLoading() {
  return (
    <div className="space-y-6 w-full animate-pulse max-w-4xl">
      <div className="border-b border-slate-200 pb-4">
        <div className="h-8 bg-slate-100 rounded w-1/4" />
        <div className="h-4 bg-slate-100 rounded w-1/2 mt-2" />
      </div>
      <div className="bg-white border border-slate-250 rounded-3xl p-6 sm:p-10 shadow-sm space-y-4">
        <div className="h-6 bg-slate-100 rounded w-1/3" />
        <div className="space-y-2">
          <div className="h-4 bg-slate-100 rounded w-full" />
          <div className="h-4 bg-slate-100 rounded w-5/6" />
          <div className="h-4 bg-slate-100 rounded w-2/3" />
        </div>
      </div>
    </div>
  );
}
