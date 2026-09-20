"use client";

import { btnGhost } from "@/components/ui";

export const PAGE_SIZES = [25, 50, 100];

export default function Pager({
  page,
  pageSize,
  total,
  onPage,
  onPageSize,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPage: (p: number) => void;
  onPageSize: (n: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(total, page * pageSize);
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 text-xs text-muted">
      <span>
        Showing <span className="text-fg tabular-nums">{from}–{to}</span> of <span className="text-fg tabular-nums">{total.toLocaleString()}</span>
      </span>
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-1">
          Rows
          <select className="rounded-md border border-border bg-surface px-1.5 py-1 text-xs" value={pageSize} onChange={(e) => onPageSize(Number(e.target.value))}>
            {PAGE_SIZES.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>
        <button className={`${btnGhost} px-2 py-1 text-xs`} onClick={() => onPage(1)} disabled={page <= 1} aria-label="First page">«</button>
        <button className={`${btnGhost} px-2 py-1 text-xs`} onClick={() => onPage(page - 1)} disabled={page <= 1} aria-label="Previous page">‹</button>
        <span className="tabular-nums">Page {page} / {pages}</span>
        <button className={`${btnGhost} px-2 py-1 text-xs`} onClick={() => onPage(page + 1)} disabled={page >= pages} aria-label="Next page">›</button>
        <button className={`${btnGhost} px-2 py-1 text-xs`} onClick={() => onPage(pages)} disabled={page >= pages} aria-label="Last page">»</button>
      </div>
    </div>
  );
}
