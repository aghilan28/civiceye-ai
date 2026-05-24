"use client";

import { motion } from "framer-motion";
import { Navigation, UsersRound } from "lucide-react";
import { useAppStore } from "@/store/use-app-store";

export function FieldResponsePanel() {
  const teams = useAppStore((state) => state.fieldTeams);

  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Field response</p>
          <h2 className="mt-1 text-xl font-semibold text-white">Team deployment</h2>
        </div>
        <UsersRound className="size-5 text-civic-cyan" />
      </div>
      <div className="grid gap-3">
        {teams.map((team) => (
          <div key={team.id} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-2xl bg-civic-cyan/10">
                <Navigation className="size-5 text-civic-cyan" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white">{team.name}</p>
                <p className="truncate text-xs capitalize text-slate-400">{team.status.replaceAll("_", " ")} - {team.currentZone}</p>
              </div>
              {team.etaMinutes ? <span className="text-xs font-semibold text-civic-cyan">{team.etaMinutes}m</span> : null}
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
              <motion.div
                animate={{ width: `${team.routeProgress}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className="h-full rounded-full bg-gradient-to-r from-civic-blue to-civic-cyan"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
