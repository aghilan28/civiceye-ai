"use client";

import { motion } from "framer-motion";

export function OperationalSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="grid gap-3">
      {Array.from({ length: rows }).map((_, index) => (
        <motion.div
          key={index}
          className="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.045] p-4"
          animate={{ opacity: [0.45, 0.85, 0.45] }}
          transition={{ duration: 1.8, repeat: Infinity, delay: index * 0.12 }}
        >
          <div className="flex items-center gap-3">
            <div className="size-11 rounded-2xl bg-civic-cyan/10" />
            <div className="flex-1">
              <div className="h-3 w-2/3 rounded-full bg-white/10" />
              <div className="mt-3 h-2 w-1/2 rounded-full bg-white/8" />
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
