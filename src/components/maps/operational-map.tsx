"use client";

import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { getMapboxToken, incidentsToGeoJson } from "@/services/maps/mapbox-service";
import type { CivicIncident } from "@/types/operations";
import type { DistrictRiskForecast, FieldTeam } from "@/types/realtime";

type OperationalMapProps = {
  incidents: CivicIncident[];
  forecasts?: DistrictRiskForecast[];
  fieldTeams?: FieldTeam[];
};

export function OperationalMap({ incidents, forecasts = [], fieldTeams = [] }: OperationalMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const token = getMapboxToken();

  useEffect(() => {
    if (!containerRef.current || !token || mapRef.current) {
      return;
    }

    mapboxgl.accessToken = token;
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [77.5946, 12.9716],
      zoom: 11.5,
      attributionControl: false
    });

    mapRef.current.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "bottom-right");

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [token]);

  useEffect(() => {
    const currentMap = mapRef.current;
    if (!currentMap || !token) {
      return;
    }

    const geoJson = incidentsToGeoJson(incidents);

    function syncLayers(map: mapboxgl.Map) {
      if (!map.getSource("incidents")) {
        map.addSource("incidents", {
          type: "geojson",
          data: geoJson,
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 48
        });

        map.addLayer({
          id: "incident-heat",
          type: "heatmap",
          source: "incidents",
          maxzoom: 15,
          paint: {
            "heatmap-weight": ["interpolate", ["linear"], ["get", "confidenceScore"], 0, 0, 1, 1],
            "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 0.7, 15, 1.3],
            "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(0,0,0,0)", 0.35, "#4F8CFF", 0.65, "#00D4FF", 1, "#FB7185"],
            "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 12, 15, 32]
          }
        });

        map.addLayer({
          id: "incident-points",
          type: "circle",
          source: "incidents",
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 8, 15, 14],
            "circle-color": ["get", "color"],
            "circle-opacity": 0.92,
            "circle-stroke-width": 2,
            "circle-stroke-color": "rgba(255,255,255,0.82)"
          }
        });

        map.addSource("risk-zones", {
          type: "geojson",
          data: {
            type: "FeatureCollection",
            features: forecasts.map((forecast, index) => ({
              type: "Feature",
              properties: {
                id: forecast.districtId,
                riskScore: forecast.riskScore
              },
              geometry: {
                type: "Point",
                coordinates: [77.5946 + index * 0.018, 12.9716 + index * 0.012]
              }
            }))
          }
        });

        map.addLayer({
          id: "risk-zone-pulses",
          type: "circle",
          source: "risk-zones",
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["get", "riskScore"], 0, 18, 100, 54],
            "circle-color": "#8B5CF6",
            "circle-opacity": 0.16,
            "circle-stroke-color": "#00D4FF",
            "circle-stroke-width": 1
          }
        });
      } else {
        const source = map.getSource("incidents") as mapboxgl.GeoJSONSource;
        source.setData(geoJson);
        const riskSource = map.getSource("risk-zones") as mapboxgl.GeoJSONSource | undefined;
        riskSource?.setData({
          type: "FeatureCollection",
          features: forecasts.map((forecast, index) => ({
            type: "Feature",
            properties: {
              id: forecast.districtId,
              riskScore: forecast.riskScore
            },
            geometry: {
              type: "Point",
              coordinates: [77.5946 + index * 0.018, 12.9716 + index * 0.012]
            }
          }))
        });
      }
    }

    if (currentMap.loaded()) {
      syncLayers(currentMap);
    } else {
      currentMap.once("load", () => syncLayers(currentMap));
    }
  }, [forecasts, incidents, token]);

  if (!token) {
    return (
      <div className="relative min-h-[34rem] overflow-hidden rounded-[2rem] border border-white/10 bg-[#06101f] p-5 backdrop-blur-2xl">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_38%_24%,rgba(0,212,255,0.2),transparent_28%),radial-gradient(circle_at_70%_72%,rgba(139,92,246,0.18),transparent_28%)]" />
        <div className="city-grid absolute inset-x-[-25%] bottom-[-20%] h-[80%] opacity-75" />
        <div className="relative">
          <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Mapbox-ready</p>
          <h2 className="mt-1 text-2xl font-semibold text-white">Operational heat layer</h2>
          <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">Add NEXT_PUBLIC_MAPBOX_TOKEN to activate live Mapbox clustering, heatmaps, and issue markers.</p>
        </div>
        {forecasts.map((forecast, index) => (
          <div
            key={forecast.districtId}
            className="absolute rounded-full border border-civic-purple/30 bg-civic-purple/10"
            style={{
              left: `${18 + index * 22}%`,
              top: `${34 + (index % 2) * 18}%`,
              width: 70 + forecast.riskScore * 0.45,
              height: 70 + forecast.riskScore * 0.45
            }}
          />
        ))}
        {fieldTeams.map((team, index) => (
          <div
            key={team.id}
            className="absolute rounded-xl border border-civic-success/30 bg-civic-success/15 px-2 py-1 text-[10px] font-semibold text-civic-success"
            style={{ left: `${28 + index * 18}%`, top: `${66 - index * 8}%` }}
          >
            {team.etaMinutes ? `${team.etaMinutes}m` : "ready"}
          </div>
        ))}
        {incidents.map((incident, index) => (
          <div
            key={incident.id}
            className="absolute rounded-full shadow-glow"
            style={{
              left: `${22 + index * 24}%`,
              top: `${42 + (index % 2) * 18}%`,
              width: 14,
              height: 14,
              backgroundColor: incident.severity === "critical" ? "#FB7185" : incident.severity === "high" ? "#4F8CFF" : "#00D4FF"
            }}
          >
            <span className="absolute -inset-5 animate-ping rounded-full bg-civic-cyan/20" />
          </div>
        ))}
      </div>
    );
  }

  return <div ref={containerRef} className="min-h-[34rem] overflow-hidden rounded-[2rem] border border-white/10 shadow-[0_28px_100px_rgba(0,0,0,0.36)]" />;
}
