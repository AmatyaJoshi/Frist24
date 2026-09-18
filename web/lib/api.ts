import type {
  AuditEvent,
  Component,
  FeedSync,
  Health,
  IncidentDetail,
  IncidentListItem,
  Product,
  Report,
} from "./types";

// Server components call the API over the compose network (API_URL);
// the browser uses NEXT_PUBLIC_API_URL. Both default to localhost:8000.
export const API_URL =
  (typeof window === "undefined" ? process.env.API_URL : undefined) ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("X-Actor")) headers.set("X-Actor", "reviewer");
  if (init?.body && typeof init.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const r = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const j = await r.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail ?? j);
    } catch {
      /* ignore */
    }
    throw new ApiError(r.status, detail);
  }
  return (await r.json()) as T;
}

export async function getHealth(): Promise<Health | null> {
  try {
    return await request<Health>("/health");
  } catch {
    return null;
  }
}

// --- products
export const getProducts = () => request<Product[]>("/products");
export const getProduct = (id: string) => request<Product>(`/products/${id}`);
export const getComponents = (id: string, q?: string, limit = 200) =>
  request<Component[]>(`/products/${id}/components?limit=${limit}${q ? `&q=${encodeURIComponent(q)}` : ""}`);
export const createProduct = (body: { sku: string; name: string; description?: string; lifecycle_status?: string }) =>
  request<Product>("/products", { method: "POST", body: JSON.stringify(body) });
export async function uploadSbom(productId: string, file: File) {
  const fd = new FormData();
  fd.append("file", file, file.name);
  return request<{ sbom: Product["sboms"][number]; created: boolean; message: string }>(`/products/${productId}/sbom`, {
    method: "POST",
    body: fd,
  });
}

// --- sync
export const runSync = () => request<Record<string, unknown>>("/sync", { method: "POST" });
export const getSyncStatus = () => request<FeedSync[]>("/sync/status");

// --- incidents & reports
export const getIncidents = () => request<IncidentListItem[]>("/incidents");
export const getIncident = (id: string) => request<IncidentDetail>(`/incidents/${id}`);
export const createTemplateDraft = (incidentId: string, stage: string, language: string) =>
  request<Report>(`/incidents/${incidentId}/reports/template?stage=${stage}&language=${language}`, { method: "POST" });
export const draftWithLlm = (incidentId: string, stage: string, language: string) =>
  request<Report>(`/draft/${stage}?incident_id=${incidentId}&language=${language}`, { method: "POST" });
export const editReport = (id: string, content: Record<string, unknown>, note?: string) =>
  request<Report>(`/reports/${id}`, { method: "PATCH", body: JSON.stringify({ content, note }) });
export const approveReport = (id: string, note?: string) =>
  request<Report>(`/reports/${id}/approve`, { method: "POST", body: JSON.stringify({ note }) });
export const rejectReport = (id: string, note?: string) =>
  request<Report>(`/reports/${id}/reject`, { method: "POST", body: JSON.stringify({ note }) });

// --- audit
export const getAudit = (limit = 200, offset = 0) =>
  request<{ total: number; items: AuditEvent[] }>(`/audit?limit=${limit}&offset=${offset}`);
export const verifyAudit = () =>
  request<{ ok: boolean; rows: number; first_bad_id: number | null; reason: string | null; head?: string }>("/audit/verify");
export const packageUrl = (incidentId: string) => `${API_URL}/incidents/${incidentId}/package`;
