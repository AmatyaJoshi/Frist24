"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createProduct, uploadSbom } from "@/lib/api";
import { btnGhost, btnPrimary } from "@/components/ui";

type P = { id: string; sku: string; name: string };

export default function UploadDrawer({ products }: { products: P[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"upload" | "create">("upload");
  const [productId, setProductId] = useState(products[0]?.id ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit() {
    setBusy(true);
    setMsg(null);
    try {
      if (mode === "create") {
        const p = await createProduct({ sku, name });
        setMsg({ ok: true, text: `Product ${p.sku} created.` });
        setProductId(p.id);
        setMode("upload");
      } else {
        if (!file || !productId) throw new Error("Pick a product and a file.");
        const r = await uploadSbom(productId, file);
        setMsg({ ok: true, text: r.message });
        setFile(null);
      }
      router.refresh();
    } catch (e) {
      setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button className={btnPrimary} onClick={() => setOpen(true)}>Upload SBOM</button>
      {open && (
        <div className="fixed inset-0 z-40 flex justify-end bg-black/60" onClick={() => setOpen(false)}>
          <aside className="h-full w-full max-w-md overflow-y-auto border-l border-border bg-surface p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{mode === "upload" ? "Upload SBOM" : "New product"}</h2>
              <button className="text-muted hover:text-fg" onClick={() => setOpen(false)}>✕</button>
            </div>
            <div className="flex gap-2 mb-5 text-xs">
              <button className={`${btnGhost} ${mode === "upload" ? "bg-surface-3" : ""}`} onClick={() => setMode("upload")}>Upload to existing SKU</button>
              <button className={`${btnGhost} ${mode === "create" ? "bg-surface-3" : ""}`} onClick={() => setMode("create")}>Create product</button>
            </div>

            {mode === "upload" ? (
              <div className="space-y-4">
                <label className="block text-sm">
                  <span className="text-muted">Product</span>
                  <select className="mt-1 w-full rounded border border-border bg-surface px-2 py-1.5" value={productId} onChange={(e) => setProductId(e.target.value)}>
                    {products.length === 0 && <option value="">— create a product first —</option>}
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>
                    ))}
                  </select>
                </label>
                <label className="block text-sm">
                  <span className="text-muted">SBOM file (CycloneDX JSON 1.2–1.6 or SPDX JSON 2.2/2.3)</span>
                  <input type="file" accept=".json,application/json" className="mt-1 block w-full text-sm" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                </label>
                <p className="text-xs text-faint">The file is parsed on your own API container. Components are matched by PURL on the next sync (or press “Sync now” on the Incidents page).</p>
              </div>
            ) : (
              <div className="space-y-4">
                <label className="block text-sm">
                  <span className="text-muted">SKU</span>
                  <input className="mt-1 w-full rounded border border-border bg-surface px-2 py-1.5 font-mono" value={sku} onChange={(e) => setSku(e.target.value)} placeholder="CTRL-9000" />
                </label>
                <label className="block text-sm">
                  <span className="text-muted">Name</span>
                  <input className="mt-1 w-full rounded border border-border bg-surface px-2 py-1.5" value={name} onChange={(e) => setName(e.target.value)} placeholder="CTRL-9000 Machine Controller" />
                </label>
              </div>
            )}

            {msg && <div className={`mt-4 rounded border px-3 py-2 text-sm ${msg.ok ? "border-ok bg-ok-soft text-ok" : "border-danger bg-danger-soft text-danger"}`}>{msg.text}</div>}

            <div className="mt-6 flex gap-2">
              <button className={btnPrimary} disabled={busy || (mode === "upload" ? !file || !productId : !sku || !name)} onClick={submit}>
                {busy ? "Working…" : mode === "upload" ? "Upload & parse" : "Create"}
              </button>
              <button className={btnGhost} onClick={() => setOpen(false)}>Close</button>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
