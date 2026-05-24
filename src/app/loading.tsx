import { OperationalSkeleton } from "@/components/product/operational-skeleton";

export default function Loading() {
  return (
    <section className="safe-x py-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6">
          <div className="h-4 w-36 rounded-full bg-civic-cyan/10" />
          <div className="mt-4 h-10 w-2/3 rounded-full bg-white/10" />
          <div className="mt-3 h-4 w-1/2 rounded-full bg-white/8" />
        </div>
        <OperationalSkeleton rows={4} />
      </div>
    </section>
  );
}
