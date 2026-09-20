import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getComponents, getIncidents, getProduct } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/time";
import { Badge, Card, Empty, ErrorBox, PageHeader, SectionTitle, input } from "@/components/ui";
import Countdown from "@/components/Countdown";
import type { Component, IncidentListItem, Product } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ProductPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ q?: string }> }) {
  const { id } = await params;
  const { q = "" } = await searchParams;
  let product: Product;
  let components: Component[] = [];
  let incidents: IncidentListItem[] = [];
  try {
    product = await getProduct(id);
    [components, incidents] = await Promise.all([getComponents(id, q || undefined, 300), getIncidents().catch(() => [])]);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    return <ErrorBox message={`API error: ${e instanceof Error ? e.message : String(e)}`} />;
  }
  const mine = incidents.filter((i) => i.product_id === id);
  const byEco = components.reduce<Record<string, number>>((acc, c) => {
    const k = c.ecosystem ?? "no purl";
    acc[k] = (acc[k] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${product.sku} · ${product.name}`}
        subtitle={
          <>
            <Link href="/products" className="hover:underline">Products</Link> / {product.sku}
            {product.description && <span className="block mt-1">{product.description}</span>}
          </>
        }
        actions={<Badge value={product.lifecycle_status} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 stagger">
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Product</SectionTitle>
          <Row k="Placed on market" v={formatDate(product.placed_on_market_at)} />
          <Row k="Components" v={String(product.component_count)} />
          <Row k="Open incidents" v={String(product.open_incidents)} accent={product.open_incidents > 0} />
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>SBOMs</SectionTitle>
          {product.sboms.length === 0 && <div className="text-faint">none uploaded</div>}
          {product.sboms.map((s) => (
            <div key={s.id} className="text-xs">
              <span className="font-mono">{s.format} {s.spec_version}</span> · {s.filename} · {s.component_count} components
              <div className="text-faint">{formatDateTime(s.uploaded_at)} · sha256 {s.sha256.slice(0, 16)}…</div>
            </div>
          ))}
        </Card>
        <Card className="p-4 text-sm space-y-2">
          <SectionTitle>Incidents for this product</SectionTitle>
          {mine.length === 0 && <div className="text-faint">none</div>}
          {mine.map((i) => (
            <Link key={i.id} href={`/incidents/${i.id}`} className="flex items-center justify-between gap-2 rounded-md px-2 py-1 hover:bg-surface-2">
              <span className="font-mono text-accent">{i.cve_id}</span>
              <Countdown deadline={i.next_deadline} compact />
            </Link>
          ))}
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 border-b border-border px-4 py-3">
          <SectionTitle>Components</SectionTitle>
          <form className="flex items-center gap-2" action={`/products/${id}`}>
            <input name="q" defaultValue={q} placeholder="Filter by name or PURL…" className={`${input} w-72`} />
            <button className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-surface-2">Filter</button>
          </form>
          <div className="ml-auto flex gap-1 text-[11px] text-faint">
            {Object.entries(byEco).sort((a, b) => b[1] - a[1]).map(([k, n]) => (
              <span key={k} className="rounded border border-border px-1.5 py-0.5">{k} {n}</span>
            ))}
          </div>
        </div>
        {components.length === 0 ? (
          <Empty title="No components match" />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-[11px] uppercase">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Version</th>
                <th className="px-4 py-2">Ecosystem</th>
                <th className="px-4 py-2">PURL</th>
              </tr>
            </thead>
            <tbody>
              {components.map((c) => (
                <tr key={c.id} className="border-t border-border hover:bg-surface-2">
                  <td className="px-4 py-1.5">{c.name}</td>
                  <td className="px-4 py-1.5 font-mono text-xs">{c.version ?? "–"}</td>
                  <td className="px-4 py-1.5 text-xs text-muted">{c.ecosystem ?? <span className="text-warn">no purl</span>}</td>
                  <td className="px-4 py-1.5 font-mono text-xs text-muted break-all">{c.purl ?? "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {components.length >= 300 && <div className="px-4 py-2 text-xs text-faint border-t border-border">Showing the first 300. Use the filter to narrow down.</div>}
      </Card>
    </div>
  );
}

function Row({ k, v, accent = false }: { k: string; v: string; accent?: boolean }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted">{k}</span>
      <span className={`tabular-nums ${accent ? "text-danger font-semibold" : ""}`}>{v}</span>
    </div>
  );
}
