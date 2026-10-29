"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  StopCircle,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  Sparkles,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Bot,
  User,
  Trash2,
  Download,
  RotateCcw,
} from "lucide-react";
import { ChatMessage, Citation } from "@/types/chat";

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSendMessage: (query: string) => void;
  onStopGeneration: () => void;
  onCitationClick: (citation: Citation) => void;
  onClearChat?: () => void;
  onRegenerate?: () => void;
  activeCitation?: Citation | null;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isStreaming,
  onSendMessage,
  onStopGeneration,
  onCitationClick,
  onClearChat,
  onRegenerate,
  activeCitation,
}) => {
  const [inputText, setInputText] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<Record<string, "up" | "down">>({});
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText.trim());
    setInputText("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const copyMessage = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleExportChat = () => {
    if (messages.length === 0) return;
    let md = "# DocIntel AI - Conversation Transcript\n\n";
    messages.forEach((m) => {
      md += `### ${m.role === "user" ? "User" : "DocIntel AI Assistant"}\n\n${m.content}\n\n`;
      if (m.citations && m.citations.length > 0) {
        md += `*Sources Used: ${m.citations.map((c) => `[p. ${c.page_number}]`).join(", ")}*\n\n`;
      }
      md += "---\n\n";
    });
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat_transcript_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper to render text with clickable [p. X] citations and styled markdown callouts
  const renderMessageContent = (content: string, citations?: Citation[]) => {
    const parts = content.split(/(\[p\.\s*\d+\])/g);

    return parts.map((part, idx) => {
      const match = part.match(/\[p\.\s*(\d+)\]/);
      if (match) {
        const pageNum = parseInt(match[1], 10);
        const matchedCitation = citations?.find((c) => c.page_number === pageNum) || {
          page_number: pageNum,
          label: `[p. ${pageNum}]`,
          snippet: `Referenced on page ${pageNum}`,
          bounding_box: { x0: 0.1, y0: 0.1, x1: 0.9, y1: 0.4 },
        };

        const isCurrentlyActive = activeCitation?.page_number === pageNum;

        return (
          <button
            key={idx}
            type="button"
            onClick={() => onCitationClick(matchedCitation)}
            className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold mx-0.5 transition cursor-pointer ${
              isCurrentlyActive
                ? "bg-amber-500 text-white shadow-sm ring-2 ring-amber-400"
                : "bg-indigo-100 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-900 border border-indigo-200 dark:border-indigo-800"
            }`}
          >
            [p. {pageNum}]
          </button>
        );
      }
      return <span key={idx}>{part}</span>;
    });
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 overflow-hidden">
      {/* Top Chat Toolbar */}
      <div className="h-10 border-b border-slate-100 dark:border-slate-800 px-4 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 shrink-0">
        <div className="flex items-center space-x-2">
          <span className="font-medium text-slate-700 dark:text-slate-300">
            Stage 2: Grounded Q&A
          </span>
          {messages.length > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
              {messages.length} messages
            </span>
          )}
        </div>

        {messages.length > 0 && (
          <div className="flex items-center space-x-1">
            <button
              onClick={handleExportChat}
              title="Export Conversation (Markdown)"
              className="p-1.5 hover:text-slate-700 dark:hover:text-slate-200 rounded transition"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                title="Regenerate last response"
                disabled={isStreaming}
                className="p-1.5 hover:text-slate-700 dark:hover:text-slate-200 rounded transition disabled:opacity-30"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            )}
            {onClearChat && (
              <button
                onClick={onClearChat}
                title="Clear conversation"
                className="p-1.5 hover:text-rose-600 rounded transition"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 dark:text-slate-500">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-3">
              <Bot className="w-6 h-6 text-indigo-500" />
            </div>
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              Ask Anything About This Document
            </h4>
            <p className="text-xs max-w-sm mt-1">
              Ask about terms, obligations, financial metrics, or key clauses. Every claim is strictly grounded with interactive page citations.
            </p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={msg.id || idx}
              className={`flex flex-col space-y-2 ${
                msg.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`flex space-x-2 max-w-[90%] md:max-w-[85%] ${
                  msg.role === "user" ? "flex-row-reverse space-x-reverse" : "flex-row"
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-white text-xs ${
                    msg.role === "user" ? "bg-indigo-600" : "bg-purple-600"
                  }`}
                >
                  {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble */}
                <div
                  className={`p-3.5 rounded-2xl text-xs md:text-sm leading-relaxed shadow-xs ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-tr-xs"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tl-xs border border-slate-200/60 dark:border-slate-700/60"
                  }`}
                >
                  <div className="whitespace-pre-wrap">
                    {msg.role === "assistant"
                      ? renderMessageContent(msg.content, msg.citations)
                      : msg.content}
                    {isStreaming && msg.role === "assistant" && msg.id === messages[messages.length - 1]?.id && (
                      <span className="inline-block w-1.5 h-3.5 bg-indigo-500 ml-1 animate-pulse" />
                    )}
                  </div>
                </div>
              </div>

              {/* Assistant Message Actions & Sources */}
              {msg.role === "assistant" && (
                <div className="pl-9 space-y-2 w-full max-w-[90%] md:max-w-[85%]">
                  {/* Sources Used Drawer */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 rounded-lg p-2.5 text-xs">
                      <div
                        onClick={() => toggleSources(msg.id)}
                        className="flex items-center justify-between cursor-pointer font-medium text-slate-600 dark:text-slate-300"
                      >
                        <div className="flex items-center space-x-1.5">
                          <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
                          <span>Sources Used ({msg.citations.length} references)</span>
                        </div>
                        {expandedSources[msg.id] ? (
                          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                        )}
                      </div>

                      {expandedSources[msg.id] && (
                        <div className="mt-2.5 pt-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
                          {msg.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              onClick={() => onCitationClick(cite)}
                              className="p-1.5 rounded hover:bg-white dark:hover:bg-slate-800 cursor-pointer transition border border-transparent hover:border-slate-200 dark:hover:border-slate-700"
                            >
                              <div className="font-semibold text-indigo-600 dark:text-indigo-400 flex items-center justify-between mb-0.5">
                                <span>Page {cite.page_number}</span>
                                <span className="text-[10px] text-slate-400">Click to view highlight</span>
                              </div>
                              <p className="text-[11px] text-slate-600 dark:text-slate-400 italic line-clamp-2">
                                "{cite.snippet}"
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Message Action Buttons */}
                  <div className="flex items-center space-x-2 text-slate-400 text-xs">
                    <button
                      onClick={() => copyMessage(msg.id, msg.content)}
                      className="p-1 hover:text-slate-600 dark:hover:text-slate-200 rounded transition"
                      title="Copy Answer"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-500" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                    <button
                      onClick={() =>
                        setFeedbackState((prev) => ({
                          ...prev,
                          [msg.id]: prev[msg.id] === "up" ? undefined! : "up",
                        }))
                      }
                      className={`p-1 hover:text-slate-600 dark:hover:text-slate-200 rounded transition ${
                        feedbackState[msg.id] === "up" ? "text-emerald-500" : ""
                      }`}
                      title="Helpful"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() =>
                        setFeedbackState((prev) => ({
                          ...prev,
                          [msg.id]: prev[msg.id] === "down" ? undefined! : "down",
                        }))
                      }
                      className={`p-1 hover:text-slate-600 dark:hover:text-slate-200 rounded transition ${
                        feedbackState[msg.id] === "down" ? "text-rose-500" : ""
                      }`}
                      title="Not helpful"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* 3 Suggested Follow-Up Questions */}
                  {msg.follow_up_suggestions && msg.follow_up_suggestions.length > 0 && (
                    <div className="pt-2 space-y-1.5">
                      <div className="flex items-center space-x-1 text-[11px] font-medium text-slate-400">
                        <Sparkles className="w-3 h-3 text-indigo-400" />
                        <span>Suggested follow-up questions:</span>
                      </div>
                      <div className="flex flex-col space-y-1">
                        {msg.follow_up_suggestions.map((q, qIdx) => (
                          <button
                            key={qIdx}
                            onClick={() => onSendMessage(q)}
                            disabled={isStreaming}
                            className="text-left text-xs px-2.5 py-1.5 rounded-lg bg-indigo-50/70 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900 border border-indigo-200/50 dark:border-indigo-800/50 transition disabled:opacity-50"
                          >
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box Area */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50 backdrop-blur-xs">
        <form onSubmit={handleSubmit} className="relative flex items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about this document..."
            disabled={isStreaming}
            className="w-full resize-none py-2.5 pl-3.5 pr-20 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-xs md:text-sm rounded-xl border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-h-32 disabled:opacity-50"
          />

          <div className="absolute right-2 bottom-1.5 flex items-center space-x-1">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStopGeneration}
                title="Stop generation"
                className="p-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white transition shadow-sm"
              >
                <StopCircle className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!inputText.trim()}
                title="Send query"
                className="p-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white transition shadow-sm"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </form>
        <p className="text-[10px] text-center text-slate-400 mt-1.5">
          Grounded Document Intelligence • Claims are paired with exact page citations
        </p>
      </div>
    </div>
  );
};
