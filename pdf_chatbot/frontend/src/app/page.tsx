"use client";

import React, { useState, useEffect, useRef } from "react";
import { Header } from "@/components/layout/Header";
import { Dropzone } from "@/components/upload/Dropzone";
import { ProcessingTimeline } from "@/components/upload/ProcessingTimeline";
import { PDFViewer } from "@/components/viewer/PDFViewer";
import { AnalysisCard } from "@/components/analysis/AnalysisCard";
import { ChatPanel } from "@/components/chat/ChatPanel";
import {
  uploadDocument,
  getDocumentStatus,
  getDocumentAnalysis,
  getChatHistory,
  streamChatResponse,
} from "@/lib/api";
import { exportDocumentAnalysisMarkdown } from "@/lib/utils";
import { AnalysisCardData } from "@/types/analysis";
import { ProcessingStatus, ChatMessage, Citation, BoundingBox } from "@/types/chat";
import { Sparkles, MessageSquare, AlertCircle } from "lucide-react";

export default function Home() {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisCardData | null>(null);

  // PDF Viewer State
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [highlightBox, setHighlightBox] = useState<BoundingBox | null>(null);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const abortChatRef = useRef<(() => void) | null>(null);

  // Navigation / Tabs (Stage 1 Analysis vs Stage 2 Chat)
  const [rightPanelTab, setRightPanelTab] = useState<"analysis" | "chat">("analysis");
  const [mobileTab, setMobileTab] = useState<"viewer" | "analysis" | "chat">("analysis");

  // Dark mode effect
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [isDarkMode]);

  // Restore active document from URL or LocalStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const docIdFromUrl = params.get("doc");
    const savedDocId = docIdFromUrl || localStorage.getItem("docintel_active_doc_id");

    if (savedDocId && savedDocId.length >= 4) {
      loadExistingDocument(savedDocId);
    }
  }, []);

  const syncUrlAndStorage = (docId: string | null) => {
    if (typeof window === "undefined") return;
    if (docId) {
      localStorage.setItem("docintel_active_doc_id", docId);
      const url = new URL(window.location.href);
      url.searchParams.set("doc", docId);
      window.history.replaceState({}, "", url.toString());
    } else {
      localStorage.removeItem("docintel_active_doc_id");
      const url = new URL(window.location.href);
      url.searchParams.delete("doc");
      window.history.replaceState({}, "", url.toString());
    }
  };

  const loadExistingDocument = async (id: string) => {
    try {
      setProcessingStatus({
        document_id: id,
        status: "uploading",
        progress_percentage: 60,
        current_step_message: "Loading saved document & intelligence...",
      });

      const status = await getDocumentStatus(id);
      if (status.status === "ready") {
        setDocumentId(id);
        setProcessingStatus(status);

        const analysis = await getDocumentAnalysis(id);
        setAnalysisData(analysis);

        const history = await getChatHistory(id);
        setMessages(history);

        setCurrentPage(1);
        setRightPanelTab("analysis");
        setMobileTab("analysis");
        syncUrlAndStorage(id);
      } else {
        setProcessingStatus(status);
      }
    } catch (err: any) {
      console.warn("Could not reload document:", err);
      syncUrlAndStorage(null);
      setDocumentId(null);
      setProcessingStatus(null);
    }
  };

  // Document upload handler
  const handleFileUpload = async (file: File) => {
    try {
      setProcessingStatus({
        document_id: "init",
        status: "uploading",
        progress_percentage: 10,
        current_step_message: "Uploading document...",
      });
      setAnalysisData(null);
      setMessages([]);
      setCurrentPage(1);

      const status = await uploadDocument(file);
      setDocumentId(status.document_id);
      setProcessingStatus(status);
      syncUrlAndStorage(status.document_id);

      // Poll pipeline status until ready
      const interval = setInterval(async () => {
        try {
          const current = await getDocumentStatus(status.document_id);
          setProcessingStatus(current);

          if (current.status === "ready") {
            clearInterval(interval);
            const analysis = await getDocumentAnalysis(status.document_id);
            setAnalysisData(analysis);
            setRightPanelTab("analysis");
            setMobileTab("analysis");
          } else if (current.status === "failed") {
            clearInterval(interval);
          }
        } catch {
          clearInterval(interval);
        }
      }, 1200);
    } catch (err: any) {
      setProcessingStatus({
        document_id: "error",
        status: "failed",
        progress_percentage: 0,
        current_step_message: "Upload failed.",
        error: err.message || "Failed to upload file.",
      });
    }
  };

  // Citation click handler: scrolls viewer and pulses highlight
  const handleCitationClick = (citation: Citation) => {
    setCurrentPage(citation.page_number);
    setActiveCitation(citation);
    setHighlightBox(citation.bounding_box || { x0: 0.1, y0: 0.1, x1: 0.9, y1: 0.3 });
    setMobileTab("viewer");

    // Clear highlight after 6 seconds
    setTimeout(() => {
      setHighlightBox(null);
    }, 6000);
  };

  // Jump to page from outline or entities
  const handleJumpToPage = (page: number) => {
    setCurrentPage(page);
    setMobileTab("viewer");
  };

  // Chat message send handler (Stage 2)
  const handleSendMessage = (query: string) => {
    if (!documentId || isStreaming) return;

    setRightPanelTab("chat");
    setMobileTab("chat");

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: query,
      timestamp: Date.now(),
    };

    const assistantMsgId = `asst_${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      citations: [],
      follow_up_suggestions: [],
      timestamp: Date.now(),
    };

    const newHistory = [...messages, userMsg];
    setMessages([...newHistory, initialAssistantMsg]);
    setIsStreaming(true);

    const abortFn = streamChatResponse(documentId, query, newHistory, {
      onToken: (token) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: m.content + token } : m
          )
        );
      },
      onSources: (sources) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, citations: sources } : m
          )
        );
      },
      onFollowUps: (followUps) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, follow_up_suggestions: followUps } : m
          )
        );
      },
      onDone: () => {
        setIsStreaming(false);
      },
      onError: (err) => {
        setIsStreaming(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: m.content + `\n\n[Error: ${err.message}]` }
              : m
          )
        );
      },
    });

    abortChatRef.current = abortFn;
  };

  const handleStopGeneration = () => {
    if (abortChatRef.current) {
      abortChatRef.current();
      setIsStreaming(false);
    }
  };

  const handleClearChat = () => {
    if (confirm("Are you sure you want to clear this conversation history?")) {
      setMessages([]);
    }
  };

  const handleRegenerate = () => {
    const lastUserMessage = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMessage) {
      handleSendMessage(lastUserMessage.content);
    }
  };

  // Export report to Markdown
  const handleExport = () => {
    if (!analysisData) return;
    const md = exportDocumentAnalysisMarkdown(analysisData, messages);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${analysisData.metadata.document_title || "analysis"}_report.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isDocumentReady = processingStatus?.status === "ready" && analysisData && documentId;

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        metadata={analysisData?.metadata}
        activeDocumentId={documentId}
        onSelectDocument={loadExistingDocument}
        onNewUpload={() => {
          syncUrlAndStorage(null);
          setDocumentId(null);
          setProcessingStatus(null);
          setAnalysisData(null);
          setMessages([]);
        }}
        onExport={handleExport}
        isDarkMode={isDarkMode}
        onToggleTheme={() => setIsDarkMode(!isDarkMode)}
      />

      {/* Main Container */}
      <main className="flex-1 overflow-hidden relative flex flex-col">
        {/* Upload / Ingestion Screen */}
        {!isDocumentReady && (
          <div className="flex-1 overflow-y-auto flex items-center justify-center p-6">
            {processingStatus && processingStatus.status !== "failed" ? (
              <ProcessingTimeline status={processingStatus} />
            ) : (
              <Dropzone
                onFileSelected={handleFileUpload}
                isLoading={processingStatus?.status === "uploading"}
              />
            )}
          </div>
        )}

        {/* Split Screen Layout (Ready State) */}
        {isDocumentReady && (
          <div className="flex-1 flex flex-col md:flex-row h-full overflow-hidden">
            {/* Mobile Tab Switcher */}
            <div className="md:hidden flex border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
              <button
                onClick={() => setMobileTab("viewer")}
                className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 ${
                  mobileTab === "viewer"
                    ? "border-indigo-600 text-indigo-600 font-semibold"
                    : "border-transparent text-slate-500"
                }`}
              >
                PDF Viewer [p. {currentPage}]
              </button>
              <button
                onClick={() => {
                  setMobileTab("analysis");
                  setRightPanelTab("analysis");
                }}
                className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 ${
                  mobileTab === "analysis"
                    ? "border-indigo-600 text-indigo-600 font-semibold"
                    : "border-transparent text-slate-500"
                }`}
              >
                Stage 1: Analysis
              </button>
              <button
                onClick={() => {
                  setMobileTab("chat");
                  setRightPanelTab("chat");
                }}
                className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 ${
                  mobileTab === "chat"
                    ? "border-indigo-600 text-indigo-600 font-semibold"
                    : "border-transparent text-slate-500"
                }`}
              >
                Stage 2: Chat
              </button>
            </div>

            {/* LEFT PANEL: Interactive PDF Viewer */}
            <div
              className={`flex-1 h-full md:block ${
                mobileTab === "viewer" ? "block" : "hidden md:block"
              }`}
            >
              <PDFViewer
                documentId={documentId}
                pageCount={analysisData.metadata.page_count}
                currentPage={currentPage}
                onPageChange={setCurrentPage}
                highlightBox={highlightBox}
              />
            </div>

            {/* RIGHT PANEL: Two-Stage Intelligence (Analysis Card or Chat) */}
            <div
              className={`w-full md:w-[480px] lg:w-[540px] xl:w-[600px] h-full flex flex-col border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 ${
                mobileTab !== "viewer" ? "block" : "hidden md:flex"
              }`}
            >
              {/* Desktop Sub-Tabs: Stage 1 Analysis vs Stage 2 Chat */}
              <div className="h-12 border-b border-slate-200 dark:border-slate-800 px-4 flex items-center justify-between bg-slate-50/70 dark:bg-slate-900/70 shrink-0">
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setRightPanelTab("analysis")}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                      rightPanelTab === "analysis"
                        ? "bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-xs border border-slate-200 dark:border-slate-700 font-semibold"
                        : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Stage 1: Analysis Card</span>
                  </button>

                  <button
                    onClick={() => setRightPanelTab("chat")}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition cursor-pointer ${
                      rightPanelTab === "chat"
                        ? "bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-xs border border-slate-200 dark:border-slate-700 font-semibold"
                        : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Stage 2: Chat & Q&A</span>
                    {messages.length > 0 && (
                      <span className="w-4 h-4 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-600 text-[10px] flex items-center justify-center font-bold">
                        {messages.filter((m) => m.role === "assistant").length}
                      </span>
                    )}
                  </button>
                </div>
              </div>

              {/* Panel Content */}
              <div className="flex-1 overflow-y-auto">
                {rightPanelTab === "analysis" ? (
                  <div className="p-4 md:p-6">
                    <AnalysisCard
                      analysis={analysisData}
                      onJumpToPage={handleJumpToPage}
                      onStartChat={(initialQuery) => {
                        setRightPanelTab("chat");
                        if (initialQuery) {
                          handleSendMessage(initialQuery);
                        }
                      }}
                    />
                  </div>
                ) : (
                  <ChatPanel
                    messages={messages}
                    isStreaming={isStreaming}
                    onSendMessage={handleSendMessage}
                    onStopGeneration={handleStopGeneration}
                    onCitationClick={handleCitationClick}
                    onClearChat={handleClearChat}
                    onRegenerate={handleRegenerate}
                    activeCitation={activeCitation}
                  />
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
