import { Card } from "@/components/ui";

export function Bone({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-md ${className}`} aria-hidden="true" />;
}

export function HeaderSkeleton({ action = true }: { action?: boolean }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="space-y-2">
        <Bone className="h-7 w-48" />
        <Bone className="h-4 w-80 max-w-full" />
      </div>
      {action && <Bone className="h-9 w-32" />}
    </div>
  );
}

export function StatSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="p-4 space-y-2">
          <Bone className="h-3 w-24" />
          <Bone className="h-8 w-16" />
          <Bone className="h-3 w-28" />
        </Card>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 6, cols = 6, header = true }: { rows?: number; cols?: number; header?: boolean }) {
  return (
    <Card className="overflow-hidden">
      {header && (
        <div className="flex gap-4 border-b border-border bg-surface-2 px-4 py-3">
          {Array.from({ length: cols }).map((_, i) => (
            <Bone key={i} className="h-3 flex-1" />
          ))}
        </div>
      )}
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex items-center gap-4 border-t border-border px-4 py-3 first:border-t-0">
          {Array.from({ length: cols }).map((_, c) => (
            <Bone key={c} className={`h-4 flex-1 ${c === 0 ? "max-w-32" : ""}`} />
          ))}
        </div>
      ))}
    </Card>
  );
}

export function CardSkeleton({ lines = 4, className = "" }: { lines?: number; className?: string }) {
  return (
    <Card className={`p-4 space-y-3 ${className}`}>
      <Bone className="h-3 w-32" />
      {Array.from({ length: lines }).map((_, i) => (
        <Bone key={i} className={`h-4 ${i % 3 === 2 ? "w-2/3" : "w-full"}`} />
      ))}
    </Card>
  );
}

export function ChipsSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Bone className="h-9 w-64" />
      {Array.from({ length: count }).map((_, i) => (
        <Bone key={i} className="h-7 w-24" />
      ))}
    </div>
  );
}
