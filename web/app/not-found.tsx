import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-16 text-center space-y-3">
      <div className="text-2xl font-semibold">Not found</div>
      <p className="text-white/50 text-sm">That incident or page does not exist (it may have been reset).</p>
      <Link href="/incidents" className="text-amber-200 hover:underline text-sm">Back to incidents</Link>
    </div>
  );
}
