// Server components call the API over the compose network (API_URL);
// the browser uses NEXT_PUBLIC_API_URL. Both default to localhost:8000.
export const API_URL =
  (typeof window === "undefined" ? process.env.API_URL : undefined) ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000";

export type Health = {
  status: string;
  service: string;
  version: string;
  db: string;
  ollama: { status: string; models: string[]; target: string };
};

export async function getHealth(): Promise<Health | null> {
  try {
    const r = await fetch(`${API_URL}/health`, { cache: "no-store" });
    if (!r.ok) return null;
    return (await r.json()) as Health;
  } catch {
    return null;
  }
}
