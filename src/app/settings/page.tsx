import { Bell, Fingerprint, MapPin, Moon } from "lucide-react";
import { PageHeader } from "@/components/product/page-header";

export default function SettingsPage() {
  return (
    <section className="safe-x py-8 sm:py-12">
      <div className="mx-auto max-w-4xl">
        <PageHeader eyebrow="System preferences" title="Settings" description="Tune permissions, alert behavior, secure access, and operating preferences." />
        <div className="mt-6 grid gap-3">
          {[
            { title: "Location intelligence", body: "Use precise location for ward routing and report radius.", icon: MapPin },
            { title: "AI notifications", body: "Receive verification, escalation, and response updates.", icon: Bell },
            { title: "Secure passkey", body: "Enable biometric-ready authentication.", icon: Fingerprint },
            { title: "Dark operating mode", body: "CivicEye runs in premium dark mode by default.", icon: Moon }
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="flex items-center gap-4 rounded-3xl border border-white/10 bg-white/[0.055] p-4 backdrop-blur-2xl">
                <span className="grid size-12 place-items-center rounded-2xl bg-civic-cyan/10">
                  <Icon className="size-5 text-civic-cyan" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-white">{item.title}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{item.body}</p>
                </div>
                <span className="h-7 w-12 rounded-full bg-civic-cyan/20 p-1">
                  <span className="block size-5 rounded-full bg-civic-cyan shadow-glow" />
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
