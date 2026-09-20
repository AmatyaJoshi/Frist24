import { HeaderSkeleton, StatSkeleton, TableSkeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div className="space-y-6">
      <HeaderSkeleton action={false} />
      <StatSkeleton />
      <TableSkeleton rows={6} cols={4} header={false} />
    </div>
  );
}
