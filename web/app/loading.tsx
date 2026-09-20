export default function Loading() {
  return (
    <div className="flex items-center gap-3 text-sm text-muted py-10">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      Loading from the local API…
    </div>
  );
}
