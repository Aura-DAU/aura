"use client";

import React from "react";

export default function GateResourcesPage() {
  const syllabus = [
    { section: "Engineering Mathematics", topics: "Discrete Mathematics, Linear Algebra, Calculus, Probability and Statistics." },
    { section: "Digital Logic", topics: "Boolean algebra, combinational and sequential circuits, minimization, number representations." },
    { section: "Computer Organization", topics: "Machine instructions, addressing modes, ALU, data-path, CPU control design, memory hierarchy, I/O interface." },
    { section: "Programming & Data Structures", topics: "Programming in C. Recursion. Arrays, stacks, queues, linked lists, trees, binary search trees, binary heaps, graphs." },
    { section: "Algorithms", topics: "Searching, sorting, hashing. Asymptotic worst case time and space complexity. Algorithm design techniques: greedy, dynamic programming, divide-and-conquer. Graph traversals, minimum spanning trees, shortest paths." },
    { section: "Theory of Computation", topics: "Regular expressions and finite automata. Context-free grammars and push-down automata. Regular and context-free languages, pumping lemma. Turing machines and undecidability." },
    { section: "Compiler Design", topics: "Lexical analysis, parsing, syntax-directed translation. Runtime environments. Intermediate code generation. Local optimization, data flow analyses." },
    { section: "Operating System", topics: "System calls, processes, threads, CPU scheduling, memory management, virtual memory, file systems, disk scheduling." },
    { section: "Databases", topics: "ER-model. Relational model: relational algebra, tuple calculus, SQL. Integrity constraints, normal forms. File organization, indexing (B and B+ trees). Transactions and concurrency control." },
    { section: "Computer Networks", topics: "OSI and TCP/IP stacks. Basics of packet switching. Data link layer, routing algorithms, congestion control. TCP/UDP and sockets. IPv4/IPv6, application layer protocols." },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          GATE Preparation Resources
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access syllabus breakdowns, recommended reference books, and preparation timelines for the Graduate Aptitude Test in Engineering.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Syllabus */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              GATE Syllabus Breakdown (Computer Science / IT)
            </h2>
            <div className="border border-border-dau rounded-2xl overflow-hidden text-xs sm:text-sm">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-border-dau font-bold text-slate-800">
                    <th className="px-4 py-3 w-1/3">Section</th>
                    <th className="px-4 py-3">Core Topics Covered</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {syllabus.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-4 py-3 font-bold text-slate-800 bg-slate-50/20">{item.section}</td>
                      <td className="px-4 py-3 text-slate-600 font-medium leading-relaxed">{item.topics}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Reference books & Mock tests */}
        <div className="space-y-6">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6 space-y-4">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">
              Recommended Reference Books
            </h2>
            <div className="space-y-3 text-xs text-slate-700 font-medium">
              <div className="bg-white p-3.5 rounded-xl border border-border-dau/50">
                <strong className="text-slate-900 block mb-0.5">Algorithms:</strong> Introduction to Algorithms by Cormen, Leiserson, Rivest, Stein (CLRS).
              </div>
              <div className="bg-white p-3.5 rounded-xl border border-border-dau/50">
                <strong className="text-slate-900 block mb-0.5">Operating Systems:</strong> Operating System Concepts by Silberschatz, Galvin, Gagne.
              </div>
              <div className="bg-white p-3.5 rounded-xl border border-border-dau/50">
                <strong className="text-slate-900 block mb-0.5">Computer Networks:</strong> Computer Networking by Kurose & Ross.
              </div>
            </div>
          </div>

          <div className="bg-orange-50 border border-orange-200/50 rounded-3xl p-6 text-xs text-slate-700">
            <h2 className="text-sm font-black text-[#E8400C] uppercase tracking-wider mb-2">
              GATE Online Test Portal
            </h2>
            <p className="leading-relaxed mb-4">
              Practicing mock papers under timed constraints is crucial. Access the university&apos;s mock portal below to take mock papers.
            </p>
            <a
              href="#"
              className="bg-[#E8400C] text-white text-[10px] font-black uppercase py-2.5 px-6 rounded-xl shadow-md shadow-[#E8400C]/20 transition-all duration-150 inline-block text-center"
            >
              Start Free Mock Test
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
