import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type GlassPanelProps = HTMLAttributes<HTMLDivElement> & {
  glow?: "cyan" | "blue" | "purple" | "none";
};

export function GlassPanel({ className, glow = "none", ...props }: GlassPanelProps) {
  return (
    <div
      className={cn(
        "glass-panel neon-edge rounded-3xl",
        glow === "cyan" && "shadow-[0_0_58px_rgba(0,212,255,0.18)]",
        glow === "blue" && "shadow-[0_0_58px_rgba(79,140,255,0.18)]",
        glow === "purple" && "shadow-[0_0_58px_rgba(139,92,246,0.18)]",
        className
      )}
      {...props}
    />
  );
}
