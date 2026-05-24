"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { bottomNavigationItems } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function BottomNavigation() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Mobile navigation"
      className="safe-x fixed inset-x-0 bottom-0 z-50 pb-safe pt-2 md:hidden"
    >
      <div className="mx-auto grid max-w-md grid-cols-5 gap-1 rounded-[1.75rem] border border-white/12 bg-civic-bg/72 p-1.5 shadow-[0_20px_60px_rgba(0,0,0,0.45),0_0_42px_rgba(0,212,255,0.12)] backdrop-blur-2xl">
        {bottomNavigationItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex min-h-14 flex-col items-center justify-center gap-1 overflow-hidden rounded-[1.35rem] px-2 text-[11px] font-semibold text-slate-400 transition duration-300 active:scale-95",
                active && "text-white"
              )}
            >
              {active ? (
                <motion.span
                  layoutId="mobile-nav-active"
                  className="absolute inset-0 rounded-[1.35rem] border border-civic-cyan/24 bg-[linear-gradient(135deg,rgba(79,140,255,0.22),rgba(0,212,255,0.12))] shadow-[0_0_32px_rgba(0,212,255,0.22)]"
                  transition={{ type: "spring", stiffness: 420, damping: 34 }}
                />
              ) : null}
              <motion.span
                animate={active ? { y: -1, scale: 1.05 } : { y: 0, scale: 1 }}
                transition={{ type: "spring", stiffness: 360, damping: 24 }}
                className="relative z-10"
              >
                <Icon className={cn("size-5 transition group-hover:text-civic-cyan", active && "text-civic-cyan")} />
              </motion.span>
              <span className="relative z-10 max-w-full truncate">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
