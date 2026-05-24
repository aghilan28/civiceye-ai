"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock, MapPin, Navigation, Wrench } from "lucide-react";
import { enterpriseApi } from "@/services/enterprise/enterprise-api";
import type { FieldTask } from "@/types/enterprise";

type FieldTaskBoardProps = {
  incidentId?: string;
};

export function FieldTaskBoard({ incidentId }: FieldTaskBoardProps) {
  const [tasks, setTasks] = useState<FieldTask[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    function refresh() {
      enterpriseApi
        .fieldTasks(undefined, controller.signal)
        .then((rows) => {
          setTasks(rows);
          setState("ready");
        })
        .catch(() => setState("error"));
    }
    refresh();
    const connection = enterpriseApi.connectEvents((event) => {
      if (event.type === "worker_assigned" || event.type === "repair_started" || event.type === "repair_completed" || event.type === "incident_updated") {
        refresh();
      }
    });
    return () => {
      controller.abort();
      connection.close();
    };
  }, []);

  const visibleTasks = useMemo(() => (incidentId ? tasks.filter((task) => task.incident_id === incidentId) : tasks), [incidentId, tasks]);

  if (state === "loading") {
    return <div className="rounded-lg border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-300">Loading field tasks from municipal work orders.</div>;
  }

  if (state === "error") {
    return <div className="rounded-lg border border-rose-300/20 bg-rose-500/10 p-5 text-sm text-rose-100">Field operations API is unavailable. Start the FastAPI backend and PostgreSQL database.</div>;
  }

  return (
    <div className="grid gap-4">
      {visibleTasks.length === 0 ? (
        <div className="rounded-lg border border-white/10 bg-white/[0.035] p-5 text-sm text-slate-400">No repair work orders are currently assigned for this view.</div>
      ) : null}
      {visibleTasks.map((task) => (
        <article key={task.id} className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-2.5 py-1 text-xs font-semibold text-cyan-200">{task.status.replace("_", " ")}</span>
                <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-xs font-semibold text-slate-300">{task.severity}</span>
                <span className="text-xs text-slate-500">{task.incident_code}</span>
              </div>
              <h2 className="mt-3 text-lg font-semibold text-white">{task.road_name ?? "Unmapped repair segment"}</h2>
              <p className="mt-1 flex items-center gap-2 text-sm text-slate-400">
                <MapPin className="size-4" />
                {task.latitude.toFixed(5)}, {task.longitude.toFixed(5)}
              </p>
            </div>
            <div className="grid grid-cols-3 gap-3 text-center">
              <TaskMetric icon={Clock} label="SLA" value={`${Math.max(0, Math.round((new Date(task.sla_due_at).getTime() - Date.now()) / 3600000))}h`} />
              <TaskMetric icon={Wrench} label="Priority" value={task.priority} />
              <TaskMetric icon={Navigation} label="Route" value="GPS" />
            </div>
          </div>
          {task.notes ? <p className="mt-4 rounded-md border border-white/10 bg-black/20 p-3 text-sm text-slate-300">{task.notes}</p> : null}
        </article>
      ))}
    </div>
  );
}

function TaskMetric({ icon: Icon, label, value }: { icon: typeof Clock; label: string; value: string | number }) {
  return (
    <div className="min-w-20 rounded-md border border-white/10 bg-black/20 p-3">
      <Icon className="mx-auto size-4 text-cyan-300" />
      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}
