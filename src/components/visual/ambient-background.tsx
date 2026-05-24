"use client";

import { motion } from "framer-motion";

const particles = Array.from({ length: 22 }, (_, index) => ({
  id: index,
  left: `${(index * 37) % 100}%`,
  top: `${(index * 53) % 100}%`,
  delay: index * 0.27,
  size: 2 + (index % 3)
}));

export function AmbientBackground() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
      <motion.div
        className="absolute -left-24 top-8 size-80 rounded-full bg-civic-blue/18 blur-3xl sm:size-[34rem]"
        animate={{ x: [0, 42, 12, 0], y: [0, 18, -18, 0], opacity: [0.42, 0.72, 0.46] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute -right-32 top-28 size-96 rounded-full bg-civic-purple/18 blur-3xl sm:size-[38rem]"
        animate={{ x: [0, -34, -8, 0], y: [0, -22, 24, 0], opacity: [0.34, 0.68, 0.4] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-20 left-1/3 size-72 rounded-full bg-civic-cyan/12 blur-3xl sm:size-[32rem]"
        animate={{ scale: [1, 1.18, 0.96, 1], opacity: [0.28, 0.58, 0.34] }}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="absolute inset-0 grid-mask opacity-80" />
      <div className="absolute inset-0 bg-[linear-gradient(115deg,transparent_0%,rgba(79,140,255,0.045)_24%,transparent_42%,rgba(0,212,255,0.04)_64%,transparent_100%)]" />
      <motion.div
        className="absolute left-1/2 top-1/2 h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-civic-cyan/10"
        animate={{ scale: [0.72, 1.18], opacity: [0.28, 0] }}
        transition={{ duration: 5.5, repeat: Infinity, ease: "easeOut" }}
      />
      <motion.div
        className="absolute left-1/2 top-1/2 h-[24rem] w-[24rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-civic-blue/10"
        animate={{ scale: [0.82, 1.26], opacity: [0.22, 0] }}
        transition={{ duration: 6.5, repeat: Infinity, ease: "easeOut", delay: 1.1 }}
      />
      {particles.map((particle) => (
        <motion.span
          key={particle.id}
          className="absolute rounded-full bg-civic-cyan/70 shadow-[0_0_14px_rgba(0,212,255,0.75)]"
          style={{
            left: particle.left,
            top: particle.top,
            width: particle.size,
            height: particle.size
          }}
          animate={{ y: [0, -28, 0], opacity: [0.12, 0.72, 0.12] }}
          transition={{ duration: 6 + (particle.id % 5), repeat: Infinity, delay: particle.delay, ease: "easeInOut" }}
        />
      ))}
      <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-civic-bg via-civic-bg/80 to-transparent" />
    </div>
  );
}
