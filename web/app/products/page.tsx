import { getProducts } from "@/lib/api";
import { Empty, ErrorBox, PageHeader } from "@/components/ui";
import UploadDrawer from "./UploadDrawer";
import ProductTable from "./ProductTable";
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
        subtitle={`${products.length} SKUs. Upload a CycloneDX or SPDX SBOM per SKU; components are matched on every sync.`}
        actions={<UploadDrawer products={products.map((p) => ({ id: p.id, sku: p.sku, name: p.name }))} />}
      />
      {error && <ErrorBox message={`API unreachable: ${error}`} />}
      {!error && products.length === 0 && <Empty title="No products yet" hint={<>Run <code>make demo</code> to seed the demo catalogue, or add a product above.</>} />}
      {products.length > 0 && <ProductTable rows={products} />}
    </div>
  );
}
