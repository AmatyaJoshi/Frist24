import { HeaderSkeleton, TableSkeleton } from "@/components/Skeleton";

export default function Loading() {
  return (
    <div>
      <HeaderSkeleton />
      <TableSkeleton rows={8} cols={7} />
    </div>
  );
}
