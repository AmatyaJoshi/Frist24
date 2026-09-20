"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  { href: "/", label: "Overview", exact: true },
  { href: "/products", label: "Products" },
  { href: "/incidents", label: "Incidents" },
  { href: "/audit", label: "Audit" },
  { href: "/settings", label: "Settings" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <nav className="flex min-w-0 items-center gap-0.5 overflow-x-auto text-sm scrollbar-none">
      {ITEMS.map((it) => {
        const active = it.exact ? path === it.href : path.startsWith(it.href);
        return (
          <Link
            key={it.href}
            href={it.href}
            className={`relative shrink-0 rounded-md px-3 py-1.5 transition-colors ${active ? "text-fg font-medium" : "text-muted hover:text-fg hover:bg-surface-2"}`}
          >
            {it.label}
            {active && <span className="absolute inset-x-3 -bottom-3.25 h-0.5 rounded-full bg-accent" />}
          </Link>
        );
      })}
    </nav>
  );
}
