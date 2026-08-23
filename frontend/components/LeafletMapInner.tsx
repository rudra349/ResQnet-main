"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { LocationSearch, GeoResult } from "./LocationSearch";
import { Maximize2 } from "lucide-react";

// Custom marker icons
const createCustomIcon = (color: string, label: string) => {
  return L.divIcon({
    className: "custom-leaflet-marker",
    html: `
      <div style="
        background-color: ${color};
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 0 10px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 10px;
        color: white;
      ">
        ${label}
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12],
  });
};

const icons = {
  critical: createCustomIcon("#ef4444", "!"),
  high: createCustomIcon("#f97316", "H"),
  medium: createCustomIcon("#eab308", "M"),
  shelter: createCustomIcon("#3b82f6", "S"),
  hospital: createCustomIcon("#10b981", "H"),
  team: createCustomIcon("#8b5cf6", "T"),
  searchedPin: createCustomIcon("#ec4899", "📍"),
};

interface MapProps {
  data?: {
    incidents: Array<{ id: string; type: string; severity: string; description: string; lat: number | null; lng: number | null }>;
    shelters: Array<{ id: string; name: string; capacity: number; occupancy: number; water_units: number; lat: number | null; lng: number | null }>;
    hospitals: Array<{ id: string; name: string; bed_available: number; bed_total: number; lat: number | null; lng: number | null }>;
    relief_teams: Array<{ id: string; name: string; status: string; lat: number | null; lng: number | null }>;
  };
}

export default function LeafletMapInner({ data }: MapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const searchedMarkerRef = useRef<L.Marker | null>(null);

  const [searchedGeo, setSearchedGeo] = useState<GeoResult | null>(null);

  const defaultCenter: [number, number] = [28.6139, 77.2090];

  // Collect all valid lat/lng points
  const allPoints: [number, number][] = [];
  data?.incidents.forEach((i) => { if (i.lat && i.lng) allPoints.push([i.lat, i.lng]); });
  data?.shelters.forEach((s) => { if (s.lat && s.lng) allPoints.push([s.lat, s.lng]); });
  data?.hospitals.forEach((h) => { if (h.lat && h.lng) allPoints.push([h.lat, h.lng]); });
  data?.relief_teams.forEach((t) => { if (t.lat && t.lng) allPoints.push([t.lat, t.lng]); });

  // 1. Initialize map once with robust cleanup
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(mapContainerRef.current, {
      center: defaultCenter,
      zoom: 13,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19,
    }).addTo(map);

    const markersGroup = L.layerGroup().addTo(map);
    markersLayerRef.current = markersGroup;
    mapInstanceRef.current = map;

    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 250);

    return () => {
      clearTimeout(timer);
      map.remove();
      mapInstanceRef.current = null;
      markersLayerRef.current = null;
      searchedMarkerRef.current = null;
    };
  }, []);

  // 2. Render data markers whenever data changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersGroup = markersLayerRef.current;
    if (!map || !markersGroup) return;

    markersGroup.clearLayers();

    // Incidents
    data?.incidents.forEach((inc) => {
      if (!inc.lat || !inc.lng) return;
      const icon = inc.severity === "critical" ? icons.critical : inc.severity === "high" ? icons.high : icons.medium;
      const marker = L.marker([inc.lat, inc.lng], { icon });
      marker.bindPopup(`
        <div class="text-xs">
          <div class="font-bold uppercase text-red-400 mb-1">Incident: ${inc.type}</div>
          <div class="text-slate-300 mb-1">${inc.description}</div>
          <div class="font-mono text-[10px] text-slate-400">Severity: ${inc.severity}</div>
        </div>
      `);
      markersGroup.addLayer(marker);
    });

    // Shelters
    data?.shelters.forEach((s) => {
      if (!s.lat || !s.lng) return;
      const marker = L.marker([s.lat, s.lng], { icon: icons.shelter });
      marker.bindPopup(`
        <div class="text-xs">
          <div class="font-bold text-blue-400 mb-1">Shelter: ${s.name}</div>
          <div class="text-slate-300">Occupancy: ${s.occupancy} / ${s.capacity}</div>
          <div class="text-slate-400">Water stock: ${s.water_units} units</div>
        </div>
      `);
      markersGroup.addLayer(marker);
    });

    // Hospitals
    data?.hospitals.forEach((h) => {
      if (!h.lat || !h.lng) return;
      const marker = L.marker([h.lat, h.lng], { icon: icons.hospital });
      marker.bindPopup(`
        <div class="text-xs">
          <div class="font-bold text-emerald-400 mb-1">Hospital: ${h.name}</div>
          <div class="text-slate-300">Beds available: ${h.bed_available} / ${h.bed_total}</div>
        </div>
      `);
      markersGroup.addLayer(marker);
    });

    // Relief Teams
    data?.relief_teams.forEach((t) => {
      if (!t.lat || !t.lng) return null;
      const marker = L.marker([t.lat, t.lng], { icon: icons.team });
      marker.bindPopup(`
        <div class="text-xs">
          <div class="font-bold text-purple-400 mb-1">Relief Team: ${t.name}</div>
          <div class="text-slate-300">Status: ${t.status}</div>
        </div>
      `);
      markersGroup.addLayer(marker);
    });
  }, [data]);

  // 3. Handle Searched Location Pin & FlyTo
  const handleSelectSearchedGeo = (geo: GeoResult | null) => {
    setSearchedGeo(geo);
    const map = mapInstanceRef.current;
    if (!map) return;

    if (searchedMarkerRef.current) {
      map.removeLayer(searchedMarkerRef.current);
      searchedMarkerRef.current = null;
    }

    if (geo) {
      const pin = L.marker([geo.lat, geo.lng], { icon: icons.searchedPin });
      pin.bindPopup(`
        <div class="text-xs">
          <div class="font-bold text-pink-400 mb-1">${geo.name}</div>
          <div class="text-slate-300 mb-1">${geo.formatted_address}</div>
          <div class="font-mono text-[10px] text-slate-400">${geo.lat.toFixed(5)}, ${geo.lng.toFixed(5)}</div>
        </div>
      `);
      pin.addTo(map);
      pin.openPopup();
      searchedMarkerRef.current = pin;

      map.flyTo([geo.lat, geo.lng], 14, { duration: 1.5 });
    }
  };

  // 4. Fit all points in bounds
  const handleFitAll = () => {
    const map = mapInstanceRef.current;
    if (!map || allPoints.length === 0) return;
    const bounds = L.latLngBounds(allPoints);
    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
  };

  return (
    <div className="w-full h-full min-h-[400px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative">
      {/* Map Search Control Overlay */}
      <div className="absolute top-3 left-3 z-[1000] w-72 sm:w-80 shadow-2xl">
        <LocationSearch
          value={searchedGeo}
          onChange={handleSelectSearchedGeo}
          placeholder="🔍 Search map location (e.g. YMCA Road)..."
        />
      </div>

      {/* Fit All Button Overlay */}
      {allPoints.length > 0 && (
        <button
          onClick={handleFitAll}
          className="absolute top-3 right-3 z-[1000] bg-[#0D121D]/90 backdrop-blur-md hover:bg-[#162032] border border-[#1E293B] text-slate-200 hover:text-white px-2.5 py-1.5 rounded-md text-xs font-mono font-semibold flex items-center gap-1.5 shadow-xl transition-colors cursor-pointer"
          title="Fit all markers in view"
        >
          <Maximize2 className="w-3.5 h-3.5 text-orange-400" />
          <span className="hidden sm:inline">Fit All Markers</span>
        </button>
      )}

      {/* Actual Map Container DIV */}
      <div ref={mapContainerRef} className="w-full h-full min-h-[400px]" />

      {/* Legend Overlay */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-slate-900/90 backdrop-blur-md p-2.5 rounded-lg border border-slate-800 text-[11px] text-slate-300 flex flex-wrap gap-3 shadow-xl">
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span><span>Critical</span></div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-orange-500 inline-block"></span><span>High</span></div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500 inline-block"></span><span>Shelter</span></div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span><span>Hospital</span></div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-purple-500 inline-block"></span><span>Relief Team</span></div>
        <div className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-pink-500 inline-block"></span><span>Searched Location</span></div>
      </div>
    </div>
  );
}
