"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SyncBadge } from "./SyncBadge";
import { Shield, AlertOctagon, Bot, PlusCircle, Package, Database } from "lucide-react";

import { SystemTelemetryBar } from "./SystemTelemetryBar";

export function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Command Center", icon: Shield },
    { href: "/report", label: "Report Incident", icon: PlusCircle },
    { href: "/resources", label: "Inventory", icon: Package },
    { href: "/ai", label: "AI Operator", icon: Bot },
    { href: "/alerts", label: "Alerts", icon: AlertOctagon },
    { href: "/queue", label: "Sync Queue", icon: Database },
  ];

  return (
    <div className="sticky top-0 z-50">
      <SystemTelemetryBar />
      <header className="bg-[#0D121D]/95 backdrop-blur-md border-b border-[#1E293B]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-orange-600 flex items-center justify-center font-bold text-white shadow-lg shadow-orange-600/30">
              R
            </div>
            <div>
              <span className="font-extrabold tracking-wider text-lg text-white">RESQ<span className="text-orange-500">NET</span></span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Persistent Memory
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? "bg-slate-800 text-orange-400 border border-slate-700 shadow-sm"
                      : "text-slate-300 hover:bg-slate-900 hover:text-white"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-orange-400" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Status Badge */}
          <div className="flex items-center gap-3">
            <SyncBadge />
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <nav className="md:hidden flex items-center justify-around py-2 border-t border-slate-900 overflow-x-auto text-xs">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center gap-1 px-2.5 py-1 rounded text-[11px] ${
                  isActive ? "text-orange-400 font-bold" : "text-slate-400"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
    </div>
  );
}
