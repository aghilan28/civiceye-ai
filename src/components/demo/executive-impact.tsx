import { Building2, HeartPulse, ShieldCheck, TrendingDown } from "lucide-react";

const impactMetrics = [
  { label: "Infrastructure resilience", value: "84", unit: "/100", icon: ShieldCheck },
  { label: "Incident reduction", value: "31", unit: "%", icon: TrendingDown },
  { label: "Citizen satisfaction", value: "4.7", unit: "/5", icon: HeartPulse },
  { label: "Municipality efficiency", value: "42", unit: "% faster", icon: Building2 }
];

export function ExecutiveImpact() {
  return (
    <div className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-4 backdrop-blur-2xl">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Executive impact</p>
      <h2 className="mt-1 text-xl font-semibold text-white">City improvement story</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {impactMetrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
              <Icon className="size-5 text-civic-cyan" />
              <p className="mt-4 text-3xl font-semibold text-white">
                {metric.value}
                <span className="text-sm text-slate-400">{metric.unit}</span>
              </p>
              <p className="mt-1 text-sm text-slate-400">{metric.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
