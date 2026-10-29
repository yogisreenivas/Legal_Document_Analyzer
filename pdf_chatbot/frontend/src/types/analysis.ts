export interface DocumentMetadata {
  document_id: string;
  filename: string;
  file_size_bytes: number;
  file_size_human: string;
  page_count: number;
  language: string;
  document_title: string;
  document_type: string;
}

export interface KeyPoint {
  point: string;
  category?: string;
}

export interface OutlineItem {
  title: string;
  page_number: number;
  level: number;
}

export interface EntityItem {
  name: string;
  category: "Person" | "Organization" | "Date" | "Financial Amount" | "Location" | "Legal Reference" | "Other";
  context_page?: number;
}

export interface DetectedTable {
  table_id: string;
  page_number: number;
  caption?: string;
  headers: string[];
  rows: string[][];
}

export interface DetectedImage {
  image_id: string;
  page_number: number;
  caption: string;
  thumbnail_url?: string;
}

export interface DocumentQuality {
  is_scanned: boolean;
  ocr_applied: boolean;
  confidence_score: number;
  quality_notes: string[];
}

export interface AnalysisCardData {
  metadata: DocumentMetadata;
  executive_summary: string;
  key_points: KeyPoint[];
  outline: OutlineItem[];
  entities: EntityItem[];
  tables: DetectedTable[];
  charts_images: DetectedImage[];
  quality: DocumentQuality;
}
