import { notFound } from "next/navigation";
import { AlertTriangle, Clock3, MapPin, RadioTower, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/product/page-header";
import { Button } from "@/components/ui/button";
import type { OperationsIncident } from "@/types/phase3";

function formatStatus(status: string) {
  return status.replaceAll("_", " ");
}

async function loadIncident(id: string) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const municipalityId = process.env.NEXT_PUBLIC_MUNICIPALITY_ID ?? "MUNI-BLR";
  const response = await fetch(`${apiBaseUrl}/operations/incidents?municipality_id=${encodeURIComponent(municipalityId)}&limit=500`, {
    cache: "no-store"
  });
  if (!response.ok) {
    return null;
  }
  const incidents = (await response.json()) as OperationsIncident[];
  return incidents.find((incident) => incident.incident_id === id || incident.incident_code === id) ?? null;
}

export default async function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const incident = await loadIncident(id);

  if (!incident) {
    notFound();
  }

  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-6xl">
        <PageHeader
          eyebrow={incident.incident_code}
          title="Persisted municipal incident"
          description={`${incident.road_name ?? "Unmapped road segment"} - routed to ${incident.assigned_department ?? "department queue"} with ${Math.round(incident.confidence * 100)}% AI confidence.`}
          action={<Button variant="gradient">Assign response</Button>}
        />
        <div className="mt-8 grid gap-5 lg:grid-cols-[1fr_0.82fr]">
          <div className="relative min-h-[32rem] overflow-hidden rounded-[2rem] border border-white/10 bg-[#06101f] p-5 backdrop-blur-2xl">
            <div className="absolute inset-0 bg-[linear-gradient(rgba(14,165,233,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(14,165,233,0.12)_1px,transparent_1px)] bg-[size:34px_34px]" />
            <div className="relative">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-500">AI evidence viewport</p>
              <h2 className="mt-1 text-2xl font-semibold text-white">Verified incident area</h2>
              <p className="mt-2 text-sm text-slate-400">
                {incident.latitude.toFixed(6)}, {incident.longitude.toFixed(6)} · {incident.geohash}
              </p>
            </div>
            <div className="absolute left-[38%] top-[42%] size-24 rounded-full border-2 border-civic-cyan bg-civic-cyan/10 shadow-glow">
              <span className="absolute -top-9 left-0 rounded-full bg-civic-cyan px-3 py-1 text-xs font-semibold text-civic-bg">{Math.round(incident.confidence * 100)}% confidence</span>
            </div>
          </div>

          <div className="grid gap-4">
            {[
              { label: "Severity", value: incident.severity, icon: AlertTriangle },
              { label: "Status", value: formatStatus(incident.status), icon: ShieldCheck },
              { label: "Department", value: incident.assigned_department ?? "Unassigned", icon: RadioTower },
              { label: "SLA due", value: new Date(incident.sla_due_at).toLocaleString(), icon: Clock3 },
              { label: "Location", value: [incident.road_name, incident.district, incident.city, incident.state].filter(Boolean).join(", "), icon: MapPin }
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="rounded-3xl border border-white/10 bg-white/[0.055] p-4 backdrop-blur-2xl">
                  <div className="flex items-center gap-3">
                    <span className="grid size-11 place-items-center rounded-2xl bg-civic-cyan/10">
                      <Icon className="size-5 text-civic-cyan" />
                    </span>
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                      <p className="mt-1 text-sm font-semibold capitalize text-white">{item.value}</p>
                    </div>
                  </div>
                </div>
              );
            })}
            <div className="rounded-3xl border border-white/10 bg-white/[0.055] p-4 backdrop-blur-2xl">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Operational trace</p>
              <div className="mt-4 grid gap-3">
                {[
                  ["Detected", incident.detected_at],
                  ["SLA due", incident.sla_due_at],
                  ["Last updated", incident.updated_at]
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl bg-civic-bg/58 p-3">
                    <p className="text-sm font-semibold capitalize text-white">{label}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{new Date(value).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
