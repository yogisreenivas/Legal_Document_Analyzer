"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, FileText, Table, Image as ImageIcon, AlertCircle } from "lucide-react";

interface DropzoneProps {
  onFileSelected: (file: File) => void;
  isLoading: boolean;
}

export const Dropzone: React.FC<DropzoneProps> = ({ onFileSelected, isLoading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const validateAndProceed = (file: File) => {
    setErrorMessage(null);
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMessage("Only PDF files are supported.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage("File exceeds maximum size limit of 50 MB.");
      return;
    }
    onFileSelected(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProceed(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProceed(e.target.files[0]);
    }
  };

  // Quick-loader for synthetic sample files
  const loadSampleFile = async (sampleFilename: string) => {
    try {
      const response = await fetch(`/samples/${sampleFilename}`);
      if (!response.ok) {
        throw new Error("Sample file not found on static server.");
      }
      const blob = await response.blob();
      const file = new File([blob], sampleFilename, { type: "application/pdf" });
      onFileSelected(file);
    } catch {
      // If client cannot fetch from Next public dir, fetch from backend sample endpoint or create dummy
      setErrorMessage("Please select a local PDF file from your device.");
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Drag & Drop Card */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20 scale-[1.01]"
            : "border-slate-300 dark:border-slate-700 hover:border-indigo-400 bg-white/50 dark:bg-slate-900/50"
        } ${isLoading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={handleInputChange}
          disabled={isLoading}
        />

        <div className="w-14 h-14 rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 mx-auto flex items-center justify-center mb-4 shadow-sm">
          <UploadCloud className="w-7 h-7" />
        </div>

        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100 mb-1">
          Drop your PDF document here
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Supports native text, multi-column contracts, tables, and scanned receipts (up to 50MB)
        </p>

        <button
          type="button"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-medium shadow-md shadow-indigo-500/20 transition"
        >
          Browse Files
        </button>
      </div>

      {errorMessage && (
        <div className="flex items-center space-x-2 text-rose-600 dark:text-rose-400 text-xs bg-rose-50 dark:bg-rose-950/40 p-3 rounded-lg border border-rose-200 dark:border-rose-800">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Synthetic Demo Presets */}
      <div className="pt-2">
        <div className="text-center mb-3">
          <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500">
            Quick Test With Sample Documents
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div
            onClick={(e) => {
              e.stopPropagation();
              loadSampleFile("sample_text_contract.pdf");
            }}
            className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-indigo-400 cursor-pointer text-left transition shadow-sm group hover:shadow-md"
          >
            <div className="w-7 h-7 rounded-md bg-blue-100 dark:bg-blue-950/60 text-blue-600 flex items-center justify-center mb-2">
              <FileText className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600">
              1. Legal Contract
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
              Software Services Agreement with terms, liability, and notice provisions.
            </p>
          </div>

          <div
            onClick={(e) => {
              e.stopPropagation();
              loadSampleFile("sample_financial_tables.pdf");
            }}
            className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-indigo-400 cursor-pointer text-left transition shadow-sm group hover:shadow-md"
          >
            <div className="w-7 h-7 rounded-md bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center mb-2">
              <Table className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600">
              2. Financial Tables
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
              Quarterly performance report with segment revenue & balance sheet.
            </p>
          </div>

          <div
            onClick={(e) => {
              e.stopPropagation();
              loadSampleFile("sample_scanned_receipt.pdf");
            }}
            className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-indigo-400 cursor-pointer text-left transition shadow-sm group hover:shadow-md"
          >
            <div className="w-7 h-7 rounded-md bg-amber-100 dark:bg-amber-950/60 text-amber-600 flex items-center justify-center mb-2">
              <ImageIcon className="w-4 h-4" />
            </div>
            <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600">
              3. Scanned Invoice
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
              Raster invoice document demonstrating OCR fallback and quality audit.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
