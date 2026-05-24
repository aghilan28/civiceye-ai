import type { LucideIcon } from "lucide-react";
import { BarChart3, Bell, BrainCircuit, Camera, Home, Map, Presentation, Radio, ShieldCheck } from "lucide-react";

export type NavigationItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

export const navigationItems: NavigationItem[] = [
  { label: "Platform", href: "#platform", icon: Home },
  { label: "Intelligence", href: "#intelligence", icon: Radio },
  { label: "Analytics", href: "#analytics", icon: BarChart3 },
  { label: "Operations", href: "#operations", icon: Map },
  { label: "AI Command", href: "/ai/live", icon: BrainCircuit },
  { label: "Demo", href: "/demo", icon: Presentation },
  { label: "Admin", href: "/admin", icon: ShieldCheck }
];

export const bottomNavigationItems: NavigationItem[] = [
  { label: "Home", href: "/dashboard", icon: Home },
  { label: "AI", href: "/ai/live", icon: BrainCircuit },
  { label: "Report", href: "/report", icon: Camera },
  { label: "Reports", href: "/reports", icon: Map },
  { label: "Alerts", href: "/notifications", icon: Bell }
];
