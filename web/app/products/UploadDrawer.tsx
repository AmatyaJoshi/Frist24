"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { createProduct, uploadSbom } from "@/lib/api";
import { Spinner, btnGhost, btnPrimary, input } from "@/components/ui";

type P = { id: string; sku: string; name: string };
type Result = { ok: boolean; text: string; productId?: string; components?: number };

export default function UploadDrawer({ products }: { products: P[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"upload" | "create">(products.length ? "upload" : "create");
  const [productId, setProductId] = useState(products[0]?.id ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [sku, setSku] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<Result | null>(null);
  const [drag, setDrag] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  function pick(f: File | null) {
    setRes(null);
    if (!f) return setFile(null);
    if (!/\.json$/i.test(f.name)) return setRes({ ok: false, text: `"${f.name}" is not a .json file. Frist24 accepts CycloneDX JSON (1.2–1.6) or SPDX JSON (2.2/2.3).` });
    if (f.size > 25 * 1024 * 1024) return setRes({ ok: false, text: "File is larger than 25 MB." });
    setFile(f);
  }

  async function submit() {
    setBusy(true);
    setRes(null);
    try {
      if (mode === "create") {
        const p = await createProduct({ sku: sku.trim(), name: name.trim() });
        setRes({ ok: true, text: `Product ${p.sku} created. Now upload its SBOM.`, productId: p.id });
        setProductId(p.id);
        setMode("upload");
        setSku("");
        setName("");
      } else {
        if (!file || !productId) throw new Error("Choose a product and a file first.");
        const r = await uploadSbom(productId, file);
        setRes({
          ok: true,
          text: r.created ? `${r.sbom.component_count} components parsed from ${r.sbom.format} ${r.sbom.spec_version ?? ""}. They are matched on the next sync.` : r.message,
          productId,
          components: r.sbom.component_count,
        });
        setFile(null);
        if (fileInput.current) fileInput.current.value = "";
      }
      router.refresh();
    } catch (e) {
      setRes({ ok: false, text: e instanceof Error ? e.message : String(e) });
    } finally {
      setBusy(false);
    }
  }

  const canSubmit = mode === "upload" ? !!file && !!productId : sku.trim().length > 0 && name.trim().length > 0;

  return (
    <>
      <button type="button" className={btnPrimary} onClick={() => setOpen(true)}>
        Upload SBOM
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-[2px]" onClick={() => setOpen(false)} role="dialog" aria-modal="true">
          <aside className="anim-slide-in h-full w-full max-w-md overflow-y-auto border-l border-border bg-surface p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">{mode === "upload" ? "Upload SBOM" : "New Product"}</h2>
              <button type="button" className="rounded-md px-2 py-1 text-muted hover:bg-surface-2 hover:text-fg" onClick={() => setOpen(false)} aria-label="Close">✕</button>
            </div>
            <div className="mb-5 flex gap-2 text-xs">
              <button type="button" className={`${btnGhost} ${mode === "upload" ? "bg-surface-3 border-border-strong" : ""}`} onClick={() => setMode("upload")} disabled={!products.length && !res?.productId}>Existing SKU</button>
              <button type="button" className={`${btnGhost} ${mode === "create" ? "bg-surface-3 border-border-strong" : ""}`} onClick={() => setMode("create")}>New Product</button>
            </div>

            {mode === "upload" ? (
              <div className="space-y-4">
                <label className="block text-sm">
                  <span className="text-muted">Product</span>
                  <select className={`${input} mt-1`} value={productId} onChange={(e) => setProductId(e.target.value)}>
                    {products.length === 0 && <option value="">— create a product first —</option>}
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>
                    ))}
                  </select>
                </label>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                  onDragLeave={() => setDrag(false)}
                  onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files?.[0] ?? null); }}
                  onClick={() => fileInput.current?.click()}
                  className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center text-sm transition-colors ${drag ? "border-accent bg-accent-soft" : "border-border hover:bg-surface-2"}`}
                >
                  <input ref={fileInput} type="file" accept=".json,application/json" className="hidden" onChange={(e) => pick(e.target.files?.[0] ?? null)} />
                  {file ? (
                    <>
                      <div className="font-medium">{file.name}</div>
                      <div className="text-xs text-faint">{(file.size / 1024).toFixed(0)} KB · click to change</div>
                    </>
                  ) : (
                    <>
                      <div className="font-medium">Drop an SBOM here or click to browse</div>
                      <div className="text-xs text-faint">CycloneDX JSON 1.2–1.6 or SPDX JSON 2.2/2.3 · max 25 MB</div>
                    </>
                  )}
                </div>
                <p className="text-xs text-faint">Parsed on your API container. Components are matched by PURL on the next sync.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <label className="block text-sm">
                  <span className="text-muted">SKU</span>
                  <input className={`${input} mt-1 font-mono`} value={sku} onChange={(e) => setSku(e.target.value)} placeholder="CTRL-9000" />
                </label>
                <label className="block text-sm">
                  <span className="text-muted">Name</span>
                  <input className={`${input} mt-1`} value={name} onChange={(e) => setName(e.target.value)} placeholder="CTRL-9000 Machine Controller" />
                </label>
              </div>
            )}

            {res && (
              <div className={`mt-4 rounded-md border px-3 py-2 text-sm ${res.ok ? "border-ok bg-ok-soft text-ok" : "border-danger bg-danger-soft text-danger"}`}>
                {res.text}
                {res.ok && res.productId && res.components != null && (
                  <div className="mt-1"><Link href={`/products/${res.productId}`} className="underline">Open product</Link></div>
                )}
              </div>
            )}

            <div className="mt-6 flex gap-2">
              <button type="button" className={btnPrimary} disabled={busy || !canSubmit} onClick={submit}>
                {busy ? <><Spinner /> {mode === "upload" ? "Uploading & parsing…" : "Creating…"}</> : mode === "upload" ? "Upload & Parse" : "Create Product"}
              </button>
              <button type="button" className={btnGhost} onClick={() => setOpen(false)}>Close</button>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
