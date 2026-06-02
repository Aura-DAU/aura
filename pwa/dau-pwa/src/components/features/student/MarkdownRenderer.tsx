"use client";

import React from "react";

interface MarkdownRendererProps {
  content: string;
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  if (!content) return <p className="text-slate-400 italic">No content available.</p>;

  // Clean the content of PDF page splits, page indicators, and zero-width spaces (\u200b)
  const cleanContent = content
    .replace(/[\u200b\u200c\u200d\ufeff]/g, "") // Clean zero-width chars
    .replace(/---[\s\S]*?\*Page Split\*[\s\S]*?---/g, "\n\n")
    .replace(/Page No \d+ of \d+/g, "")
    .replace(/---/g, "\n")
    .trim();

  const lines = cleanContent.split("\n");
  const elements: React.ReactNode[] = [];

  let inList = false;
  let listItems: string[] = [];
  let listType: "bullet" | "number" = "bullet";

  let inTable = false;
  let tableHeaders: string[] = [];
  let tableRows: string[][] = [];

  const flushList = (key: string) => {
    if (listItems.length > 0) {
      if (listType === "bullet") {
        elements.push(
          <ul key={`ul-${key}`} className="list-disc pl-5 my-3 space-y-1.5 text-xs sm:text-sm text-slate-700 leading-relaxed list-inside">
            {listItems.map((item, idx) => (
              <li key={idx} dangerouslySetInnerHTML={{ __html: formatInline(item) }} />
            ))}
          </ul>
        );
      } else {
        elements.push(
          <ol key={`ol-${key}`} className="list-decimal pl-5 my-3 space-y-1.5 text-xs sm:text-sm text-slate-700 leading-relaxed list-inside">
            {listItems.map((item, idx) => (
              <li key={idx} dangerouslySetInnerHTML={{ __html: formatInline(item) }} />
            ))}
          </ol>
        );
      }
      listItems = [];
      inList = false;
    }
  };

  const flushTable = (key: string) => {
    if (tableHeaders.length > 0 || tableRows.length > 0) {
      elements.push(
        <div key={`table-wrapper-${key}`} className="my-5 overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left border-collapse text-xs sm:text-sm">
            {tableHeaders.length > 0 && (
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  {tableHeaders.map((header, idx) => (
                    <th
                      key={idx}
                      className="px-4 py-2.5 font-bold text-slate-900 uppercase tracking-wider"
                      dangerouslySetInnerHTML={{ __html: formatInline(header) }}
                    />
                  ))}
                </tr>
              </thead>
            )}
            <tbody className="divide-y divide-slate-100 bg-white">
              {tableRows.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-slate-50/50 transition-colors">
                  {row.map((cell, cellIdx) => (
                    <td
                      key={cellIdx}
                      className="px-4 py-2.5 text-slate-600 font-medium"
                      dangerouslySetInnerHTML={{ __html: formatInline(cell) }}
                    />
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableHeaders = [];
      tableRows = [];
      inTable = false;
    }
  };

  // Inline formatting helper (Bold, Italic, Links, Code)
  function formatInline(text: string): string {
    let formatted = text
      // Bold **text**
      .replace(/\*\*(.*?)\*\*/g, "<strong class='font-bold text-slate-900'>$1</strong>")
      // Italic *text*
      .replace(/\*(.*?)\*/g, "<em class='italic text-slate-800'>$1</em>")
      // Code `text`
      .replace(/`(.*?)`/g, "<code class='bg-slate-100 px-1 py-0.5 rounded text-[#E8400C] font-mono text-xs'>$1</code>")
      // Links [text](url)
      .replace(/\[(.*?)\]\((.*?)\)/g, "<a href='$2' target='_blank' class='text-[#E8400C] hover:underline font-bold'>$1</a>")
      // Bullet markers like ● or ○
      .replace(/^[●○]\s*/, "");

    // Check if line is a metadata key-value (e.g. Instructor: Dr. Arpit Rana) and style key
    const metaKeywords = [
      "Instructor:",
      "Prerequisites:",
      "Slot:",
      "Category:",
      "Course Credits:",
      "Lectures (1 x 3):",
      "Lab Session (1 x 2):",
      "TA contact info:",
      "Course Description:",
      "Suggested Books:",
      "Course Outcomes:"
    ];

    for (const key of metaKeywords) {
      if (formatted.startsWith(key)) {
        formatted = formatted.replace(key, `<span class="font-bold text-slate-800 tracking-tight">${key}</span>`);
        break;
      }
    }

    return formatted;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // 1. Table Detection
    if (line.startsWith("|")) {
      flushList(`table-pre-${i}`);
      inTable = true;
      const cells = line
        .split("|")
        .map((c) => c.trim())
        .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);

      const isSeparator = cells.every((cell) => /^:?-+:?$/.test(cell));

      if (isSeparator) {
        continue;
      }

      if (tableHeaders.length === 0 && tableRows.length === 0) {
        tableHeaders = cells;
      } else {
        tableRows.push(cells);
      }
      continue;
    } else if (inTable) {
      flushTable(`table-post-${i}`);
    }

    // 2. Headings
    if (line.startsWith("#")) {
      flushList(`heading-pre-${i}`);
      const match = line.match(/^(#{1,6})\s+(.*)$/);
      if (match) {
        const level = match[1].length;
        const text = match[2].trim().replace(/^[\u200b\s]+/, "");
        
        if (level === 1) {
          elements.push(
            <h1 key={i} className="text-xl sm:text-2xl font-black text-slate-900 border-b border-slate-200 pb-2 mt-6 mb-4 tracking-tight">
              {text}
            </h1>
          );
        } else if (level === 2) {
          elements.push(
            <h2 key={i} className="text-base sm:text-lg font-bold text-slate-900 mt-6 mb-3 tracking-tight flex items-center gap-2 border-l-4 border-[#E8400C] pl-2.5">
              {text}
            </h2>
          );
        } else if (level === 3) {
          elements.push(
            <h3 key={i} className="text-sm sm:text-base font-bold text-slate-900 mt-5 mb-2">
              {text}
            </h3>
          );
        } else {
          elements.push(
            <h4 key={i} className="text-xs sm:text-sm font-bold text-slate-500 mt-4 mb-1 uppercase tracking-wider">
              {text}
            </h4>
          );
        }
        continue;
      }
    }

    // 3. Lists Detection
    const bulletMatch = line.match(/^([●○*+-]|\d+\.)\s+(.*)$/);
    if (bulletMatch) {
      const marker = bulletMatch[1];
      const text = bulletMatch[2];
      const type = /^\d+\./.test(marker) ? "number" : "bullet";

      if (!inList || listType !== type) {
        flushList(`list-change-${i}`);
        inList = true;
        listType = type;
      }
      listItems.push(text);
      continue;
    }

    // Empty lines
    if (line === "") {
      flushList(`empty-${i}`);
      continue;
    }

    // 4. Regular Paragraphs
    if (inList) {
      listItems[listItems.length - 1] += " " + line;
    } else {
      elements.push(
        <p
          key={i}
          className="text-xs sm:text-sm text-slate-600 leading-relaxed mb-3 text-justify"
          dangerouslySetInnerHTML={{ __html: formatInline(line) }}
        />
      );
    }
  }

  // Flush remaining blocks
  flushList("final");
  flushTable("final");

  return <div className="space-y-1">{elements}</div>;
}
