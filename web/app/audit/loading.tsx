import { ChipsSkeleton, HeaderSkeleton, TableSkeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div className="space-y-4">
      <HeaderSkeleton />
      <ChipsSkeleton count={8} />
      <TableSkeleton rows={12} cols={5} />
    </div>
  );
}
