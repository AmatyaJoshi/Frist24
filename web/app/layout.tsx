import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Frist24",
  description: "CRA Article 14 reporting assistant — local-first, deterministic, auditable",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <header className="border-b border-white/10 px-6 py-3 flex items-center gap-6">
          <Link href="/" className="font-semibold tracking-tight">
            Frist<span style={{ color: "var(--accent)" }}>24</span>
          </Link>
          <nav className="text-sm flex gap-4" style={{ color: "var(--muted)" }}>
            <Link href="/products" className="hover:text-white">Products</Link>
            <Link href="/incidents" className="hover:text-white">Incidents</Link>
            <Link href="/audit" className="hover:text-white">Audit</Link>
          </nav>
          <span className="ml-auto text-xs text-white/30">local-first · no vulnerability data leaves this machine</span>
        </header>
        <main className="px-6 py-8 max-w-7xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
