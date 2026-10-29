"use client";

import React from "react";
import { CheckCircle2, Loader2, AlertCircle, FileText, Layers, Brain, Database, ShieldCheck } from "lucide-react";
import { ProcessingStatus } from "@/types/chat";

interface ProcessingTimelineProps {
  status: ProcessingStatus;
}

const STEPS = [
  { key: "uploading", label: "Upload & File Security", icon: ShieldCheck },
  { key: "extracting", label: "Page Text & Coordinate Extraction", icon: FileText },
  { key: "running_ocr", label: "OCR Scan Verification", icon: Layers },
  { key: "indexing", label: "Page-Aware Chunking & Chroma Indexing", icon: Database },
  { key: "analyzing", label: "LLM Stage 1 Document Intelligence", icon: Brain },
];

export const ProcessingTimeline: React.FC<ProcessingTimelineProps> = ({ status }) => {
  const getStepStatus = (stepKey: string) => {
    const stepOrder = ["uploading", "extracting", "running_ocr", "indexing", "analyzing", "ready"];
    const currentIdx = stepOrder.indexOf(status.status);
    const stepIdx = stepOrder.indexOf(stepKey);

    if (status.status === "failed") return "error";
    if (currentIdx > stepIdx || status.status === "ready") return "completed";
    if (currentIdx === stepIdx) return "active";
    return "pending";
  };

  return (
    <div className="w-full max-w-xl mx-auto p-6 bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Processing Document Pipeline
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          {status.current_step_message || "Ingesting and indexing document..."}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden mb-8">
        <div
          className="bg-indigo-600 h-full transition-all duration-500 ease-out"
          style={{ width: `${Math.min(100, Math.max(5, status.progress_percentage))}%` }}
        />
      </div>

      {/* Step items */}
      <div className="space-y-4">
        {STEPS.map((step) => {
          const stepStatus = getStepStatus(step.key);
          const Icon = step.icon;

          return (
            <div
              key={step.key}
              className={`flex items-center space-x-3 text-sm p-2 rounded-lg transition-colors ${
                stepStatus === "active"
                  ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 font-medium"
                  : stepStatus === "completed"
                  ? "text-slate-700 dark:text-slate-300"
                  : "text-slate-400 dark:text-slate-600"
              }`}
            >
              <div className="w-6 h-6 flex items-center justify-center shrink-0">
                {stepStatus === "completed" && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                )}
                {stepStatus === "active" && (
                  <Loader2 className="w-5 h-5 text-indigo-600 dark:text-indigo-400 animate-spin" />
                )}
                {stepStatus === "pending" && (
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
                )}
                {stepStatus === "error" && (
                  <AlertCircle className="w-5 h-5 text-rose-500" />
                )}
              </div>

              <span className="flex-1 text-xs md:text-sm">{step.label}</span>

              {stepStatus === "active" && (
                <span className="text-xs bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-full">
                  Running...
                </span>
              )}
            </div>
          );
        })}
      </div>

      {status.status === "failed" && (
        <div className="mt-6 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-lg text-rose-700 dark:text-rose-300 text-xs text-center">
          {status.error || "Processing failed. Please check the document format and try again."}
        </div>
      )}
    </div>
  );
};
