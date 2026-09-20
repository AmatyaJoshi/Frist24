import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import Nav from "@/components/Nav";
import ThemeToggle from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "Frist24 — CRA Article 14 reporting",
  description: "Local-first, deterministic, auditable CRA Article 14 reporting assistant",
};

// Applied before hydration so the stored theme never flashes.
const themeInit = `try{var t=localStorage.getItem("frist24-theme");if(t==="dark"||(t===null&&window.matchMedia("(prefers-color-scheme: dark)").matches&&false)){document.documentElement.dataset.theme="dark"}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="min-h-screen antialiased">
        <header className="sticky top-0 z-30 border-b border-border bg-surface/90 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-6">
            <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-accent text-white text-xs font-bold">24</span>
              <span>Frist<span className="text-accent">24</span></span>
            </Link>
            <Nav />
            <div className="ml-auto flex items-center gap-3">
              <span className="hidden md:inline text-xs text-faint">local-first · no vulnerability data leaves this machine</span>
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8 anim-fade-up">{children}</main>
        <footer className="mx-auto max-w-7xl px-6 py-8 text-xs text-faint border-t border-border mt-8">
          Frist24 · Regulation (EU) 2024/2847 Art. 14 · Deterministic first, LLM second, human always. Report schemas are the manufacturer&apos;s working
          interpretation, not the official ENISA form.
        </footer>
      </body>
    </html>
  );
}
