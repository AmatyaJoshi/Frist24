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
    <nav className="flex items-center gap-1 text-sm">
      {ITEMS.map((it) => {
        const active = it.exact ? path === it.href : path.startsWith(it.href);
        return (
          <Link
            key={it.href}
            href={it.href}
            className={`rounded-md px-3 py-1.5 transition-colors ${active ? "bg-surface-3 text-fg font-medium" : "text-muted hover:text-fg hover:bg-surface-2"}`}
          >
            {it.label}
          </Link>
        );
      })}
    </nav>
  );
}
