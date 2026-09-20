import { Bone, CardSkeleton, HeaderSkeleton } from "@/components/Skeleton";
import { Card } from "@/components/ui";

export default function Loading() {
  return (
    <div className="space-y-6">
      <HeaderSkeleton action={false} />
      <Card className="p-5 space-y-5">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Bone className="h-4 w-32" />
              <Bone className="h-9 w-full" />
            </div>
          ))}
        </div>
        <Bone className="h-3 w-72" />
        <div className="flex flex-wrap gap-1.5">
          {Array.from({ length: 27 }).map((_, i) => (
            <Bone key={i} className="h-7 w-10" />
          ))}
        </div>
        <Bone className="h-9 w-36" />
      </Card>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <CardSkeleton lines={4} />
        <CardSkeleton lines={5} />
        <CardSkeleton lines={4} />
      </div>
    </div>
  );
}
