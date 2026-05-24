"use client";

import { useEffect, useMemo, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { Activity, AlertTriangle, Cpu, Layers, RadioTower, Route } from "lucide-react";
import { motion } from "framer-motion";
import { getMapboxToken } from "@/services/maps/mapbox-service";
import type { MapIntelligence, MapIncidentFeature } from "@/types/enterprise";

type EnterpriseCommandMapProps = {
  intelligence: MapIntelligence;
};

const severityColor: Record<MapIncidentFeature["severity"], string> = {
  LOW: "#34D399",
  MEDIUM: "#FBBF24",
  HIGH: "#38BDF8",
  CRITICAL: "#FB7185"
};

export function EnterpriseCommandMap({ intelligence }: EnterpriseCommandMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const popupRef = useRef<mapboxgl.Popup | null>(null);
  const token = getMapboxToken();
  const center = useMemo<[number, number]>(() => {
    const first = intelligence.incidents[0];
    return first ? [first.longitude, first.latitude] : [77.5946, 12.9716];
  }, [intelligence.incidents]);

  useEffect(() => {
    if (!containerRef.current || !token || mapRef.current) {
      return;
    }
    mapboxgl.accessToken = token;
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center,
      zoom: 11.6,
      pitch: 52,
      bearing: -18,
      attributionControl: false
    });
    mapRef.current.addControl(new mapboxgl.NavigationControl({ visualizePitch: true }), "bottom-right");
    popupRef.current = new mapboxgl.Popup({ closeButton: false, closeOnClick: true, className: "civiceye-map-popup" });
    return () => {
      popupRef.current?.remove();
      mapRef.current?.remove();
      mapRef.current = null;
      popupRef.current = null;
    };
  }, [center, token]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !token) {
      return;
    }
    const incidentsGeoJson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: intelligence.incidents.map((incident) => ({
        type: "Feature",
        properties: {
          id: incident.incident_id,
          code: incident.incident_code,
          severity: incident.severity,
          status: incident.status,
          confidence: incident.confidence,
          district: incident.district ?? "Unassigned",
          department: incident.assigned_department ?? "Unassigned",
          sla: incident.sla_due_at,
          detected: incident.detected_at,
          color: severityColor[incident.severity]
        },
        geometry: { type: "Point", coordinates: [incident.longitude, incident.latitude] }
      }))
    };
    const districtsGeoJson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: intelligence.districts
        .filter((district) => district.boundary_geojson)
        .map((district) => ({
          type: "Feature",
          properties: {
            id: district.district_id,
            name: district.name,
            degradation: district.degradation_score,
            incidentCount: district.incident_count,
            criticalCount: district.critical_count,
            slaRiskCount: district.sla_risk_count
          },
          geometry: district.boundary_geojson as GeoJSON.Geometry
        }))
    };
    const workersGeoJson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features: intelligence.worker_telemetry
        .filter((worker) => typeof worker.longitude === "number" && typeof worker.latitude === "number")
        .map((worker) => ({
          type: "Feature",
          properties: { id: String(worker.id), name: String(worker.name ?? "Crew"), battery: Number(worker.battery_percent ?? 0) },
          geometry: { type: "Point", coordinates: [Number(worker.longitude), Number(worker.latitude)] }
        }))
    };

    function syncLayers(current: mapboxgl.Map) {
      if (!current.getSource("enterprise-incidents")) {
        current.addSource("enterprise-incidents", { type: "geojson", data: incidentsGeoJson, cluster: true, clusterMaxZoom: 14, clusterRadius: 46 });
        current.addSource("district-overlays", { type: "geojson", data: districtsGeoJson });
        current.addSource("field-workers", { type: "geojson", data: workersGeoJson });
        current.addLayer({
          id: "district-risk-fill",
          type: "fill",
          source: "district-overlays",
          paint: {
            "fill-color": ["interpolate", ["linear"], ["get", "degradation"], 0, "rgba(52,211,153,0.08)", 55, "rgba(56,189,248,0.12)", 80, "rgba(251,113,133,0.2)"],
            "fill-outline-color": "rgba(125,211,252,0.46)"
          }
        });
        current.addLayer({
          id: "incident-density",
          type: "heatmap",
          source: "enterprise-incidents",
          maxzoom: 15,
          paint: {
            "heatmap-weight": ["interpolate", ["linear"], ["get", "confidence"], 0, 0, 1, 1],
            "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 0.5, 15, 1.7],
            "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 8, 14, 15, 38],
            "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(0,0,0,0)", 0.35, "#0EA5E9", 0.68, "#FBBF24", 1, "#FB7185"]
          }
        });
        current.addLayer({
          id: "incident-pulse",
          type: "circle",
          source: "enterprise-incidents",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 10, 15, 18],
            "circle-color": ["get", "color"],
            "circle-opacity": 0.18,
            "circle-stroke-width": 1,
            "circle-stroke-color": ["get", "color"],
            "circle-stroke-opacity": 0.95
          }
        });
        current.addLayer({
          id: "incident-points-live",
          type: "circle",
          source: "enterprise-incidents",
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 5, 15, 9],
            "circle-color": ["get", "color"],
            "circle-opacity": 0.96,
            "circle-stroke-width": 2,
            "circle-stroke-color": "rgba(255,255,255,0.86)"
          }
        });
        current.addLayer({
          id: "cluster-counts",
          type: "symbol",
          source: "enterprise-incidents",
          filter: ["has", "point_count"],
          layout: { "text-field": ["get", "point_count_abbreviated"], "text-size": 12 },
          paint: { "text-color": "#E0F2FE" }
        });
        current.addLayer({
          id: "field-workers-live",
          type: "circle",
          source: "field-workers",
          paint: {
            "circle-radius": 7,
            "circle-color": "#34D399",
            "circle-stroke-color": "#ECFEFF",
            "circle-stroke-width": 2
          }
        });
        current.on("click", "incident-points-live", (event) => {
          const feature = event.features?.[0];
          if (!feature || feature.geometry.type !== "Point") {
            return;
          }
          const coordinates = feature.geometry.coordinates as [number, number];
          const props = feature.properties ?? {};
          popupRef.current
            ?.setLngLat(coordinates)
            .setHTML(
              `<div class="space-y-2 text-slate-100"><div class="text-xs uppercase tracking-[0.18em] text-cyan-200">${props.code}</div><div class="text-sm font-semibold">${props.severity} ${props.status}</div><div class="text-xs text-slate-300">AI ${Math.round(Number(props.confidence) * 100)}% · ${props.district}</div><div class="text-xs text-slate-300">${props.department} · SLA ${new Date(String(props.sla)).toLocaleString()}</div></div>`
            )
            .addTo(current);
        });
      } else {
        (current.getSource("enterprise-incidents") as mapboxgl.GeoJSONSource).setData(incidentsGeoJson);
        (current.getSource("district-overlays") as mapboxgl.GeoJSONSource).setData(districtsGeoJson);
        (current.getSource("field-workers") as mapboxgl.GeoJSONSource).setData(workersGeoJson);
      }
    }
    if (map.loaded()) {
      syncLayers(map);
    } else {
      map.once("load", () => syncLayers(map));
    }
  }, [intelligence, token]);

  if (!token) {
    return <MapFallback intelligence={intelligence} />;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_22rem]">
      <div ref={containerRef} className="min-h-[42rem] overflow-hidden rounded-lg border border-white/10 shadow-[0_28px_100px_rgba(0,0,0,0.36)]" />
      <TelemetryRail intelligence={intelligence} />
    </div>
  );
}

function MapFallback({ intelligence }: EnterpriseCommandMapProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_22rem]">
      <div className="relative min-h-[42rem] overflow-hidden rounded-lg border border-white/10 bg-[#040912] p-5">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(14,165,233,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(14,165,233,0.12)_1px,transparent_1px)] bg-[size:34px_34px]" />
        {intelligence.heatmap_points.slice(0, 24).map((point, index) => (
          <motion.div
            key={point.incident_id}
            className="absolute rounded-full border border-cyan-200/40 bg-cyan-300/20 shadow-[0_0_28px_rgba(34,211,238,0.36)]"
            style={{ left: `${16 + (index % 6) * 13}%`, top: `${18 + Math.floor(index / 6) * 17}%`, width: 16 + point.weight * 34, height: 16 + point.weight * 34 }}
            animate={{ scale: [1, 1.28, 1], opacity: [0.42, 0.88, 0.42] }}
            transition={{ duration: 2.4, repeat: Infinity, delay: index * 0.08 }}
          />
        ))}
        <div className="relative max-w-md">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-200/80">Live GIS fallback</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">Mapbox token required for full digital twin</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">The same persisted incidents, district overlays, repairs, and worker telemetry are loaded. Add `NEXT_PUBLIC_MAPBOX_TOKEN` for live clustering and vector layers.</p>
        </div>
      </div>
      <TelemetryRail intelligence={intelligence} />
    </div>
  );
}

function TelemetryRail({ intelligence }: EnterpriseCommandMapProps) {
  const critical = intelligence.incidents.filter((incident) => incident.severity === "CRITICAL").length;
  const slaRisk = intelligence.incidents.filter((incident) => new Date(incident.sla_due_at).getTime() - Date.now() < 6 * 3600000).length;
  return (
    <div className="grid gap-3">
      <RailMetric icon={AlertTriangle} label="Critical incidents" value={critical} />
      <RailMetric icon={Route} label="Active repairs" value={intelligence.active_repairs.length} />
      <RailMetric icon={RadioTower} label="Field telemetry" value={intelligence.worker_telemetry.length} />
      <RailMetric icon={Cpu} label="SLA risk" value={slaRisk} />
      <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Layers className="size-4 text-cyan-300" />
          District degradation
        </div>
        <div className="mt-4 grid gap-3">
          {intelligence.districts.slice(0, 6).map((district) => (
            <div key={district.district_id}>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300">{district.name}</span>
                <span className="text-cyan-200">{Math.round(district.degradation_score)}</span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
                <div className="h-full rounded-full bg-cyan-300" style={{ width: `${Math.min(100, district.degradation_score)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RailMetric({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        <Icon className="size-4 text-cyan-300" />
      </div>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}
