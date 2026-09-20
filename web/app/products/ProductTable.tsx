"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import Pager from "@/components/Pager";
import { Badge, Card, Empty, input } from "@/components/ui";
import { formatDate } from "@/lib/time";
import type { Product } from "@/lib/types";

export default function ProductTable({ rows }: { rows: Product[] }) {
  const [q, setQ] = useState("");
  const [only, setOnly] = useState<"all" | "incidents" | "active" | "discontinued">("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const filtered = useMemo(() => {
    const n = q.trim().toLowerCase();
    return rows.filter((p) => {
      if (only === "incidents" && p.open_incidents === 0) return false;
      if ((only === "active" || only === "discontinued") && p.lifecycle_status !== only) return false;
      return !n || p.sku.toLowerCase().includes(n) || p.name.toLowerCase().includes(n) || (p.description ?? "").toLowerCase().includes(n);
    });
  }, [rows, q, only]);
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const current = Math.min(page, pages);
  const slice = filtered.slice((current - 1) * pageSize, current * pageSize);

  const chip = (k: typeof only, label: string) => (
    <button key={k} onClick={() => { setOnly(k); setPage(1); }} className={`rounded-md border px-2 py-1 uppercase tracking-wide transition-colors ${only === k ? "border-border-strong bg-surface-3 text-fg" : "border-border bg-surface text-muted hover:text-fg"}`}>
      {label}
    </button>
  );

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <input className={`${input} max-w-xs`} placeholder="Search SKU or Name…" value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} aria-label="Search products" />
        {chip("all", "ALL")}
        {chip("incidents", "WITH OPEN INCIDENTS")}
        {chip("active", "ACTIVE")}
        {chip("discontinued", "DISCONTINUED")}
      </div>
      {filtered.length === 0 ? (
        <Empty title="No products match" />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-[11px] uppercase">
              <tr>
                <th className="px-4 py-2.5">SKU</th>
                <th className="px-4 py-2.5">Product</th>
                <th className="px-4 py-2.5">Lifecycle</th>
                <th className="px-4 py-2.5">On Market</th>
                <th className="px-4 py-2.5">SBOM</th>
                <th className="px-4 py-2.5 text-right">Components</th>
                <th className="px-4 py-2.5 text-right">Open Incidents</th>
              </tr>
            </thead>
            <tbody>
              {slice.map((p) => (
                <tr key={p.id} className="border-t border-border hover:bg-surface-2">
                  <td className="px-4 py-2.5 font-mono"><Link href={`/products/${p.id}`} className="text-accent hover:underline">{p.sku}</Link></td>
                  <td className="px-4 py-2.5">
                    <div className="font-medium">{p.name}</div>
                    {p.description && <div className="hidden max-w-md truncate text-xs text-faint lg:block">{p.description}</div>}
                  </td>
                  <td className="px-4 py-2.5"><Badge value={p.lifecycle_status} /></td>
                  <td className="px-4 py-2.5 text-muted">{formatDate(p.placed_on_market_at)}</td>
                  <td className="px-4 py-2.5 text-xs text-muted">
                    {p.sboms.length === 0 ? <span className="text-faint">none</span> : <span className="font-mono">{p.sboms[0].format} {p.sboms[0].spec_version}{p.sboms.length > 1 ? ` +${p.sboms.length - 1}` : ""}</span>}
                  </td>
                  <td className="px-4 py-2.5 text-right tabular-nums">{p.component_count.toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-right tabular-nums">
                    {p.open_incidents > 0 ? <Link href={`/products/${p.id}`} className="font-semibold text-danger hover:underline">{p.open_incidents}</Link> : <span className="text-faint">0</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border">
            <Pager page={current} pageSize={pageSize} total={filtered.length} onPage={setPage} onPageSize={(n) => { setPageSize(n); setPage(1); }} />
          </div>
        </Card>
      )}
    </div>
  );
}
