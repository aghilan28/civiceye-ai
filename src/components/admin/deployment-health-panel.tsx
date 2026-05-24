import { Activity, Cloud, GitBranch, ShieldCheck } from "lucide-react";

const deploymentSignals = [
  { label: "Frontend", value: "Vercel ready", icon: Cloud },
  { label: "Backend", value: "Docker ready", icon: Activity },
  { label: "CI/CD", value: "GitHub Actions", icon: GitBranch },
  { label: "Security", value: "RBAC active", icon: ShieldCheck }
];

export function DeploymentHealthPanel() {
  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Deployment health</p>
      <h2 className="mt-1 text-xl font-semibold text-white">Production readiness</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {deploymentSignals.map((signal) => {
          const Icon = signal.icon;
          return (
            <div key={signal.label} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
              <Icon className="size-5 text-civic-cyan" />
              <p className="mt-3 text-sm font-semibold text-white">{signal.value}</p>
              <p className="mt-1 text-xs text-slate-500">{signal.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
