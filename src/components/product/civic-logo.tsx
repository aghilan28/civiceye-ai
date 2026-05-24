import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export function CivicLogo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span className="relative grid size-10 shrink-0 place-items-center rounded-2xl border border-civic-cyan/30 bg-civic-cyan/10 shadow-glow">
        <span className="absolute inset-1 rounded-xl bg-civic-cyan/10 blur-sm" />
        <ShieldCheck className="relative size-5 text-civic-cyan" />
      </span>
      <span className="text-lg font-semibold tracking-normal text-white">CivicEye</span>
    </div>
  );
}
