"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { MapPin, Search, X, Loader2, WifiOff, AlertCircle } from "lucide-react";

export interface GeoResult {
  place_id: string;
  display_name: string;
  name: string;
  formatted_address: string;
  lat: number;
  lng: number;
  city?: string;
  state?: string;
  country?: string;
}

interface Props {
  value: GeoResult | null;
  onChange: (result: GeoResult | null) => void;
  onMapFly?: (lat: number, lng: number) => void;
  placeholder?: string;
}

const NOMINATIM_URL = "https://nominatim.openstreetmap.org/search";
const MIN_QUERY_LEN = 3;
const DEBOUNCE_MS = 450;

function extractLabel(result: any): { name: string; secondary: string } {
  const parts: string[] = (result.display_name || "").split(",").map((s: string) => s.trim());
  return {
    name: parts.slice(0, 2).join(", "),
    secondary: parts.slice(2, 5).join(", "),
  };
}

export function LocationSearch({ value, onChange, onMapFly, placeholder }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeoResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [offline, setOffline] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [highlightIdx, setHighlightIdx] = useState(-1);

  useEffect(() => {
    setOffline(!navigator.onLine);
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, []);

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim() || q.trim().length < MIN_QUERY_LEN) {
      setResults([]);
      setOpen(false);
      return;
    }
    if (offline) return;

    // Cancel previous in-flight request
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        q: q.trim(),
        format: "json",
        addressdetails: "1",
        limit: "6",
        "accept-language": "en",
      });

      const res = await fetch(`${NOMINATIM_URL}?${params}`, {
        headers: { "User-Agent": "ResQNet/2.0 (Crisis Dispatch OS)" },
        signal: abortRef.current.signal,
      });

      if (!res.ok) throw new Error("Search failed");

      const data = await res.json();

      const parsed: GeoResult[] = data.map((r: any) => {
        const addr = r.address || {};
        return {
          place_id: String(r.place_id),
          display_name: r.display_name,
          name: r.name || r.display_name.split(",")[0].trim(),
          formatted_address: r.display_name,
          lat: parseFloat(r.lat),
          lng: parseFloat(r.lon),
          city: addr.city || addr.town || addr.village || addr.suburb || addr.county,
          state: addr.state,
          country: addr.country,
        };
      });

      setResults(parsed);
      setOpen(parsed.length > 0);
      setHighlightIdx(-1);
      if (parsed.length === 0) setError(null);
    } catch (err: any) {
      if (err.name === "AbortError") return;
      setError("Unable to search locations. Check your connection.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [offline]);

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setQuery(q);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!q.trim()) {
      setResults([]);
      setOpen(false);
      setError(null);
      return;
    }
    debounceRef.current = setTimeout(() => doSearch(q), DEBOUNCE_MS);
  };

  const handleSelect = (r: GeoResult) => {
    onChange(r);
    setQuery("");
    setResults([]);
    setOpen(false);
    setError(null);
    if (onMapFly) onMapFly(r.lat, r.lng);
  };

  const handleClear = () => {
    onChange(null);
    setQuery("");
    setResults([]);
    setOpen(false);
    setError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightIdx >= 0) handleSelect(results[highlightIdx]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  // If a location is already selected, show the selected state
  if (value) {
    const secondary = value.formatted_address.split(",").slice(1, 4).join(",").trim();
    return (
      <div className="bg-[#0B1220] border border-emerald-700/60 rounded-lg px-3 py-2.5 flex items-start justify-between gap-2 group">
        <div className="flex items-start gap-2 min-w-0">
          <MapPin className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="min-w-0">
            <div className="text-sm text-white font-medium truncate">{value.name}</div>
            {secondary && (
              <div className="text-[11px] text-slate-400 font-mono truncate">{secondary}</div>
            )}
            <div className="text-[10px] text-emerald-500/70 font-mono mt-0.5">
              {value.lat.toFixed(5)}, {value.lng.toFixed(5)}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={handleClear}
          className="shrink-0 w-6 h-6 rounded flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 transition-colors cursor-pointer mt-0.5"
          title="Clear location"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Search input */}
      <div className={`flex items-center bg-[#080B10] border rounded-lg px-3 py-2.5 gap-2 transition-colors ${
        error ? "border-red-700" : open ? "border-orange-500" : "border-[#1E293B] focus-within:border-orange-500"
      }`}>
        {loading ? (
          <Loader2 className="w-4 h-4 text-orange-400 shrink-0 animate-spin" />
        ) : offline ? (
          <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
        ) : (
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
        )}
        <input
          type="text"
          value={query}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={
            offline
              ? "Location search requires internet connection"
              : placeholder ?? "Search city, area, road, landmark or address…"
          }
          disabled={offline}
          className="flex-1 bg-transparent text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
          autoComplete="off"
          spellCheck={false}
        />
        {query && (
          <button
            type="button"
            onClick={() => { setQuery(""); setResults([]); setOpen(false); setError(null); }}
            className="shrink-0 text-slate-500 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Geolocation Button */}
      {!offline && !query && (
        <button
          type="button"
          onClick={() => {
            if ("geolocation" in navigator) {
              setLoading(true);
              navigator.geolocation.getCurrentPosition(
                async (pos) => {
                  const { latitude: lat, longitude: lng } = pos.coords;
                  try {
                    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`, {
                      headers: { "User-Agent": "ResQNet/2.0" }
                    });
                    const data = await res.json();
                    handleSelect({
                      place_id: String(data.place_id || Date.now()),
                      display_name: data.display_name || `Current Location (${lat.toFixed(4)}, ${lng.toFixed(4)})`,
                      name: data.name || data.address?.road || data.address?.suburb || "Current Location",
                      formatted_address: data.display_name || `Coordinates: ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
                      lat,
                      lng,
                      city: data.address?.city || data.address?.town || data.address?.county,
                      state: data.address?.state,
                      country: data.address?.country
                    });
                  } catch {
                    handleSelect({
                      place_id: String(Date.now()),
                      display_name: `Current GPS Position (${lat.toFixed(4)}, ${lng.toFixed(4)})`,
                      name: "GPS Location",
                      formatted_address: `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`,
                      lat,
                      lng
                    });
                  } finally {
                    setLoading(false);
                  }
                },
                (err) => {
                  setLoading(false);
                  setError("Geolocation permission denied or unavailable.");
                }
              );
            } else {
              setError("Geolocation not supported by browser.");
            }
          }}
          className="mt-1.5 flex items-center gap-1.5 text-[11px] font-mono text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer"
        >
          <MapPin className="w-3 h-3 animate-bounce" />
          <span>Use my current GPS location</span>
        </button>
      )}

      {/* Error */}
      {error && !open && (
        <div className="mt-1.5 flex items-center gap-1.5 text-[11px] font-mono text-red-400">
          <AlertCircle className="w-3 h-3 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Min length hint */}
      {query.length > 0 && query.length < MIN_QUERY_LEN && !loading && (
        <div className="mt-1.5 text-[11px] font-mono text-slate-500">
          Type at least {MIN_QUERY_LEN} characters to search…
        </div>
      )}

      {/* No results */}
      {open && results.length === 0 && !loading && query.length >= MIN_QUERY_LEN && (
        <div className="absolute z-[9999] w-full mt-1 bg-[#0D121D] border border-[#1E293B] rounded-lg shadow-2xl px-4 py-3 text-xs font-mono text-slate-400">
          No locations found for &quot;{query}&quot;
        </div>
      )}

      {/* Results dropdown */}
      {open && results.length > 0 && (
        <ul className="absolute z-[9999] w-full mt-1 bg-[#0D121D] border border-[#1E293B] rounded-lg shadow-2xl overflow-hidden max-h-72 overflow-y-auto">
          {results.map((r, idx) => {
            const { name, secondary } = extractLabel(r);
            return (
              <li key={`${r.place_id}-${idx}`}>
                <button
                  type="button"
                  onMouseDown={(e) => { e.preventDefault(); handleSelect(r); }}
                  onMouseEnter={() => setHighlightIdx(idx)}
                  className={`w-full text-left px-3.5 py-2.5 flex items-start gap-2.5 transition-colors border-b border-[#1E293B] last:border-b-0 cursor-pointer ${
                    highlightIdx === idx ? "bg-[#162032]" : "hover:bg-[#111722]"
                  }`}
                >
                  <MapPin className="w-3.5 h-3.5 text-orange-400 shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <div className="text-sm text-white font-medium truncate">{name}</div>
                    {secondary && (
                      <div className="text-[11px] text-slate-400 font-mono truncate mt-0.5">{secondary}</div>
                    )}
                  </div>
                </button>
              </li>
            );
          })}
          <li className="px-3.5 py-1.5 text-[10px] font-mono text-slate-600 bg-[#080B10]">
            © OpenStreetMap contributors · Nominatim
          </li>
        </ul>
      )}
    </div>
  );
}
