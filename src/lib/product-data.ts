import {
  AlertTriangle,
  Bell,
  Building2,
  Camera,
  CheckCircle2,
  Droplets,
  MapPin,
  RadioTower,
  Recycle,
  Route,
  ShieldCheck,
  Sparkles,
  UsersRound,
  Zap
} from "lucide-react";
import type { CivicIssueType, CivicSeverity } from "@/types/civic";

export type OnboardingStep = {
  slug: string;
  eyebrow: string;
  title: string;
  body: string;
  primary: string;
  secondary?: string;
  icon: typeof Sparkles;
};

export type DemoIncident = {
  id: string;
  title: string;
  location: string;
  issueType: CivicIssueType;
  severity: CivicSeverity;
  confidence: number;
  status: "AI verified" | "Crew assigned" | "Municipality review" | "Resolved";
  eta: string;
  department: string;
};

export const onboardingSteps: OnboardingStep[] = [
  {
    slug: "welcome",
    eyebrow: "City intelligence online",
    title: "Welcome to CivicEye",
    body: "Launch into an AI civic network that turns reports, sensors, and municipal workflows into one operational city layer.",
    primary: "Continue",
    secondary: "Skip for now",
    icon: Sparkles
  },
  {
    slug: "permissions",
    eyebrow: "AI monitoring flow",
    title: "How AI monitoring works",
    body: "Computer vision detects damage, maps severity, geotags the incident, and routes it to the right response queue.",
    primary: "See permissions",
    icon: RadioTower
  },
  {
    slug: "location-access",
    eyebrow: "Location intelligence",
    title: "Enable precise civic context",
    body: "Location access helps CivicEye identify the ward, response radius, nearby reports, and repair priority.",
    primary: "Allow location",
    secondary: "Not now",
    icon: MapPin
  },
  {
    slug: "notifications",
    eyebrow: "Response updates",
    title: "Stay in the incident loop",
    body: "Get AI verification, crew assignment, municipality response, and resolution updates as the report moves.",
    primary: "Enable alerts",
    secondary: "Later",
    icon: Bell
  },
  {
    slug: "role-selection",
    eyebrow: "Operational identity",
    title: "Choose your CivicEye role",
    body: "Tune the app around reporting, municipal response, analytics, or smart-city partnership workflows.",
    primary: "Enter CivicEye",
    icon: UsersRound
  }
];

export const roleOptions = [
  { title: "Citizen", description: "Report issues and track city response.", icon: Camera },
  { title: "Municipality Officer", description: "Verify, assign, and resolve civic incidents.", icon: Building2 },
  { title: "Operations Analyst", description: "Monitor infrastructure patterns and SLA risk.", icon: Route },
  { title: "Smart-City Partner", description: "Connect sensors, AI models, and field teams.", icon: ShieldCheck }
];

export const demoIncidents: DemoIncident[] = [
  {
    id: "CE-24018",
    title: "Drainage overflow detected",
    location: "Ward 18, Bengaluru",
    issueType: "drainage_overflow",
    severity: "critical",
    confidence: 96,
    status: "Crew assigned",
    eta: "12 min",
    department: "Stormwater response"
  },
  {
    id: "CE-24019",
    title: "Road surface fracture",
    location: "MG Road corridor",
    issueType: "road_damage",
    severity: "high",
    confidence: 91,
    status: "AI verified",
    eta: "28 min",
    department: "Road maintenance"
  },
  {
    id: "CE-24020",
    title: "Garbage accumulation cluster",
    location: "Indiranagar 12th Main",
    issueType: "garbage",
    severity: "medium",
    confidence: 88,
    status: "Municipality review",
    eta: "42 min",
    department: "Solid waste"
  }
];

export const issueTypes = [
  { value: "pothole", label: "Pothole", icon: Route, severity: "high" },
  { value: "garbage", label: "Garbage", icon: Recycle, severity: "medium" },
  { value: "drainage_overflow", label: "Drain overflow", icon: Droplets, severity: "critical" },
  { value: "broken_streetlight", label: "Streetlight", icon: Zap, severity: "low" },
  { value: "water_leakage", label: "Water leakage", icon: Droplets, severity: "high" },
  { value: "road_damage", label: "Road damage", icon: AlertTriangle, severity: "high" }
] as const;

export const scanStages = [
  "Infrastructure detection",
  "Surface analysis",
  "Severity mapping",
  "Hazard classification",
  "Geo-context analysis",
  "Department routing",
  "Confidence scoring"
];

export const notifications = [
  { title: "Crew assigned", body: "Stormwater response accepted CE-24018.", time: "2m", icon: CheckCircle2 },
  { title: "AI verification complete", body: "Road damage confidence raised to 91%.", time: "8m", icon: Sparkles },
  { title: "SLA risk elevated", body: "Critical overflow approaching escalation window.", time: "14m", icon: AlertTriangle }
];
