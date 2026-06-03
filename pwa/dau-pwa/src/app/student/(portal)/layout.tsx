import React from "react";
import StudentTopBar from "@/components/features/student/StudentTopBar";
import StudentVerticalTabs from "@/components/features/student/StudentVerticalTabs";
import StudentSidebar from "@/components/features/student/StudentSidebar";
import StudentBottomNav from "@/components/features/student/StudentBottomNav";

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen bg-white text-slate-900 relative">
      {/* Shared Portal Topbar */}
      <StudentTopBar />

      {/* Main tab switching pills for desktop viewports */}
      <StudentVerticalTabs />

      {/* Portal Inner Structure: Sidebar + Responsive Content Area */}
      <div className="flex flex-1 relative">
        <StudentSidebar />

        <main className="flex-1 w-full p-4 sm:p-6 md:p-8 pb-20 md:pb-8 overflow-y-auto">
          <div className="max-w-6xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>

      {/* Bottom bar switcher for mobile screens */}
      <StudentBottomNav />
    </div>
  );
}
