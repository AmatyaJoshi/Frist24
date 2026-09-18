import Link from "next/link";
import { getProducts } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/time";
import { Badge, Card, Empty, ErrorBox, PageHeader } from "@/components/ui";
import UploadDrawer from "./UploadDrawer";
import type { Product } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ProductsPage() {
  let products: Product[] = [];
  let error: string | null = null;
  try {
    products = await getProducts();
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }
  return (
    <div>
      <PageHeader
        title="Products"
        subtitle="Products with digital elements you place on the EU market. Upload a CycloneDX or SPDX SBOM per SKU; components are matched against OSV, KEV and EPSS on every sync."
        actions={<UploadDrawer products={products.map((p) => ({ id: p.id, sku: p.sku, name: p.name }))} />}
      />
      {error && <ErrorBox message={`API unreachable: ${error}`} />}
      {!error && products.length === 0 && <Empty title="No products yet" hint={<>Run <code>make demo</code> to seed two SKUs with real public SBOMs, or add a product above.</>} />}
      {products.length > 0 && (
        <Card>
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-white/40">
              <tr>
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Lifecycle</th>
                <th className="px-4 py-3">On market</th>
                <th className="px-4 py-3">SBOMs</th>
                <th className="px-4 py-3 text-right">Components</th>
                <th className="px-4 py-3 text-right">Open incidents</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-t border-white/5 hover:bg-white/[0.03]">
                  <td className="px-4 py-3 font-mono">{p.sku}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{p.name}</div>
                    {p.description && <div className="text-xs text-white/40 max-w-md truncate">{p.description}</div>}
                  </td>
                  <td className="px-4 py-3"><Badge value={p.lifecycle_status} /></td>
                  <td className="px-4 py-3 text-white/60">{formatDate(p.placed_on_market_at)}</td>
                  <td className="px-4 py-3 text-white/70">
                    {p.sboms.length === 0 && <span className="text-white/30">none</span>}
                    {p.sboms.map((s) => (
                      <div key={s.id} className="text-xs" title={`sha256 ${s.sha256}`}>
                        <span className="font-mono">{s.format} {s.spec_version}</span> · {s.filename ?? "upload"} · {formatDateTime(s.uploaded_at)}
                      </div>
                    ))}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{p.component_count}</td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {p.open_incidents > 0 ? (
                      <Link href="/incidents" className="text-red-300 font-semibold hover:underline">{p.open_incidents}</Link>
                    ) : (
                      <span className="text-white/30">0</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
