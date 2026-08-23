"use client";

import { useEffect, useState } from "react";
import { Database, Wifi, Bot, ShieldCheck, Activity, Radio, Layers, HardDrive } from "lucide-react";

export function SystemTelemetryBar() {
  const [currentTime, setCurrentTime] = useState<string>("");
  const [online, setOnline] = useState<boolean>(true);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString("en-US", { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);

    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    setOnline(navigator.onLine);

    return () => {
      clearInterval(interval);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return (
    <div className="w-full bg-[#080B10] border-b border-[#1E293B] px-3 py-1.5 flex flex-wrap items-center justify-between text-[11px] font-mono tracking-tight text-slate-400 select-none">
      {/* Left: Mission / Host info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-slate-200 font-bold tracking-wider">
          <Radio className="w-3.5 h-3.5 text-orange-500 animate-pulse" />
          <span>RESQNET OS</span>
          <span className="text-[9px] px-1 py-0.2 rounded bg-orange-950/80 text-orange-400 border border-orange-800">
            v2.4 CRX
          </span>
        </div>
        <span className="hidden sm:inline text-slate-700">|</span>
        <span className="hidden sm:inline text-slate-500">REGION ALPHA COMMAND</span>
      </div>

      {/* Center: Live Telemetry Telemetry items */}
      <div className="flex items-center gap-3 sm:gap-5 overflow-x-auto py-0.5">
        <div className="flex items-center gap-1.5">
          <Database className="w-3 h-3 text-emerald-400" />
          <span className="text-slate-500">DB:</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-ping" />
            COCKROACHDB [768-D]
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Bot className="w-3 h-3 text-cyan-400" />
          <span className="text-slate-500">AI AGENT:</span>
          <span className="text-cyan-400 font-semibold">GEMINI 3.6 FLASH</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Wifi className={`w-3 h-3 ${online ? "text-emerald-400" : "text-amber-400"}`} />
          <span className="text-slate-500">LINK:</span>
          <span className={online ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
            {online ? "ONLINE" : "OFFLINE (IDB ACTIVE)"}
          </span>
        </div>
      </div>

      {/* Right: Real-time clock */}
      <div className="hidden md:flex items-center gap-2 text-slate-300">
        <Activity className="w-3.5 h-3.5 text-orange-400" />
        <span className="text-slate-400 font-semibold">UTC {currentTime || "00:00:00"}</span>
      </div>
    </div>
  );
}
