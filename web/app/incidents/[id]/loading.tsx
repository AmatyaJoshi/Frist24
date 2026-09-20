import { Bone, CardSkeleton } from "@/components/Skeleton";
import { Card } from "@/components/ui";

export default function Loading() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <Bone className="h-3 w-32" />
          <Bone className="h-7 w-96 max-w-full" />
          <Bone className="h-4 w-64" />
        </div>
        <Card className="grid w-full grid-cols-1 gap-4 p-4 sm:grid-cols-3 sm:gap-6 xl:w-auto">
          {[0, 1, 2].map((i) => (
            <div key={i} className="space-y-2 text-center">
              <Bone className="mx-auto h-3 w-28" />
              <Bone className="mx-auto h-7 w-24" />
              <Bone className="mx-auto h-3 w-32" />
            </div>
          ))}
        </Card>
      </div>
      <Card className="px-4 py-3"><Bone className="h-6 w-full" /></Card>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)_minmax(0,0.9fr)]">
        <div className="space-y-4">
          <CardSkeleton lines={3} />
          <CardSkeleton lines={4} />
          <CardSkeleton lines={2} />
        </div>
        <div className="space-y-4">
          <CardSkeleton lines={2} />
          <CardSkeleton lines={10} />
        </div>
        <CardSkeleton lines={8} />
      </div>
    </div>
  );
}
