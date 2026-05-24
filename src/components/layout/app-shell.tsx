import type { ReactNode } from "react";
import { SessionHydrator } from "@/components/auth/session-hydrator";
import { RouteChrome } from "@/components/layout/route-chrome";
import { AmbientBackground } from "@/components/visual/ambient-background";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-x-clip bg-civic-bg">
      <SessionHydrator />
      <AmbientBackground />
      <RouteChrome>{children}</RouteChrome>
    </div>
  );
}
