"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  FileText,
  Download,
  UploadCloud,
  Moon,
  Sun,
  Library,
  Clock,
  Trash2,
  ChevronDown,
  X,
  ExternalLink
} from "lucide-react";
import { DocumentMetadata } from "@/types/analysis";
import { listDocuments, deleteDocument, DocumentSummary } from "@/lib/api";

interface HeaderProps {
  metadata?: DocumentMetadata | null;
  activeDocumentId?: string | null;
  onNewUpload: () => void;
  onExport: () => void;
  onSelectDocument: (docId: string) => void;
  isDarkMode: boolean;
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  metadata,
  activeDocumentId,
  onNewUpload,
  onExport,
  onSelectDocument,
  isDarkMode,
  onToggleTheme,
}) => {
  const [showLibrary, setShowLibrary] = useState<boolean>(false);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowLibrary(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchDocs = async () => {
    try {
      setIsLoadingDocs(true);
      const docs = await listDocuments(20);
      setDocuments(docs);
    } catch (err) {
      console.error("Failed to load documents list:", err);
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const handleToggleLibrary = () => {
    if (!showLibrary) {
      fetchDocs();
    }
    setShowLibrary(!showLibrary);
  };

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this document from the library?")) {
      try {
        await deleteDocument(docId);
        setDocuments((prev) => prev.filter((d) => d.id !== docId));
        if (activeDocumentId === docId) {
          onNewUpload();
        }
      } catch (err) {
        alert("Failed to delete document.");
      }
    }
  };

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 flex items-center justify-between z-30 transition-colors relative">
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
          <FileText className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-900 dark:text-white text-base">
              DocIntel AI
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-medium border border-indigo-200/50 dark:border-indigo-800/50">
              Two-Stage RAG
            </span>
          </div>
          {metadata ? (
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-xs md:max-w-md font-medium">
              {metadata.document_title || metadata.filename}
            </p>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              High-Precision PDF Intelligence & Grounded Chat
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center space-x-2">
        {/* Document Library Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={handleToggleLibrary}
            className="flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition"
          >
            <Library className="w-3.5 h-3.5 text-indigo-500" />
            <span className="hidden sm:inline">Library</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showLibrary ? "rotate-180" : ""}`} />
          </button>

          {showLibrary && (
            <div className="absolute right-0 mt-2 w-80 md:w-96 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 p-2 z-50">
              <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                  Analyzed Documents
                </span>
                <button
                  onClick={() => setShowLibrary(false)}
                  className="p-1 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 py-1">
                {isLoadingDocs ? (
                  <div className="p-6 text-center text-xs text-slate-400">Loading library...</div>
                ) : documents.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400">
                    No documents analyzed yet. Upload a PDF to begin!
                  </div>
                ) : (
                  documents.map((doc) => {
                    const isActive = doc.id === activeDocumentId;
                    return (
                      <div
                        key={doc.id}
                        onClick={() => {
                          onSelectDocument(doc.id);
                          setShowLibrary(false);
                        }}
                        className={`p-2.5 rounded-lg text-left cursor-pointer transition flex items-center justify-between group ${
                          isActive
                            ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200"
                            : "hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300"
                        }`}
                      >
                        <div className="min-w-0 pr-2">
                          <h4 className="text-xs font-medium truncate">
                            {doc.document_title || doc.filename}
                          </h4>
                          <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-0.5">
                            <span>{doc.page_count} pgs</span>
                            <span>•</span>
                            <span>{doc.file_size_human}</span>
                            <span>•</span>
                            <span className="flex items-center">
                              <Clock className="w-2.5 h-2.5 mr-0.5" />
                              {new Date(doc.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-1 shrink-0">
                          {isActive && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-indigo-600 text-white font-medium rounded">
                              Active
                            </span>
                          )}
                          <button
                            onClick={(e) => handleDelete(e, doc.id)}
                            title="Delete Document"
                            className="p-1 text-slate-400 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        {metadata && (
          <>
            <div className="hidden lg:flex items-center space-x-2 text-xs bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300">
              <span>{metadata.page_count} pages</span>
              <span>•</span>
              <span>{metadata.file_size_human}</span>
            </div>

            <button
              onClick={onExport}
              title="Export Analysis & Chat as Markdown"
              className="flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Export Report</span>
            </button>
          </>
        )}

        <button
          onClick={onNewUpload}
          className="flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition"
        >
          <UploadCloud className="w-3.5 h-3.5" />
          <span>Upload PDF</span>
        </button>

        <button
          onClick={onToggleTheme}
          aria-label="Toggle theme"
          className="p-2 rounded-md text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
