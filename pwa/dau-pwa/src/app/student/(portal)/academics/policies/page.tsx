import React from "react";
import { getPoliciesList } from "@/lib/utils/courseParser";
import PoliciesInteractiveLayout from "@/components/features/student/PoliciesInteractiveLayout";

// Force dynamic rendering since we are reading from filesystem at request time
export const dynamic = "force-dynamic";

export default function PoliciesPage() {
  const policies = getPoliciesList();

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Policies & Guidelines
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Explore the official Dhirubhai Ambani University academic policies, program requirements, and student code of conduct handbooks.
        </p>
      </div>

      {/* Main Interactive Master-Detail Portal Panel */}
      <PoliciesInteractiveLayout initialPolicies={policies} />
    </div>
  );
}
