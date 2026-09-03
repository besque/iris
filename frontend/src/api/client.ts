import { buildReportJson, mockQuery, mockUpload, triggerDownload } from "./mock";
import type { QueryResponse, ReportPayload, UploadResponse, ValidationResult } from "./types";

const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error((await res.text()) || `Request failed (${res.status})`);
  return res.json() as Promise<T>;
}

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  if (USE_MOCK || files.length === 0) return mockUpload(files);

  const body = new FormData();
  files.forEach((file, i) => body.append(`file_${i}`, file));
  return parseJson<UploadResponse>(
    await fetch(`${API_BASE}/upload`, { method: "POST", body }),
  );
}

export async function runQuery(
  sessionId: string,
  query: string,
  validation: ValidationResult,
): Promise<QueryResponse> {
  if (USE_MOCK) return mockQuery(query, validation);

  return parseJson<QueryResponse>(
    await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, query }),
    }),
  );
}

export async function downloadReport(payload: ReportPayload): Promise<void> {
  let blob = buildReportJson(payload);

  if (!USE_MOCK) {
    try {
      const res = await fetch(`${API_BASE}/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) blob = await res.blob();
    } catch {
      /* fall back to local JSON */
    }
  }

  triggerDownload(blob, `iridis-report-${Date.now()}.json`);
}

export const isMockMode = USE_MOCK;
