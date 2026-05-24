import { ShieldCheck, Smartphone, UploadCloud } from "lucide-react";
import { OperationsShell } from "@/components/operations/operations-shell";

export default function FieldProfilePage() {
  return (
    <OperationsShell eyebrow="Field identity" title="Worker profile">
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { label: "RBAC", body: "Field worker permissions are scoped by municipality, department, district, and assigned repair task.", icon: ShieldCheck },
          { label: "Offline", body: "Task acceptance, status changes, and proof uploads are queued locally until connectivity returns.", icon: Smartphone },
          { label: "Proof", body: "Before and after repair media must include timestamps and can be routed to AI verification hooks.", icon: UploadCloud }
        ].map((item) => (
          <div key={item.label} className="rounded-2xl border border-white/10 bg-white/[0.035] p-5">
            <item.icon className="size-6 text-civic-cyan" />
            <h2 className="mt-4 text-lg font-semibold text-white">{item.label}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{item.body}</p>
          </div>
        ))}
      </div>
    </OperationsShell>
  );
}
