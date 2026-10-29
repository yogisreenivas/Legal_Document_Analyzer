"use client";

import React, { useState } from "react";
import {
  FileText,
  Bookmark,
  CheckCircle,
  Tag,
  Table as TableIcon,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { AnalysisCardData } from "@/types/analysis";

interface AnalysisCardProps {
  analysis: AnalysisCardData;
  onJumpToPage: (page: number) => void;
  onStartChat: (initialQuery?: string) => void;
}

export const AnalysisCard: React.FC<AnalysisCardProps> = ({
  analysis,
  onJumpToPage,
  onStartChat,
}) => {
  const [copied, setCopied] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    summary: true,
    keyPoints: true,
    outline: true,
    entities: true,
    tables: true,
    quality: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const copyAnalysis = () => {
    navigator.clipboard.writeText(JSON.stringify(analysis, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const { metadata, executive_summary, key_points, outline, entities, tables, quality } = analysis;

  return (
    <div className="space-y-5 pb-8">
      {/* Stage 1 Top Header Badge */}
      <div className="bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-700 rounded-2xl p-5 text-white shadow-lg shadow-indigo-500/10">
        <div className="flex items-start justify-between">
          <div>
            <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-white/20 text-white text-[11px] font-medium backdrop-blur-xs mb-2">
              <Sparkles className="w-3 h-3" />
              <span>Stage 1: Document Intelligence Card</span>
            </div>
            <h2 className="text-xl font-bold leading-tight">
              {metadata.document_title || metadata.filename}
            </h2>
            <div className="flex flex-wrap items-center gap-2 mt-3 text-xs text-indigo-100">
              <span className="bg-white/15 px-2.5 py-1 rounded-md font-medium">
                {metadata.document_type}
              </span>
              <span>•</span>
              <span>{metadata.page_count} Pages</span>
              <span>•</span>
              <span>{metadata.file_size_human}</span>
              <span>•</span>
              <span>{metadata.language}</span>
            </div>
          </div>

          <button
            onClick={copyAnalysis}
            title="Copy Analysis JSON"
            className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition text-xs flex items-center space-x-1"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* 1. Executive Summary */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
        <div
          onClick={() => toggleSection("summary")}
          className="flex items-center justify-between cursor-pointer"
        >
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              Executive Summary
            </h3>
          </div>
          {expandedSections.summary ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>

        {expandedSections.summary && (
          <p className="mt-3 text-xs md:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
            {executive_summary}
          </p>
        )}
      </div>

      {/* 2. Key Points / Takeaways */}
      {key_points && key_points.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div
            onClick={() => toggleSection("keyPoints")}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-emerald-500" />
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Key Highlights & Findings ({key_points.length})
              </h3>
            </div>
            {expandedSections.keyPoints ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>

          {expandedSections.keyPoints && (
            <div className="mt-4 space-y-2.5">
              {key_points.map((kp, idx) => (
                <div
                  key={idx}
                  className="flex items-start space-x-2.5 text-xs md:text-sm text-slate-700 dark:text-slate-300"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2 shrink-0" />
                  <div className="flex-1">
                    {kp.category && (
                      <span className="inline-block text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 mr-2">
                        {kp.category}
                      </span>
                    )}
                    <span>{kp.point}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 3. Document Structure / Outline Navigation */}
      {outline && outline.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div
            onClick={() => toggleSection("outline")}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center space-x-2">
              <Bookmark className="w-4 h-4 text-blue-500" />
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Document Outline & Navigation ({outline.length})
              </h3>
            </div>
            {expandedSections.outline ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>

          {expandedSections.outline && (
            <div className="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
              {outline.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => onJumpToPage(item.page_number)}
                  className="py-2 px-1 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/60 rounded cursor-pointer group transition"
                  style={{ paddingLeft: `${Math.max(4, item.level * 10)}px` }}
                >
                  <span className="text-xs md:text-sm text-slate-700 dark:text-slate-300 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 font-medium">
                    {item.title}
                  </span>
                  <span className="text-[11px] text-slate-400 group-hover:text-indigo-500 flex items-center space-x-1 shrink-0 ml-2">
                    <span>Page {item.page_number}</span>
                    <ExternalLink className="w-3 h-3" />
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 4. Extracted Entities */}
      {entities && entities.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div
            onClick={() => toggleSection("entities")}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center space-x-2">
              <Tag className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Key Entities Detected ({entities.length})
              </h3>
            </div>
            {expandedSections.entities ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>

          {expandedSections.entities && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {entities.map((ent, idx) => (
                <span
                  key={idx}
                  onClick={() => ent.context_page && onJumpToPage(ent.context_page)}
                  className={`text-xs px-2.5 py-1 rounded-full border transition cursor-pointer flex items-center space-x-1 ${
                    ent.category === "Person"
                      ? "bg-purple-50 dark:bg-purple-950/40 border-purple-200 dark:border-purple-800 text-purple-700 dark:text-purple-300"
                      : ent.category === "Organization"
                      ? "bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300"
                      : ent.category === "Financial Amount"
                      ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300"
                      : ent.category === "Date"
                      ? "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300"
                      : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                  }`}
                >
                  <span className="font-medium">{ent.name}</span>
                  {ent.context_page && (
                    <span className="text-[10px] opacity-70">p.{ent.context_page}</span>
                  )}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 5. Detected Tabular Structures */}
      {tables && tables.length > 0 && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
          <div
            onClick={() => toggleSection("tables")}
            className="flex items-center justify-between cursor-pointer"
          >
            <div className="flex items-center space-x-2">
              <TableIcon className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                Detected Tables ({tables.length})
              </h3>
            </div>
            {expandedSections.tables ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </div>

          {expandedSections.tables && (
            <div className="mt-4 space-y-4">
              {tables.map((tbl) => (
                <div key={tbl.table_id} className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden">
                  <div className="bg-slate-50 dark:bg-slate-800/80 px-3 py-2 flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-300">
                    <span>{tbl.caption || `Table on Page ${tbl.page_number}`}</span>
                    <button
                      onClick={() => onJumpToPage(tbl.page_number)}
                      className="text-indigo-600 dark:text-indigo-400 hover:underline flex items-center space-x-1"
                    >
                      <span>Jump to Page {tbl.page_number}</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                  <div className="overflow-x-auto max-h-60 overflow-y-auto">
                    <table className="w-full text-left text-xs">
                      {tbl.headers.length > 0 && (
                        <thead className="bg-slate-100 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300 sticky top-0">
                          <tr>
                            {tbl.headers.map((h, i) => (
                              <th key={i} className="p-2 font-semibold border-b border-slate-200 dark:border-slate-800">
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                      )}
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {tbl.rows.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="p-2 text-slate-600 dark:text-slate-300">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 6. Document Quality & OCR Diagnostics */}
      {quality && (
        <div className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl p-4 text-xs">
          <div
            onClick={() => toggleSection("quality")}
            className="flex items-center justify-between cursor-pointer text-slate-600 dark:text-slate-400"
          >
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-indigo-500" />
              <span className="font-medium">Document Quality & OCR Audit</span>
            </div>
            {expandedSections.quality ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </div>

          {expandedSections.quality && (
            <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800 space-y-2 text-slate-500 dark:text-slate-400">
              <div className="flex items-center justify-between">
                <span>Extraction Confidence:</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {(quality.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Format Type:</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {quality.is_scanned ? "Scanned Raster PDF" : "Digital Vector PDF"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>OCR Pipeline:</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {quality.ocr_applied ? "Tesseract Fallback Invoked" : "Native Coordinate Extraction"}
                </span>
              </div>
              {quality.quality_notes.map((note, idx) => (
                <p key={idx} className="italic text-[11px] text-slate-400">
                  • {note}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stage 2 Call to Action Prompt */}
      <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 text-center">
        <h4 className="text-sm font-semibold text-indigo-900 dark:text-indigo-200 mb-1">
          Ready for Stage 2: Grounded Q&A
        </h4>
        <p className="text-xs text-indigo-700 dark:text-indigo-300 mb-3">
          Ask specific questions to retrieve exact clauses with page citations and highlights.
        </p>
        <button
          onClick={() => onStartChat()}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg shadow-sm transition"
        >
          Ask a Question Below ↓
        </button>
      </div>
    </div>
  );
};
