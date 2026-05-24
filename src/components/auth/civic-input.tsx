"use client";

import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type CivicInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function CivicInput({ label, className, ...props }: CivicInputProps) {
  return (
    <label className="group block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 group-focus-within:text-civic-cyan">
        {label}
      </span>
      <input
        className={cn(
          "h-14 w-full rounded-2xl border border-white/10 bg-white/[0.055] px-4 text-sm font-medium text-white outline-none transition placeholder:text-slate-600 focus:border-civic-cyan/40 focus:bg-civic-cyan/8 focus:shadow-[0_0_34px_rgba(0,212,255,0.14)]",
          className
        )}
        {...props}
      />
    </label>
  );
}
