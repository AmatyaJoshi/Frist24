import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import Nav from "@/components/Nav";
import ThemeToggle from "@/components/ThemeToggle";

export const metadata: Metadata = {
  title: "Frist24 — CRA Article 14 reporting",
  description: "Local-first, deterministic, auditable CRA Article 14 reporting assistant",
};

const themeInit = `try{if(localStorage.getItem("frist24-theme")==="dark"){document.documentElement.dataset.theme="dark"}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="flex min-h-screen flex-col antialiased">
        <header className="sticky top-0 z-30 border-b border-border bg-surface/85 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 md:px-6">
            <Link href="/" className="shrink-0 text-2xl font-extrabold tracking-tighter">
              Frist<span className="text-accent">24</span>
            </Link>
            <Nav />
            <div className="ml-auto flex items-center gap-3">
              <span className="hidden lg:inline text-xs text-faint">local-first · nothing leaves this machine</span>
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-6 md:py-8 anim-fade-up">{children}</main>
        <footer className="border-t border-border">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-faint md:px-6">
            <span>Frist24 · Regulation (EU) 2024/2847 Art. 14</span>
            <span>Deterministic first · LLM second · human always</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
