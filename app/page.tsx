"use client";

import { useEffect, useMemo, useState } from "react";

type StopLadderRow = {
  name: string;
  stop_price: number;
  p: number;
  confidence: number;
  rr: number;
  ev: number;
};

type Signal = {
  id: string;
  ticker: string;
  label: string;
  plan_type: string;

  entry: any;
  stop: { price: number; [k: string]: any };
  targets: Array<{ price: number; [k: string]: any }>;

  vol_z?: number;
  rs_vs_spy?: number;
  created_at?: string;

  probability?: number | null;
  confidence?: number | null;
  why?: string[] | null;
  chosen_stop?: any;
  stop_ladder?: StopLadderRow[] | null;
};

type ApiResp = {
  source?: string;
  as_of?: string | null;
  signals?: Signal[];
  error?: string;
};

function num(x: any, d = 0) {
  const n = Number(x);
  return Number.isFinite(n) ? n : d;
}

function levelBox(entry: number, stop: number, tp1: number) {
  const lo = Math.min(stop, entry, tp1);
  const hi = Math.max(stop, entry, tp1);
  const span = hi - lo || 1;

  const y = (v: number) => 1 - (v - lo) / span; // 0..1
  const yEntry = y(entry);
  const yStop = y(stop);
  const yTp = y(tp1);

  return (
    <svg viewBox="0 0 100 60" className="w-full h-24 rounded bg-slate-950/60 border border-slate-800">
      {/* TP */}
      <line x1="10" x2="90" y1={10 + 40 * yTp} y2={10 + 40 * yTp} stroke="currentColor" opacity="0.65" />
      {/* Entry */}
      <line x1="10" x2="90" y1={10 + 40 * yEntry} y2={10 + 40 * yEntry} stroke="currentColor" opacity="0.95" />
      {/* Stop */}
      <line x1="10" x2="90" y1={10 + 40 * yStop} y2={10 + 40 * yStop} stroke="currentColor" opacity="0.45" />
      <text x="10" y={8 + 40 * yTp} fontSize="6" fill="currentColor" opacity="0.8">TP1</text>
      <text x="10" y={8 + 40 * yEntry} fontSize="6" fill="currentColor" opacity="0.8">ENTRY</text>
      <text x="10" y={8 + 40 * yStop} fontSize="6" fill="currentColor" opacity="0.8">SL</text>
    </svg>
  );
}

function pct(x: any) {
  const n = num(x, NaN);
  return Number.isFinite(n) ? `${Math.round(n * 100)}%` : "---";
}

export default function AlphaTerminalV21() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [source, setSource] = useState<string>("unknown");
  const [asOf, setAsOf] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [tab, setTab] = useState<"top" | "detail">("top");
  const [selected, setSelected] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"ev" | "prob" | "conf" | "rr">("ev");

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await fetch(`/api/signals?limit=300`, { cache: "no-store" });
        const j = (await res.json()) as ApiResp;
        if (!res.ok) throw new Error(j?.error || `API error ${res.status}`);
        setSignals(j.signals ?? []);
        setSource(j.source ?? "unknown");
        setAsOf(j.as_of ?? null);
        setErr(null);
      } catch (e: any) {
        setErr(e?.message ?? "Failed to load signals");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const enriched = useMemo(() => {
    return (signals ?? []).map((s) => {
      const ai = s.entry?.ai ?? null;
      const probability = s.probability ?? ai?.probability ?? null;
      const confidence = s.confidence ?? ai?.confidence ?? null;
      const why = (s.why ?? ai?.why ?? null) as any;
      const stop_ladder = (s.stop_ladder ?? ai?.stop_ladder ?? null) as any;
      const chosen_stop = s.chosen_stop ?? ai?.chosen_stop ?? null;

      const entryRef = num(s.entry?.trigger ?? s.entry?.price ?? s.entry?.zone?.low ?? 0);
      const tp1 = num(s.targets?.[0]?.price ?? 0);
      const stopPrice = num(s.stop?.price ?? chosen_stop?.stop_price ?? 0);

      const risk = entryRef - stopPrice;
      const reward = tp1 - entryRef;
      const rr = risk > 0 && reward > 0 ? reward / risk : 0;
      const ev = (probability ?? 0) * rr - (1 - (probability ?? 0));

      return { ...s, probability, confidence, why, stop_ladder, chosen_stop, __entryRef: entryRef, __tp1: tp1, __stop: stopPrice, __rr: rr, __ev: ev };
    });
  }, [signals]);

  const sorted = useMemo(() => {
    const arr = [...enriched];
    const key = sortBy;
    arr.sort((a: any, b: any) => {
      const av = key === "prob" ? num(a.probability, 0) : key === "conf" ? num(a.confidence, 0) : key === "rr" ? num(a.__rr, 0) : num(a.__ev, -999);
      const bv = key === "prob" ? num(b.probability, 0) : key === "conf" ? num(b.confidence, 0) : key === "rr" ? num(b.__rr, 0) : num(b.__ev, -999);
      return bv - av;
    });
    return arr;
  }, [enriched, sortBy]);

  const selectedSignal = useMemo(() => {
    if (!selected) return sorted[0] ?? null;
    return sorted.find((s) => s.ticker === selected) ?? sorted[0] ?? null;
  }, [sorted, selected]);

  if (loading) {
    return <div className="p-10 bg-slate-950 text-blue-500 font-mono h-screen">Loading Alpha Feed...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-10 border-b border-slate-800 pb-6 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-blue-500 uppercase italic">
            Alpha Terminal <span className="text-slate-500 font-light italic">v2.1</span>
          </h1>
          <p className="text-slate-500 font-mono text-xs mt-2 italic">"Sober Math for the Family Account"</p>
          <p className="text-slate-600 font-mono text-[10px] mt-2 uppercase tracking-widest">
            LAST: {asOf ? new Date(asOf).toLocaleString() : "unknown"} • SOURCE: {source}
          </p>
        </div>
        <div className="text-right text-xs text-slate-500 font-mono uppercase">
          STATUS: {err ? "ERROR" : "LIVE"} <br />
          SIGNALS: {signals.length}
        </div>
      </header>

      {err && (
        <div className="mb-8 p-4 rounded-lg border border-red-500/20 bg-red-500/5 text-red-300 font-mono text-xs">
          {err}
        </div>
      )}

      <div className="mb-6 flex gap-2">
        <button onClick={() => setTab("top")} className={`px-3 py-2 rounded text-xs font-black ${tab === "top" ? "bg-blue-500/20 text-blue-300" : "bg-slate-900 text-slate-300"}`}>
          TOP SIGNALS
        </button>
        <button onClick={() => setTab("detail")} className={`px-3 py-2 rounded text-xs font-black ${tab === "detail" ? "bg-blue-500/20 text-blue-300" : "bg-slate-900 text-slate-300"}`}>
          TICKER DETAIL
        </button>

        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-mono">SORT:</span>
          {(["ev","prob","conf","rr"] as const).map((k) => (
            <button key={k} onClick={() => setSortBy(k)} className={`px-2 py-1 rounded ${sortBy === k ? "bg-slate-700" : "bg-slate-900"}`}>
              {k.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {tab === "top" && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sorted.map((s: any) => (
            <div key={s.ticker} className="bg-slate-900 border border-slate-800 rounded-xl p-6 border-l-4 border-l-blue-500 hover:shadow-2xl hover:shadow-blue-500/10 transition-all">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-3xl font-black cursor-pointer" onClick={() => { setSelected(s.ticker); setTab("detail"); }}>
                    {s.ticker}
                  </h2>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">{s.label}</p>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono text-slate-400">P: <span className="text-blue-300 font-black">{pct(s.probability)}</span></div>
                  <div className="text-xs font-mono text-slate-400">C: <span className="text-slate-200 font-black">{pct(s.confidence)}</span></div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                <div className="bg-slate-950/60 border border-slate-800 p-2 rounded">
                  <div className="text-slate-500">EV</div>
                  <div className="text-slate-100 font-black">{num(s.__ev, 0).toFixed(2)}</div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800 p-2 rounded">
                  <div className="text-slate-500">RR</div>
                  <div className="text-slate-100 font-black">{num(s.__rr, 0).toFixed(2)}</div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800 p-2 rounded">
                  <div className="text-slate-500">VOL_Z</div>
                  <div className="text-slate-100 font-black">{num(s.vol_z, 0).toFixed(2)}</div>
                </div>
              </div>

              <div className="mt-4">{levelBox(num(s.__entryRef, 0), num(s.__stop, 0), num(s.__tp1, 0))}</div>

              <div className="mt-4 text-xs text-slate-400 space-y-1">
                {(s.why ?? []).slice(0, 3).map((w: string, i: number) => (
                  <div key={i} className="truncate">• {w}</div>
                ))}
              </div>

              {Array.isArray(s.stop_ladder) && s.stop_ladder.length > 0 && (
                <div className="mt-4 text-[11px] font-mono text-slate-300">
                  <div className="text-slate-500 uppercase text-[10px] mb-1">Stops (P% / C%)</div>
                  {s.stop_ladder.slice(0, 3).map((r: any) => (
                    <div key={r.name} className="flex justify-between">
                      <span>{r.name}</span>
                      <span>{pct(r.p)} / {pct(r.confidence)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === "detail" && selectedSignal && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="text-xs font-mono text-slate-400 mb-3">SELECT</div>
            <div className="space-y-2 max-h-[70vh] overflow-auto pr-1">
              {sorted.slice(0, 150).map((s: any) => (
                <button
                  key={s.ticker}
                  onClick={() => setSelected(s.ticker)}
                  className={`w-full text-left px-3 py-2 rounded border ${selected === s.ticker ? "border-blue-500 bg-blue-500/10" : "border-slate-800 bg-slate-950/30"}`}
                >
                  <div className="flex justify-between text-sm font-black">
                    <span>{s.ticker}</span>
                    <span className="text-slate-300">{pct(s.probability)}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-widest">{s.label}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-4xl font-black">{selectedSignal.ticker}</div>
                <div className="text-xs font-mono text-slate-500 uppercase tracking-widest">{selectedSignal.label} • {selectedSignal.plan_type}</div>
              </div>
              <div className="text-right text-xs font-mono text-slate-400">
                <div>P: <span className="text-blue-300 font-black">{pct((selectedSignal as any).probability)}</span></div>
                <div>C: <span className="text-slate-200 font-black">{pct((selectedSignal as any).confidence)}</span></div>
                <div>EV: <span className="text-slate-200 font-black">{num((selectedSignal as any).__ev, 0).toFixed(2)}</span></div>
              </div>
            </div>

            <div className="mt-5">{levelBox(num((selectedSignal as any).__entryRef, 0), num((selectedSignal as any).__stop, 0), num((selectedSignal as any).__tp1, 0))}</div>

            <div className="mt-6 grid md:grid-cols-3 gap-3 text-sm font-mono">
              <div className="bg-slate-950/60 border border-slate-800 p-3 rounded">
                <div className="text-slate-500 text-xs">ENTRY</div>
                <div className="text-slate-100 font-black">${num((selectedSignal as any).__entryRef, 0).toFixed(2)}</div>
              </div>
              <div className="bg-slate-950/60 border border-slate-800 p-3 rounded">
                <div className="text-slate-500 text-xs">STOP</div>
                <div className="text-slate-100 font-black">${num((selectedSignal as any).__stop, 0).toFixed(2)}</div>
              </div>
              <div className="bg-slate-950/60 border border-slate-800 p-3 rounded">
                <div className="text-slate-500 text-xs">TP1</div>
                <div className="text-slate-100 font-black">${num((selectedSignal as any).__tp1, 0).toFixed(2)}</div>
              </div>
            </div>

            <div className="mt-6 grid md:grid-cols-2 gap-6">
              <div>
                <div className="text-slate-500 uppercase text-xs font-mono mb-2">WHY</div>
                <div className="space-y-2 text-xs text-slate-300">
                  {(((selectedSignal as any).why ?? []) as string[]).slice(0, 10).map((w, i) => (
                    <div key={i} className="bg-slate-950/40 border border-slate-800 rounded p-2">• {w}</div>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-slate-500 uppercase text-xs font-mono mb-2">STOP LADDER</div>
                <div className="space-y-2 text-xs font-mono text-slate-300">
                  {Array.isArray((selectedSignal as any).stop_ladder) && (selectedSignal as any).stop_ladder.length > 0 ? (
                    (selectedSignal as any).stop_ladder.slice(0, 8).map((r: any) => (
                      <div key={r.name} className="flex justify-between bg-slate-950/40 border border-slate-800 rounded p-2">
                        <span>{r.name} @ ${num(r.stop_price, 0).toFixed(2)}</span>
                        <span>{pct(r.p)} / {pct(r.confidence)} • EV {num(r.ev, 0).toFixed(2)}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-500">No stop ladder available.</div>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-8 text-xs text-slate-500 font-mono">
              Clickable chart + overlays (TradingView/Canvas) comes next; this is the v2.1 mock level panel.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
