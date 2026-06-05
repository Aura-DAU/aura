"use client";

import React, { useState, useEffect } from "react";
import { getEventsList, EventItem } from "@/services/studentServices";
import { fetchStudentServiceDocument } from "@/services/studentServices";
import MarkdownRenderer from "@/components/ui/MarkdownRenderer";

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [filter, setFilter] = useState("All");
  const [loading, setLoading] = useState(true);

  // Detail Modal State
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [eventContent, setEventContent] = useState("");
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    async function loadEvents() {
      try {
        const list = await getEventsList();
        setEvents(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadEvents();
  }, []);

  const categories = ["All", "Workshop / Seminar", "Sports Event", "Alumni Connect", "Campus News"];

  const filteredEvents = events.filter((ev) => {
    return filter === "All" || ev.category === filter;
  });

  const handleOpenEvent = async (event: EventItem) => {
    setSelectedEvent(event);
    setLoadingContent(true);
    setEventContent("");
    try {
      const res = await fetchStudentServiceDocument({ fileName: event.fileName });
      if (res.success && res.content) {
        setEventContent(res.content);
      } else {
        setEventContent("Could not load details for this event.");
      }
    } catch {
      setEventContent("Error loading details for this event.");
    } finally {
      setLoadingContent(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Daily Campus Events & News
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Stay updated with daily announcements, guest lectures, sports achievements, and student events.
          </p>
        </div>

        {/* Filter pills */}
        <div className="flex gap-1.5 overflow-x-auto pb-1 max-w-full scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1.5 rounded-full text-[10px] font-black tracking-wider uppercase whitespace-nowrap transition-all duration-255 ${
                filter === cat
                  ? "bg-[#E8400C] text-white shadow-md shadow-[#E8400C]/20"
                  : "bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Events timeline grid */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse bg-slate-50 border border-border-dau rounded-3xl p-6 h-28" />
          ))}
        </div>
      ) : filteredEvents.length > 0 ? (
        <div className="space-y-4 max-w-4xl">
          {filteredEvents.map((event, idx) => (
            <div
              key={idx}
              className="bg-white border border-border-dau rounded-3xl p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 text-[8px] font-black uppercase tracking-wider rounded bg-orange-50 border border-orange-200/50 text-[#E8400C]">
                    {event.category}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono font-bold">
                    {event.date}
                  </span>
                </div>
                <h3 className="text-xs sm:text-sm font-black text-slate-900 leading-tight">
                  {event.title}
                </h3>
              </div>

              <button
                onClick={() => handleOpenEvent(event)}
                className="shrink-0 bg-slate-50 text-slate-700 hover:bg-[#E8400C]/5 hover:text-[#E8400C] text-[10px] font-black uppercase py-2.5 px-5 rounded-xl border border-slate-100 hover:border-[#E8400C]/20 transition-all duration-150"
              >
                Read Details
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <svg className="w-8 h-8 text-slate-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-slate-500 font-bold">No events found matching this category.</p>
        </div>
      )}

      {/* Details Dialog Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col border border-border-dau shadow-2xl">
            {/* Modal Header */}
            <div className="p-6 border-b border-border-dau bg-slate-50/50 flex justify-between items-start gap-4">
              <div>
                <span className="text-[9px] font-black uppercase tracking-wider text-[#E8400C] block mb-1">
                  {selectedEvent.category} • {selectedEvent.date}
                </span>
                <h2 className="text-base font-black text-slate-900 leading-tight">
                  {selectedEvent.title}
                </h2>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="p-1 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l18 18" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-4">
              {loadingContent ? (
                <div className="space-y-3 animate-pulse">
                  <div className="h-4 bg-slate-100 rounded w-full" />
                  <div className="h-4 bg-slate-100 rounded w-5/6" />
                </div>
              ) : (
                <div className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-700 leading-relaxed">
                  <MarkdownRenderer content={eventContent} />
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border-dau bg-slate-50/50 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="bg-[#E8400C] text-white text-[10px] font-black uppercase py-2.5 px-6 rounded-xl hover:bg-[#D7380A] transition-colors"
              >
                Close Announcement
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
