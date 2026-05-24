import { AlertTriangle, Bot, Droplets, LightbulbOff, Recycle, Route } from "lucide-react";

export const citySignals = [
  { label: "Potholes", value: "1,284", trend: "+18%", icon: Route, color: "text-civic-cyan", severity: "High" },
  { label: "Garbage zones", value: "342", trend: "-9%", icon: Recycle, color: "text-civic-success", severity: "Medium" },
  { label: "Drain overflow", value: "89", trend: "+7%", icon: Droplets, color: "text-civic-blue", severity: "Critical" },
  { label: "Streetlights", value: "216", trend: "-12%", icon: LightbulbOff, color: "text-civic-warning", severity: "Low" }
];

export const platformStats = [
  { value: "94.8%", numeric: 94.8, suffix: "%", label: "AI detection confidence", trend: "+4.2%" },
  { value: "42s", numeric: 42, suffix: "s", label: "median civic alert routing", trend: "-31%" },
  { value: "12.6k", numeric: 12.6, suffix: "k", label: "monthly verified reports", trend: "+22%" },
  { value: "7", numeric: 7, suffix: "", label: "infrastructure classes", trend: "live" }
];

export const detectionClasses = [
  { label: "Pothole", confidence: 97, icon: AlertTriangle },
  { label: "Garbage", confidence: 91, icon: Recycle },
  { label: "Water leak", confidence: 88, icon: Droplets },
  { label: "Road damage", confidence: 93, icon: Bot }
];

export const incidentFeed = [
  { zone: "Ward 18", issue: "Drainage overflow", eta: "3m ago", severity: "Critical", confidence: 96 },
  { zone: "MG Road", issue: "Road surface fracture", eta: "8m ago", severity: "High", confidence: 91 },
  { zone: "Indiranagar", issue: "Garbage accumulation", eta: "14m ago", severity: "Medium", confidence: 88 }
];

export const responseTimeline = [
  { label: "AI verified", value: "00:12", active: true },
  { label: "Zone routed", value: "00:42", active: true },
  { label: "Crew assigned", value: "04:18", active: true },
  { label: "Resolved SLA", value: "18:30", active: false }
];
