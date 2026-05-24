import { env } from "@/config/env";
import { markerColorForSeverity } from "@/lib/severity";
import type { CivicIncident } from "@/types/operations";

export type MapIncidentFeature = {
  type: "Feature";
  properties: {
    id: string;
    issueType: CivicIncident["issueType"];
    severity: CivicIncident["severity"];
    status: CivicIncident["lifecycleStatus"];
    color: string;
    confidenceScore: number;
  };
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
};

export type IncidentFeatureCollection = {
  type: "FeatureCollection";
  features: MapIncidentFeature[];
};

export function getMapboxToken() {
  return env.mapboxToken;
}

export function incidentsToGeoJson(incidents: CivicIncident[]): IncidentFeatureCollection {
  return {
    type: "FeatureCollection",
    features: incidents.map<MapIncidentFeature>((incident) => ({
      type: "Feature",
      properties: {
        id: incident.id,
        issueType: incident.issueType,
        severity: incident.severity,
        status: incident.lifecycleStatus,
        color: markerColorForSeverity(incident.severity),
        confidenceScore: incident.confidenceScore
      },
      geometry: {
        type: "Point",
        coordinates: [incident.geoCoordinates.longitude, incident.geoCoordinates.latitude]
      }
    }))
  };
}

export function buildHeatmapWeights(incidents: CivicIncident[]) {
  return incidents.map((incident) => ({
    id: incident.id,
    coordinates: incident.geoCoordinates,
    weight:
      incident.severity === "critical"
        ? 1
        : incident.severity === "high"
          ? 0.76
          : incident.severity === "medium"
            ? 0.48
            : 0.24
  }));
}
