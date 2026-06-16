"use client";

import { motion } from "framer-motion";

const STARTERS = [
  "When does the next semester start?",
  "How do I apply for hostel allotment?",
  "Show me B.Tech ICT semester V syllabus",
  "What is the attendance policy?",
];

interface EmptyStateProps {
  onSelectStarter: (text: string) => void;
}

export default function EmptyState({ onSelectStarter }: EmptyStateProps) {
  return (
    <div className="flex w-full flex-1 flex-col items-center justify-center px-4 py-12 text-center md:text-left md:items-start md:justify-center">
      <div className="mx-auto w-full max-w-3xl">
        <motion.h1
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="text-center text-4xl font-semibold tracking-tight md:text-left lg:text-6xl"
        >
          <span className="bg-gradient-to-r from-white to-theme-gray-lighter bg-clip-text text-transparent">
            How can I
          </span>{" "}
          <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-transparent">
            help you today?
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.05 }}
          className="mt-4 text-center text-base text-muted-foreground md:text-left"
        >
          Ask AURA anything about Dhirubhai Ambani University — academics, hostels, schedules, syllabus.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.1 }}
          className="mt-8 flex flex-wrap justify-center gap-2 md:justify-start"
        >
          {STARTERS.map((starter) => (
            <button
              key={starter}
              type="button"
              onClick={() => onSelectStarter(starter)}
              className="group inline-flex items-center rounded-full border border-theme-gray-light bg-theme-gray-light/30 px-4 py-2 text-sm text-foreground backdrop-blur-sm transition-colors hover:border-theme-red/40 hover:bg-theme-gray-light/60"
            >
              <span className="mr-2 h-2 w-2 rounded-full bg-theme-red" />
              <span>{starter}</span>
            </button>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
