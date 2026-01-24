"use client";
import { useEffect, useState } from 'react';

interface Signal {
  id: string;
  ticker: string;
  label: string;
  plan_type: string;
  entry: any;
  stop: { price: number };
  targets: Array<{ price: number }>;
  vol_z: number;
  rs_vs_spy: number;
  created_at: string;
}


export default function MomDashboard() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [source, setSource] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const res = await fetch("/api/signals?limit=300", { cache: "no-store" });
      const j = await res.json();
      setSignals(j.signals ?? []);
      setLastScan(j.signals?.[0]?.as_of ?? null);
    })();
  }, []);

  if (loading) return <div className="p-10 bg-slate-950 text-blue-500 font-mono h-screen">Loading Alpha Feed...</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <header className="mb-12 border-b border-slate-800 pb-6 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-blue-500 uppercase italic">
            Alpha Terminal <span className="text-slate-500 font-light italic">v1.0</span>
          </h1>
          <p className="text-slate-500 font-mono text-xs mt-2 italic">"Sober Math for the Family Account"</p>
        </div>
        <div className="text-right text-xs text-slate-500 font-mono uppercase">
          STATUS: PRODUCTION_LIVE <br />
          SOURCE: {source || "unknown"} <br />
          SIGNALS: {signals.length}
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {signals.map((s) => (
          <div key={s.id} className="bg-slate-900 border border-slate-800 rounded-xl p-6 border-l-4 border-l-blue-500 hover:shadow-2xl hover:shadow-blue-500/10 transition-all group">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-4xl font-black">{s.ticker}</h2>
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">{s.label}</p>
              </div>
              <div className="text-right">
                <span className="bg-blue-500/10 text-blue-400 px-3 py-1 rounded-md text-[10px] font-black">
                  VOL_Z: {s.vol_z || '---'}
                </span>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-slate-950/50 border border-slate-800 p-4 rounded-lg">
                <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-1 font-bold">Plan Type</p>
                <p className="text-xl font-bold text-white tracking-tight">{s.plan_type}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-500/5 border border-blue-500/10 p-3 rounded-lg">
                  <p className="text-[9px] text-blue-500/60 uppercase font-bold mb-1">Entry</p>
                  <p className="text-lg font-mono font-bold text-blue-400 tracking-tighter">${s.entry?.price?.toFixed(2) || '---'}</p>
                </div>
                <div className="bg-red-500/5 border border-red-500/10 p-3 rounded-lg">
                  <p className="text-[9px] text-red-500/60 uppercase font-bold mb-1">Stop Loss</p>
                  <p className="text-lg font-mono font-bold text-red-400 tracking-tighter">${s.stop?.price?.toFixed(2) || '---'}</p>
                </div>
              </div>

              {s.targets && s.targets.length > 0 && (
                <div className="bg-green-500/5 border border-green-500/10 p-3 rounded-lg">
                  <p className="text-[9px] text-green-500/60 uppercase font-bold mb-1">Target (TP)</p>
                  <p className="text-lg font-mono font-bold text-green-400 tracking-tighter">${s.targets[0]?.price?.toFixed(2) || '---'}</p>
                </div>
              )}

              <div className="pt-4 border-t border-slate-800">
                <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2 font-bold italic">Signal Metrics</p>
                <div className="text-xs text-slate-400 grid grid-cols-2 gap-2">
                  <span>RS vs SPY: {s.rs_vs_spy?.toFixed(2) || '---'}</span>
                  <span>Vol Z: {s.vol_z?.toFixed(2) || '---'}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {signals.length === 0 && (
        <div className="text-center text-slate-400 mt-20">
          <p className="text-lg">No signals found. Scanner will update Monday at 8:30 AM EST.</p>
        </div>
      )}
    </div>
  );
}