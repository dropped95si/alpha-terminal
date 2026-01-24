"use client";

import React, { useEffect, useMemo, useState } from "react";

type Candidate = {
  ticker: string;
  label: string;
  plan_type?: string;
  rs_vs_spy?: number | null;
  vol_z?: number | null;
  scan_run_id?: string | null;
  signal_id?: string | null;
  already_labeled_today?: boolean;
};

type Timeframe = "intraday" | "swing" | "position";
type ExitIntent =
  | "before_last_high"
  | "partial_then_runner"
  | "hard_stop_only"
  | "trailing_stop"
  | "decide_live";

type IdeaSource = "scanner" | "memory" | "news_attention" | "instinct";
type Mode = "conservative" | "aggressive";

const entryOptions = [
  "fib_retracement_bounce",
  "volume_shelf",
  "breakout_reclaim",
  "ma_or_ema_cross",
  "flag_or_pennant",
  "support_resistance",
  "trendline_break",
  "mean_reversion_to_vwap",
] as const;

export default function TeachPage() {
  const [token, setToken] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [asOf, setAsOf] = useState<string | null>(null);

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [idx, setIdx] = useState(0);

  // label form state
  const [mode, setMode] = useState<Mode>("conservative");
  const [ideaSource, setIdeaSource] = useState<IdeaSource>("scanner");
  const [timeframe, setTimeframe] = useState<Timeframe>("swing");
  const [exitIntent, setExitIntent] = useState<ExitIntent>("before_last_high");
  const [entryReasons, setEntryReasons] = useState<string[]>([]);
  const [confidence, setConfidence] = useState<number>(7);
  const [notes, setNotes] = useState("");

  const [saving, setSaving] = useState(false);
  const c = useMemo(() => candidates[idx] ?? null, [candidates, idx]);

  function resetFormForNext() {
    setEntryReasons([]);
    setConfidence(7);
    setNotes("");
    // keep mode/timeframe/exitIntent sticky so you can label fast
  }

  function toggleReason(r: string) {
    setEntryReasons((prev) => {
      if (prev.includes(r)) return prev.filter((x) => x !== r);
      if (prev.length >= 2) return prev; // cap at 2
      return [...prev, r];
    });
  }

  async function loadCandidates(tok: string) {
    const t = tok?.trim();
    if (!t) return;

    const res = await fetch("/api/teach/candidates", {
      headers: { Authorization: `Bearer ${t}` },
    });

    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      throw new Error(j?.error || `Load failed (${res.status})`);
    }

    const j = await res.json();
    setAsOf(j.as_of ?? null);
    setCandidates(j.candidates ?? []);
    setIdx(0);
    setLoaded(true);
    resetFormForNext();
  }

  async function saveLabel() {
    if (!c) return;
    const t = token.trim();
    if (!t) return alert("Paste TEACH_TOKEN first.");

    setSaving(true);
    try {
      const body = {
        ticker: c.ticker,
        mode,
        idea_source: ideaSource,
        timeframe,
        exit_intent: exitIntent,
        entry_reasons: entryReasons,
        confidence,
        notes: notes || null,
        scan_run_id: c.scan_run_id ?? null,
        signal_id: c.signal_id ?? null,
      };

      const res = await fetch("/api/teach/label", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${t}`,
        },
        body: JSON.stringify(body),
      });

      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j?.error || `Save failed (${res.status})`);

      // go next (or reload if at end)
      if (idx < candidates.length - 1) setIdx((x) => x + 1);
      else await loadCandidates(t);

      resetFormForNext();
    } catch (e: any) {
      alert(e?.message || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  // auto-load token from localStorage
  useEffect(() => {
    const t = localStorage.getItem("TEACH_TOKEN");
    if (t) setToken(t);
  }, []);

  // keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Enter") saveLabel();
      if (e.key === "ArrowLeft") setIdx((x) => Math.max(x - 1, 0));
      if (e.key === "ArrowRight") setIdx((x) => Math.min(x + 1, candidates.length - 1));
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [candidates.length, idx, token, mode, ideaSource, timeframe, exitIntent, entryReasons, confidence, notes, c]);

  // ✅ IMPORTANT: returns must be inside THIS component
  if (!loaded) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold tracking-tight">
            Teach Mode <span className="text-cyan-400">v1</span>
          </h1>

          <div className="mt-6 flex items-center gap-2">
            <input
              className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm w-[360px]"
              placeholder="Paste TEACH_TOKEN once"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <button
              className="bg-cyan-500 hover:bg-cyan-400 text-black font-semibold px-4 py-2 rounded"
              onClick={async () => {
                localStorage.setItem("TEACH_TOKEN", token);
                await loadCandidates(token);
              }}
            >
              Load 10
            </button>
          </div>

          <div className="mt-6 text-zinc-400 text-sm">
            No candidates loaded yet.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-end justify-between gap-4 mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Teach Mode <span className="text-cyan-400">v1</span>
            </h1>
            <div className="text-sm text-zinc-400">
              {asOf ? <>Latest scan: <span className="text-zinc-200">{asOf}</span></> : "Loaded"}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              className="bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm w-[320px]"
              placeholder="Paste TEACH_TOKEN once"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
            <button
              className="bg-cyan-500 hover:bg-cyan-400 text-black font-semibold px-4 py-2 rounded"
              onClick={async () => {
                localStorage.setItem("TEACH_TOKEN", token);
                await loadCandidates(token);
              }}
            >
              Load 10
            </button>
          </div>
        </div>

        {!c ? (
          <div className="bg-zinc-900 border border-zinc-800 rounded p-6 text-zinc-300">
            No candidates. Click <b>Load 10</b>.
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left */}
            <div className="lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded p-4">
              <div className="flex items-center justify-between">
                <div className="text-xl font-bold">{c.ticker}</div>
                <div className="text-xs px-2 py-1 rounded border border-zinc-700 text-zinc-300">
                  {c.label}
                </div>
              </div>

              <div className="mt-3 text-sm text-zinc-300 space-y-2">
                <div>RS vs SPY: <b>{c.rs_vs_spy ?? "—"}</b></div>
                <div>Vol Z: <b>{c.vol_z ?? "—"}</b></div>
                <div className="text-xs text-zinc-400">Plan type: {c.plan_type ?? "—"}</div>
                {c.already_labeled_today && (
                  <div className="mt-2 text-xs text-emerald-300">Already labeled today ✅</div>
                )}
              </div>

              <div className="mt-4 flex gap-2">
                <button
                  className="flex-1 bg-zinc-800 hover:bg-zinc-700 px-3 py-2 rounded"
                  onClick={() => setIdx((x) => Math.max(x - 1, 0))}
                >
                  ← Prev
                </button>
                <button
                  className="flex-1 bg-zinc-800 hover:bg-zinc-700 px-3 py-2 rounded"
                  onClick={() => setIdx((x) => Math.min(x + 1, candidates.length - 1))}
                >
                  Next →
                </button>
              </div>

              <div className="mt-3 text-xs text-zinc-500">
                Shortcuts: <b>Enter</b>=Save, <b>←/→</b>=Prev/Next
              </div>
            </div>

            {/* Right */}
            <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-zinc-400 mb-2">Mode</div>
                  <div className="flex gap-2">
                    <button
                      className={`px-3 py-2 rounded border ${mode === "conservative" ? "border-cyan-400 bg-cyan-400/10" : "border-zinc-700"}`}
                      onClick={() => setMode("conservative")}
                    >
                      Conservative
                    </button>
                    <button
                      className={`px-3 py-2 rounded border ${mode === "aggressive" ? "border-pink-400 bg-pink-400/10" : "border-zinc-700"}`}
                      onClick={() => setMode("aggressive")}
                    >
                      Aggressive
                    </button>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-zinc-400 mb-2">Idea source</div>
                  <select
                    className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2"
                    value={ideaSource}
                    onChange={(e) => setIdeaSource(e.target.value as IdeaSource)}
                  >
                    <option value="scanner">Scanner</option>
                    <option value="memory">I’ve traded it</option>
                    <option value="news_attention">News / Attention</option>
                    <option value="instinct">Instinct</option>
                  </select>
                </div>

                <div>
                  <div className="text-xs text-zinc-400 mb-2">Timeframe intent</div>
                  <select
                    className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2"
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value as Timeframe)}
                  >
                    <option value="intraday">Intraday</option>
                    <option value="swing">Swing</option>
                    <option value="position">Position</option>
                  </select>
                </div>

                <div>
                  <div className="text-xs text-zinc-400 mb-2">Exit intent</div>
                  <select
                    className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2"
                    value={exitIntent}
                    onChange={(e) => setExitIntent(e.target.value as ExitIntent)}
                  >
                    <option value="before_last_high">Exit before last high</option>
                    <option value="partial_then_runner">Partial then runner</option>
                    <option value="hard_stop_only">Hard stop only</option>
                    <option value="trailing_stop">Trailing stop</option>
                    <option value="decide_live">Decide live</option>
                  </select>
                </div>
              </div>

              <div className="mt-5">
                <div className="text-xs text-zinc-400 mb-2">Entry reasons (pick up to 2)</div>
                <div className="flex flex-wrap gap-2">
                  {entryOptions.map((r) => (
                    <button
                      key={r}
                      className={`px-3 py-2 rounded border text-sm ${
                        entryReasons.includes(r) ? "border-emerald-400 bg-emerald-400/10" : "border-zinc-700"
                      }`}
                      onClick={() => toggleReason(r)}
                    >
                      {r.replaceAll("_", " ")}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-5">
                <div className="text-xs text-zinc-400 mb-2">
                  Confidence: <b className="text-zinc-100">{confidence}</b>
                </div>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={confidence}
                  onChange={(e) => setConfidence(Number(e.target.value))}
                  className="w-full"
                />
              </div>

              <div className="mt-5">
                <div className="text-xs text-zinc-400 mb-2">Notes (optional)</div>
                <textarea
                  className="w-full bg-zinc-950 border border-zinc-700 rounded px-3 py-2 min-h-[80px]"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. fib 0.618 bounce + volume shelf + prior high reclaim"
                />
              </div>

              <div className="mt-5 flex items-center justify-between">
                <div className="text-xs text-zinc-500">Saves into Supabase <b>teach_labels</b></div>
                <button
                  disabled={saving}
                  className="bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-bold px-5 py-3 rounded"
                  onClick={saveLabel}
                >
                  {saving ? "Saving..." : "Save & Next (Enter)"}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 text-sm text-zinc-500">
          Day goal: label 10. If you do 14 days = 140 decisions → enough to start learning your brain.
        </div>
      </div>
    </div>
  );
}
