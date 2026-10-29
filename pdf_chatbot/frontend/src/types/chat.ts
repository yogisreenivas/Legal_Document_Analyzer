import { AnalysisCardData } from "./analysis";

export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface Citation {
  page_number: number;
  label: string;
  snippet: string;
  bounding_box?: BoundingBox;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  follow_up_suggestions?: string[];
  timestamp: number;
}

export interface ProcessingStatus {
  document_id: string;
  status: "uploading" | "extracting" | "running_ocr" | "indexing" | "analyzing" | "ready" | "failed";
  progress_percentage: number;
  current_step_message: string;
  error?: string;
  analysis?: AnalysisCardData;
}
