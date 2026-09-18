import type { Metadata } from "next";
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
          <span className="font-semibold tracking-tight">
            Frist<span style={{ color: "var(--accent)" }}>24</span>
          </span>
          <nav className="text-sm flex gap-4" style={{ color: "var(--muted)" }}>
            <a href="/products">Products</a>
            <a href="/incidents">Incidents</a>
            <a href="/audit">Audit</a>
          </nav>
        </header>
        <main className="px-6 py-8 max-w-6xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
