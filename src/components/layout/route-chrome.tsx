"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { ProtectedRoute } from "@/components/auth/protected-route";
import { BottomNavigation } from "@/components/layout/bottom-navigation";
import { Navbar } from "@/components/layout/navbar";
import { FloatingReportFab } from "@/components/product/floating-report-fab";

const authPrefixes = ["/auth"];
const onboardingPrefixes = ["/onboarding"];
const appPrefixes = ["/dashboard", "/report", "/reports", "/notifications", "/profile", "/settings", "/map", "/admin", "/demo", "/operations", "/field", "/analytics", "/ai"];

function matches(pathname: string, prefixes: string[]) {
  return prefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function RouteChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAuth = matches(pathname, authPrefixes);
  const isOnboarding = matches(pathname, onboardingPrefixes);
  const isApp = matches(pathname, appPrefixes);
  const showNavbar = !isAuth && !isOnboarding;
  const showBottomNav = !isAuth && !isOnboarding;
  const showFab = isApp && pathname !== "/report";

  return (
    <>
      {showNavbar ? <Navbar /> : null}
      <main className="relative z-10 pb-24 md:pb-0">
        {isApp ? <ProtectedRoute demoMode={pathname.startsWith("/demo")}>{children}</ProtectedRoute> : children}
      </main>
      {showFab ? <FloatingReportFab /> : null}
      {showBottomNav ? <BottomNavigation /> : null}
    </>
  );
}
