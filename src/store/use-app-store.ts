"use client";

import { create } from "zustand";
import type { AuthSession } from "@/types/auth";
import type { CivicIssueType, CivicReport } from "@/types/civic";
import type { DemoScenarioId, ReplayState, ScenarioStage } from "@/types/demo";
import type { CivicIncident, CivicNotification, DashboardMetrics, OfflineQueueItem } from "@/types/operations";
import type { CivicRealtimeEvent, DistrictRiskForecast, FieldTeam, LiveTelemetrySnapshot, RealtimeConnectionStatus } from "@/types/realtime";

type ReportFlowState = {
  step: "capture" | "preview" | "scanning" | "result";
  selectedIssueType: CivicIssueType | null;
  scanStage: number;
  uploadPreviewUrl: string | null;
  uploadProgress: number;
  scanError: string | null;
  createdIncidentId: string | null;
};

type LoadingState = {
  dashboard: boolean;
  reports: boolean;
  upload: boolean;
  sync: boolean;
};

type AppState = {
  session: AuthSession | null;
  reports: CivicReport[];
  incidents: CivicIncident[];
  notifications: CivicNotification[];
  dashboardMetrics: DashboardMetrics | null;
  offlineQueue: OfflineQueueItem[];
  realtimeStatus: RealtimeConnectionStatus;
  realtimeEvents: CivicRealtimeEvent[];
  liveTelemetry: LiveTelemetrySnapshot | null;
  riskForecasts: DistrictRiskForecast[];
  fieldTeams: FieldTeam[];
  activeDemoScenarioId: DemoScenarioId;
  demoStage: ScenarioStage | null;
  presentationMode: boolean;
  replay: ReplayState;
  selectedReportId: string | null;
  onboardingStep: number;
  notificationsEnabled: boolean;
  locationEnabled: boolean;
  isOnline: boolean;
  loading: LoadingState;
  reportFlow: ReportFlowState;
  setSession: (session: AuthSession | null) => void;
  setReports: (reports: CivicReport[]) => void;
  setIncidents: (incidents: CivicIncident[]) => void;
  upsertIncident: (incident: CivicIncident) => void;
  setNotifications: (notifications: CivicNotification[]) => void;
  pushNotification: (notification: CivicNotification) => void;
  setDashboardMetrics: (metrics: DashboardMetrics | null) => void;
  setOfflineQueue: (queue: OfflineQueueItem[]) => void;
  setRealtimeStatus: (status: RealtimeConnectionStatus) => void;
  pushRealtimeEvent: (event: CivicRealtimeEvent) => void;
  setLiveTelemetry: (telemetry: LiveTelemetrySnapshot | null) => void;
  setRiskForecasts: (forecasts: DistrictRiskForecast[]) => void;
  setFieldTeams: (teams: FieldTeam[]) => void;
  setActiveDemoScenario: (scenarioId: DemoScenarioId) => void;
  setDemoStage: (stage: ScenarioStage | null) => void;
  setPresentationMode: (enabled: boolean) => void;
  setReplay: (replay: Partial<ReplayState>) => void;
  selectReport: (id: string | null) => void;
  setOnboardingStep: (step: number) => void;
  setNotificationsEnabled: (enabled: boolean) => void;
  setLocationEnabled: (enabled: boolean) => void;
  setOnline: (online: boolean) => void;
  setLoading: (loading: Partial<LoadingState>) => void;
  setReportFlow: (flow: Partial<ReportFlowState>) => void;
  resetReportFlow: () => void;
};

const initialReportFlow: ReportFlowState = {
  step: "capture",
  selectedIssueType: null,
  scanStage: 0,
  uploadPreviewUrl: null,
  uploadProgress: 0,
  scanError: null,
  createdIncidentId: null
};

const initialLoading: LoadingState = {
  dashboard: false,
  reports: false,
  upload: false,
  sync: false
};

export const useAppStore = create<AppState>((set) => ({
  session: null,
  reports: [],
  incidents: [],
  notifications: [],
  dashboardMetrics: null,
  offlineQueue: [],
  realtimeStatus: "idle",
  realtimeEvents: [],
  liveTelemetry: null,
  riskForecasts: [],
  fieldTeams: [],
  activeDemoScenarioId: "flood_emergency",
  demoStage: null,
  presentationMode: false,
  replay: {
    scenarioId: "flood_emergency",
    playing: false,
    cursorMs: 0,
    speed: 1
  },
  selectedReportId: null,
  onboardingStep: 0,
  notificationsEnabled: false,
  locationEnabled: false,
  isOnline: true,
  loading: initialLoading,
  reportFlow: initialReportFlow,
  setSession: (session) => set({ session }),
  setReports: (reports) => set({ reports }),
  setIncidents: (incidents) => set({ incidents }),
  upsertIncident: (incident) =>
    set((state) => ({
      incidents: state.incidents.some((item) => item.id === incident.id)
        ? state.incidents.map((item) => (item.id === incident.id ? incident : item))
        : [incident, ...state.incidents]
    })),
  setNotifications: (notifications) => set({ notifications }),
  pushNotification: (notification) => set((state) => ({ notifications: [notification, ...state.notifications] })),
  setDashboardMetrics: (dashboardMetrics) => set({ dashboardMetrics }),
  setOfflineQueue: (offlineQueue) => set({ offlineQueue }),
  setRealtimeStatus: (realtimeStatus) => set({ realtimeStatus }),
  pushRealtimeEvent: (event) => set((state) => ({ realtimeEvents: [event, ...state.realtimeEvents].slice(0, 80) })),
  setLiveTelemetry: (liveTelemetry) => set({ liveTelemetry }),
  setRiskForecasts: (riskForecasts) => set({ riskForecasts }),
  setFieldTeams: (fieldTeams) => set({ fieldTeams }),
  setActiveDemoScenario: (activeDemoScenarioId) =>
    set((state) => ({
      activeDemoScenarioId,
      replay: { ...state.replay, scenarioId: activeDemoScenarioId, cursorMs: 0, playing: false },
      demoStage: null
    })),
  setDemoStage: (demoStage) => set({ demoStage }),
  setPresentationMode: (presentationMode) => set({ presentationMode }),
  setReplay: (replay) => set((state) => ({ replay: { ...state.replay, ...replay } })),
  selectReport: (id) => set({ selectedReportId: id }),
  setOnboardingStep: (step) => set({ onboardingStep: step }),
  setNotificationsEnabled: (enabled) => set({ notificationsEnabled: enabled }),
  setLocationEnabled: (enabled) => set({ locationEnabled: enabled }),
  setOnline: (online) => set({ isOnline: online }),
  setLoading: (loading) => set((state) => ({ loading: { ...state.loading, ...loading } })),
  setReportFlow: (flow) => set((state) => ({ reportFlow: { ...state.reportFlow, ...flow } })),
  resetReportFlow: () => set({ reportFlow: initialReportFlow })
}));
