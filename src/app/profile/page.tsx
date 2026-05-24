import { Building2, Mail, ShieldCheck, UserCircle } from "lucide-react";
import { PageHeader } from "@/components/product/page-header";

export default function ProfilePage() {
  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-4xl">
        <PageHeader eyebrow="Operational identity" title="Profile" description="Manage the identity used for civic reports, response workflows, and municipality collaboration." />
        <div className="mt-8 rounded-[2rem] border border-white/10 bg-white/[0.055] p-5 backdrop-blur-2xl">
          <div className="flex items-center gap-4">
            <span className="grid size-20 place-items-center rounded-3xl border border-civic-cyan/20 bg-civic-cyan/10 shadow-glow">
              <UserCircle className="size-10 text-civic-cyan" />
            </span>
            <div>
              <h2 className="text-2xl font-semibold text-white">Aarav Mehta</h2>
              <p className="mt-1 text-sm text-slate-400">Operations Analyst</p>
            </div>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {[
              { label: "Email", value: "aarav@civiceye.ai", icon: Mail },
              { label: "Municipality", value: "Bengaluru Zone 07", icon: Building2 },
              { label: "Trust level", value: "Verified", icon: ShieldCheck }
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="rounded-2xl border border-white/10 bg-civic-bg/58 p-4">
                  <Icon className="size-5 text-civic-cyan" />
                  <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">{item.label}</p>
                  <p className="mt-1 truncate text-sm font-semibold text-white">{item.value}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
