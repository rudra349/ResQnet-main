"use client";

import { useState } from "react";
import { Navbar } from "@/components/Navbar";
import { AgentResponseCard } from "@/components/AgentResponse";
import { api } from "@/lib/axios";
import { AgentResponse } from "@/lib/types";
import {
  Bot,
  Send,
  Sparkles,
  Loader2,
  Terminal,
  Database,
  Radio,
  Search,
  CheckCircle2,
} from "lucide-react";

export default function AIAssistantPage() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const demoQueries = [
    "Where should we send 500 water bottles?",
    "How can Team 4 reach Shelter Alpha with Road 17 flooded?",
    "Where is water most urgently needed right now?",
    "Hospital Central is low on ICU beds — what is the recommended action?",
  ];

  const handleSend = async (queryText?: string) => {
    const q = queryText || message;
    if (!q.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await api.post("/agent/chat", { message: q });
      setResponse(res.data);
      if (!queryText) setMessage("");
    } catch (err: any) {
      console.error("Agent chat error:", err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
      setError(detail ? `AI Query Error: ${detail}` : "Failed to query AI Agent. Verify backend is running and Gemini API key is configured.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080B10] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-3 sm:px-6 py-6 space-y-4">
        {/* HEADER PANEL */}
        <div className="bg-[#0D121D] border border-[#1E293B] p-4 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded bg-cyan-950/80 border border-cyan-800 flex items-center justify-center text-cyan-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-wider uppercase flex items-center gap-2">
                <span>AI Operational Dispatch Assistant</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  SINGLE AGENT
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Autonomous tool calling loop • Vector retrieval against CockroachDB • Evidence-backed decisions
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 font-mono text-[11px] text-emerald-400 bg-[#111722] px-3 py-1.5 rounded border border-[#1E293B]">
            <Database className="w-3.5 h-3.5" />
            <span>PERSISTENT MEMORY LINK: READY</span>
          </div>
        </div>

        {/* HACKATHON DEMO QUERY CHIPS */}
        <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-3.5 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono font-bold text-orange-400">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>DISPATCH SCENARIO PRESETS:</span>
            </div>
            <span className="text-slate-500 font-normal">Click to trigger full vector retrieval loop</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {demoQueries.map((q, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setMessage(q);
                  handleSend(q);
                }}
                className="text-left p-2.5 rounded bg-[#111722] hover:bg-[#162032] border border-[#1E293B] text-slate-200 hover:text-white transition-all text-xs flex items-center justify-between group cursor-pointer"
              >
                <span className="font-mono text-[11px] truncate pr-2">{q}</span>
                <Send className="w-3 h-3 text-slate-500 group-hover:text-orange-400 transition-colors shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* COMMAND INPUT BAR */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <div className="relative flex-1">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 font-mono text-xs text-orange-500 font-bold select-none">
              &gt;
            </span>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Enter operational query (e.g., 'Where is drinking water available near Shelter Alpha?')..."
              className="w-full bg-[#0D121D] border border-[#1E293B] rounded-lg pl-8 pr-4 py-3 text-xs sm:text-sm font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className="px-4 sm:px-6 py-3 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white font-bold text-xs sm:text-sm font-mono flex items-center gap-2 transition-colors cursor-pointer shrink-0 shadow-sm"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            <span className="hidden sm:inline">Dispatch Query</span>
          </button>
        </form>

        {/* ERROR NOTICE */}
        {error && (
          <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs font-mono">
            [ERROR] {error}
          </div>
        )}

        {/* LOADING REASONING STATE */}
        {loading && (
          <div className="bg-[#0D121D] border border-[#1E293B] rounded-lg p-8 text-center space-y-3 font-mono">
            <Loader2 className="w-6 h-6 text-orange-500 animate-spin mx-auto" />
            <div className="text-xs font-bold text-slate-200">
              AGENT EXECUTING REASONING LOOP ACROSS COCKROACHDB...
            </div>
            <div className="text-[11px] text-slate-400">
              search_memories(768-D) ➔ search_incidents() ➔ search_resources() ➔ evaluate
            </div>
          </div>
        )}

        {/* RESPONSE COMPONENT */}
        {response && !loading && <AgentResponseCard response={response} />}
      </main>
    </div>
  );
}
