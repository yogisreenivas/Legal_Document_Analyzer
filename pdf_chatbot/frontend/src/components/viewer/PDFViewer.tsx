"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Grid,
  Loader2,
  RotateCw,
  Expand,
} from "lucide-react";
import { getPageImageUrl } from "@/lib/api";
import { BoundingBox } from "@/types/chat";

interface PDFViewerProps {
  documentId: string;
  pageCount: number;
  currentPage: number;
  onPageChange: (page: number) => void;
  highlightBox?: BoundingBox | null;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  documentId,
  pageCount,
  currentPage,
  onPageChange,
  highlightBox,
}) => {
  const [zoom, setZoom] = useState<number>(100);
  const [rotation, setRotation] = useState<number>(0);
  const [showThumbnails, setShowThumbnails] = useState<boolean>(false);
  const [pageInput, setPageInput] = useState<string>(String(currentPage));
  const [isLoadingImage, setIsLoadingImage] = useState<boolean>(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setPageInput(String(currentPage));
    setIsLoadingImage(true);
  }, [currentPage]);

  // Keyboard navigation for page switching
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is typing in an input or textarea
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) return;
      if (e.key === "ArrowLeft" && currentPage > 1) {
        onPageChange(currentPage - 1);
      } else if (e.key === "ArrowRight" && currentPage < pageCount) {
        onPageChange(currentPage + 1);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentPage, pageCount, onPageChange]);

  const handlePrevPage = () => {
    if (currentPage > 1) onPageChange(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < pageCount) onPageChange(currentPage + 1);
  };

  const handlePageInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const p = parseInt(pageInput, 10);
    if (!isNaN(p) && p >= 1 && p <= pageCount) {
      onPageChange(p);
    } else {
      setPageInput(String(currentPage));
    }
  };

  const handleRotate = () => {
    setRotation((prev) => (prev + 90) % 360);
  };

  const handleToggleFullscreen = () => {
    if (!document.fullscreenElement) {
      rootRef.current?.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  return (
    <div
      ref={rootRef}
      className="flex flex-col h-full bg-slate-100 dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 select-none overflow-hidden"
    >
      {/* Top Controls Toolbar */}
      <div className="h-12 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-3 flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setShowThumbnails(!showThumbnails)}
            title="Toggle Thumbnails"
            className={`p-1.5 rounded-md text-xs flex items-center space-x-1 ${
              showThumbnails
                ? "bg-indigo-100 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Grid className="w-4 h-4" />
          </button>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 mx-1" />

          {/* Page Navigation */}
          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
            title="Previous Page (Left Arrow)"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <form onSubmit={handlePageInputSubmit} className="flex items-center space-x-1 text-xs">
            <input
              type="text"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              className="w-10 text-center py-1 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <span className="text-slate-400">/ {pageCount}</span>
          </form>

          <button
            onClick={handleNextPage}
            disabled={currentPage >= pageCount}
            title="Next Page (Right Arrow)"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Zoom & View Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setZoom((z) => Math.max(40, z - 15))}
            title="Zoom Out"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400 w-12 text-center">
            {zoom}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(220, z + 15))}
            title="Zoom In"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 mx-1" />

          {/* Rotate */}
          <button
            onClick={handleRotate}
            title="Rotate 90° Clockwise"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>

          {/* Reset Zoom */}
          <button
            onClick={() => { setZoom(100); setRotation(0); }}
            title="Reset Zoom & Orientation"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={handleToggleFullscreen}
            title="Toggle Fullscreen"
            className="p-1.5 rounded-md text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <Expand className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main View Area: Thumbnails Drawer + Canvas */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Thumbnails Sidebar */}
        {showThumbnails && (
          <div className="w-36 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 overflow-y-auto p-2 space-y-3 shrink-0 z-10 transition-all">
            {Array.from({ length: pageCount }).map((_, idx) => {
              const pNum = idx + 1;
              const isSelected = pNum === currentPage;
              return (
                <div
                  key={pNum}
                  onClick={() => onPageChange(pNum)}
                  className={`cursor-pointer rounded-lg overflow-hidden border-2 transition ${
                    isSelected
                      ? "border-indigo-600 shadow-md ring-2 ring-indigo-500/20"
                      : "border-slate-200 dark:border-slate-700 hover:border-slate-400 opacity-70 hover:opacity-100"
                  }`}
                >
                  <img
                    src={getPageImageUrl(documentId, pNum)}
                    alt={`Thumbnail Page ${pNum}`}
                    loading="lazy"
                    className="w-full h-auto object-cover bg-white"
                  />
                  <div className="text-[10px] text-center font-medium py-1 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    Page {pNum}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Primary Page Canvas */}
        <div
          ref={containerRef}
          className="flex-1 overflow-auto flex items-start justify-center p-6 relative bg-slate-200/50 dark:bg-slate-950/70"
        >
          <div
            className="relative shadow-2xl rounded-sm transition-all duration-150"
            style={{
              width: `${zoom}%`,
              maxWidth: "960px",
              transform: `rotate(${rotation}deg)`,
              transformOrigin: "center center",
            }}
          >
            {isLoadingImage && (
              <div className="absolute inset-0 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xs flex items-center justify-center z-10 rounded-sm">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
              </div>
            )}

            <img
              src={getPageImageUrl(documentId, currentPage)}
              alt={`Page ${currentPage}`}
              onLoad={() => setIsLoadingImage(false)}
              className="w-full h-auto bg-white dark:bg-slate-900 block rounded-sm pointer-events-auto"
            />

            {/* Bounding Box Citation Highlight Overlay */}
            {highlightBox && (
              <div
                className="absolute border-2 border-amber-500 bg-amber-400/25 rounded transition-all duration-300 pointer-events-none animate-pulse"
                style={{
                  left: `${highlightBox.x0 * 100}%`,
                  top: `${highlightBox.y0 * 100}%`,
                  width: `${(highlightBox.x1 - highlightBox.x0) * 100}%`,
                  height: `${(highlightBox.y1 - highlightBox.y0) * 100}%`,
                  boxShadow: "0 0 18px rgba(245, 158, 11, 0.6)",
                }}
              >
                <div className="absolute -top-5 left-0 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow">
                  Source Citation [p. {currentPage}]
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
