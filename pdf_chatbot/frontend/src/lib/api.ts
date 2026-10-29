import { ProcessingStatus, ChatMessage } from "@/types/chat";
import { AnalysisCardData } from "@/types/analysis";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function generateRequestId(): string {
  return "req_" + Math.random().toString(36).substring(2, 10);
}

export interface DocumentSummary {
  id: string;
  filename: string;
  file_size_human: string;
  page_count: number;
  status: string;
  document_title: string;
  document_type: string;
  created_at: string;
  updated_at: string;
}

export async function listDocuments(limit: number = 30): Promise<DocumentSummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/documents?limit=${limit}`, {
    cache: "no-store",
    headers: { "X-Request-ID": generateRequestId() },
  });
  if (!res.ok) {
    throw new Error(`Failed to list documents: ${res.statusText}`);
  }
  return res.json();
}

export async function uploadDocument(file: File): Promise<ProcessingStatus> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: "POST",
    headers: { "X-Request-ID": generateRequestId() },
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Upload failed." }));
    throw new Error(errorData.detail || `Upload failed with HTTP ${res.status}`);
  }

  return res.json();
}

export async function getDocumentStatus(documentId: string): Promise<ProcessingStatus> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/status`, {
    cache: "no-store",
    headers: { "X-Request-ID": generateRequestId() },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch status: ${res.statusText}`);
  }
  return res.json();
}

export async function getDocumentAnalysis(documentId: string): Promise<AnalysisCardData> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/analysis`, {
    cache: "no-store",
    headers: { "X-Request-ID": generateRequestId() },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch analysis: ${res.statusText}`);
  }
  return res.json();
}

export async function getChatHistory(documentId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}/chat-history`, {
    cache: "no-store",
    headers: { "X-Request-ID": generateRequestId() },
  });
  if (!res.ok) {
    return [];
  }
  const data = await res.json();
  return (data.messages || []).map((m: any) => ({
    role: m.role,
    content: m.content,
    citations: m.citations || [],
    follow_up_suggestions: m.follow_up_suggestions || [],
  }));
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: "DELETE",
    headers: { "X-Request-ID": generateRequestId() },
  });
  if (!res.ok) {
    throw new Error(`Failed to delete document: ${res.statusText}`);
  }
}

export function getPageImageUrl(documentId: string, pageNumber: number): string {
  return `${API_BASE_URL}/api/documents/${documentId}/pages/${pageNumber}`;
}

export function getOriginalPdfUrl(documentId: string): string {
  return `${API_BASE_URL}/api/documents/${documentId}/file`;
}

export function streamChatResponse(
  documentId: string,
  question: string,
  history: ChatMessage[],
  callbacks: {
    onToken: (token: string) => void;
    onSources: (sources: any[]) => void;
    onFollowUps: (followUps: string[]) => void;
    onDone: () => void;
    onError: (err: Error) => void;
  }
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          "X-Request-ID": generateRequestId(),
        },
        body: JSON.stringify({
          document_id: documentId,
          question,
          conversation_history: history.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Chat API error: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No readable response body received.");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "message";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          if (trimmed.startsWith("event:")) {
            currentEvent = trimmed.slice(6).trim();
          } else if (trimmed.startsWith("data:")) {
            const dataStr = trimmed.slice(5).trim();

            if (currentEvent === "token") {
              callbacks.onToken(dataStr);
            } else if (currentEvent === "sources") {
              try {
                callbacks.onSources(JSON.parse(dataStr));
              } catch {
                // Ignore parse errors on raw tokens
              }
            } else if (currentEvent === "follow_ups") {
              try {
                callbacks.onFollowUps(JSON.parse(dataStr));
              } catch {
                // Ignore
              }
            } else if (currentEvent === "done") {
              callbacks.onDone();
            } else if (currentEvent === "error") {
              callbacks.onError(new Error(dataStr));
            }
          }
        }
      }

      callbacks.onDone();
    } catch (err: any) {
      if (err.name !== "AbortError") {
        callbacks.onError(err);
      }
    }
  })();

  return () => {
    controller.abort();
  };
}
