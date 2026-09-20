import { ChipsSkeleton, HeaderSkeleton, TableSkeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div className="space-y-3">
      <HeaderSkeleton />
      <ChipsSkeleton />
      <TableSkeleton rows={8} cols={9} />
    </div>
  );
}
