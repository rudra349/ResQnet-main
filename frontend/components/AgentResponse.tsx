"use client";

import { useState } from "react";
import { AgentResponse as AgentResponseType } from "@/lib/types";
import {
  Brain,
  CheckCircle2,
  Database,
  ChevronDown,
  ChevronUp,
  Cpu,
  Layers,
  Sparkles,
  Search,
  FileText,
  Radio,
} from "lucide-react";

interface Props {
  response: AgentResponseType;
}

export function AgentResponseCard({ response }: Props) {
  const [showMemories, setShowMemories] = useState(true);

  const confidencePct = Math.round(response.confidence * 100);
  const confidenceColor =
    confidencePct >= 80
      ? "text-emerald-400 border-emerald-800 bg-emerald-950/60"
      : confidencePct >= 50
      ? "text-amber-400 border-amber-800 bg-amber-950/60"
      : "text-red-400 border-red-800 bg-red-950/60";

  return (
    <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-4 space-y-4 shadow-xl font-sans">
      {/* CARD TELEMETRY HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E293B] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded bg-cyan-950 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
            <Cpu className="w-4 h-4 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm tracking-wide">
              OPERATIONAL AI DISPATCH REPORT
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              Trace ID: #{response.request_id.substring(0, 8)} • Model: Gemini 3.6 Flash
            </span>
          </div>
        </div>

        <div className={`px-2.5 py-1 rounded border text-xs font-mono font-bold flex items-center gap-1.5 self-start sm:self-auto ${confidenceColor}`}>
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>CONFIDENCE: {confidencePct}%</span>
        </div>
      </div>

      {/* TOOLS INVOCATION CHAIN */}
      {response.tools_used && response.tools_used.length > 0 && (
        <div className="bg-[#111722] border border-[#1E293B] rounded p-2.5 space-y-1.5">
          <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Search className="w-3 h-3 text-cyan-400" />
            <span>Executed Agent Tool Chain ({response.tools_used.length}):</span>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {response.tools_used.map((tool, idx) => (
              <span
                key={idx}
                className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1A2333] text-cyan-300 border border-cyan-800/60 flex items-center gap-1"
              >
                <span>{idx + 1}.</span>
                <span>{tool}()</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* STRUCTURED RESPONSE BODY */}
      <div className="bg-[#080B10] border border-[#1E293B] p-3.5 rounded text-xs text-slate-200 leading-relaxed font-sans whitespace-pre-line space-y-2">
        {response.answer}
      </div>

      {/* RETRIEVED COCKROACHDB MEMORY TRAIL */}
      {response.memories_retrieved && response.memories_retrieved.length > 0 && (
        <div className="bg-[#111722] border border-[#1E293B] rounded overflow-hidden">
          <button
            onClick={() => setShowMemories(!showMemories)}
            className="w-full px-3.5 py-2 flex items-center justify-between text-xs font-mono text-slate-300 hover:bg-[#162032] transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-bold text-emerald-400">
                COCKROACHDB VECTOR EVIDENCE ({response.memories_retrieved.length} RETRIEVED)
              </span>
            </div>
            {showMemories ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {showMemories && (
            <div className="p-3 border-t border-[#1E293B] space-y-2 max-h-60 overflow-y-auto">
              {response.memories_retrieved.map((mem, idx) => (
                <div
                  key={mem.id || idx}
                  className="bg-[#080B10] p-2.5 rounded border border-[#1E293B] text-xs space-y-1"
                >
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span className="text-orange-400 font-bold uppercase">
                      ● {mem.type} MEMORY [{mem.id ? mem.id.substring(0, 8) : "N/A"}]
                    </span>
                    <span>
                      {mem.created_at
                        ? new Date(mem.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "Committed"}
                    </span>
                  </div>
                  <p className="text-slate-300 text-xs leading-normal">{mem.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
