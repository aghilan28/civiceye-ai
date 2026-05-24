import { Github, Linkedin, ShieldCheck, Twitter } from "lucide-react";

const footerLinks = ["Platform", "AI Detection", "Operations", "Security"];

export function Footer() {
  return (
    <footer className="safe-x border-t border-white/10 bg-civic-bg/44 py-8 backdrop-blur-2xl">
      <div className="mx-auto grid max-w-7xl gap-8 text-sm text-slate-400 md:grid-cols-[1fr_auto_auto] md:items-center">
        <div className="max-w-md">
          <div className="flex items-center gap-2">
            <span className="relative grid size-9 place-items-center rounded-xl border border-civic-cyan/30 bg-civic-cyan/10 shadow-glow">
              <span className="absolute inset-1 rounded-lg bg-civic-cyan/10 blur-sm" />
              <ShieldCheck className="relative size-5 text-civic-cyan" />
            </span>
            <span className="font-semibold text-white">CivicEye</span>
          </div>
          <p className="mt-3 leading-6">AI civic infrastructure intelligence for mobile-first city operations.</p>
        </div>

        <nav aria-label="Footer navigation" className="flex flex-wrap gap-3 md:justify-end">
          {footerLinks.map((link) => (
            <a key={link} href="#platform" className="rounded-full px-3 py-2 transition hover:bg-white/8 hover:text-white">
              {link}
            </a>
          ))}
        </nav>

        <div className="flex gap-2 md:justify-end">
          {[
            { icon: Twitter, label: "CivicEye on X" },
            { icon: Linkedin, label: "CivicEye on LinkedIn" },
            { icon: Github, label: "CivicEye on GitHub" }
          ].map(({ icon: Icon, label }) => (
            <a
              key={label}
              href="#platform"
              aria-label={label}
              className="grid size-10 place-items-center rounded-2xl border border-white/10 bg-white/[0.055] text-slate-300 transition hover:border-civic-cyan/30 hover:text-civic-cyan"
            >
              <Icon className="size-4" />
            </a>
          ))}
        </div>
      </div>
    </footer>
  );
}
