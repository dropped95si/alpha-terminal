"use client";
import React, { useEffect, useState } from 'react';
import { MatrixTable } from '@/components/MatrixTable';
import { NeonChart } from '@/components/NeonChart';
import { Badge } from '@/components/Badge';

export default function AlphaTerminalV2() {
  const [signals, setSignals] = useState([]);

  // V2 Data Fetcher
  useEffect(() => {
    async function loadAlpha() {
      const res = await fetch('/api/ingest-scan');
      const data = await res.json();
      setSignals(data);
    }
    loadAlpha();
  }, []);

  return (
    <main className="min-h-screen bg-[#050505] text-white p-8 font-sans">
      {/* HEADER: V2.0 MECHANICAL BASELINE */}
      <header className="flex justify-between items-end mb-16 border-b border-white/5 pb-8">
        <div>
          <h1 className="text-7xl font-black tracking-tighter italic">
            ALPHA TERMINAL <span className="text-blue-500">V2.0</span>
          </h1>
          <p className="text-slate-500 uppercase font-bold tracking-widest text-xs mt-2">
            Institutional Probability Engine // Mechanical Engineering for Money
          </p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-slate-600 uppercase font-black">System Status</p>
          <p className="text-emerald-500 font-mono font-bold italic">● ADAPTIVE_LEARNING_ACTIVE</p>
        </div>
      </header>

      {/* SIGNAL GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {signals.map((s: any) => (
          <div key={s.ticker} className="bg-[#080808] border border-white/5 p-8 rounded-[2rem] hover:border-blue-500/30 transition-all group">
            
            {/* TICKER & MANUAL ALPHA BADGE */}
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-5xl font-black tracking-tighter italic group-hover:text-blue-400 transition-colors">
                  {s.ticker}
                </h2>
                {s.is_manual_alpha && (
                  <span className="bg-blue-500 text-[9px] font-black px-2 py-0.5 rounded-full uppercase mt-1 inline-block animate-pulse">
                    Human Verified Alpha
                  </span>
                )}
              </div>
              <div className="text-right">
                <p className="text-[10px] text-slate-500 font-black uppercase">Confidence</p>
                <p className="text-3xl font-black text-white">{s.confidence}%</p>
              </div>
            </div>

            {/* ALPHA HEATMAP (1:3 Reward/Risk) */}
            <div className="mb-8">
              <div className="flex justify-between text-[9px] font-black uppercase text-slate-600 mb-2">
                <span>Structural Risk</span>
                <span>Alpha Target (3.0x)</span>
              </div>
              <div className="h-4 w-full bg-white/5 rounded-full flex overflow-hidden p-1 border border-white/5">
                <div className="h-full bg-red-600/40 rounded-l-full" style={{ width: '25%' }}></div>
                <div className="w-1 bg-white/20"></div>
                <div className="h-full bg-blue-600 rounded-r-full shadow-[0_0_20px_rgba(37,99,235,0.4)]" style={{ width: '70%' }}></div>
              </div>
            </div>

            {/* MECHANICAL STATS */}
            <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-6">
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold">Position Size</p>
                <p className="text-xl font-mono font-black text-emerald-400">{s.shares} <span className="text-[10px]">SHRS</span></p>
              </div>
              <div className="text-right">
                <p className="text-[10px] text-slate-500 uppercase font-bold">Whale Fight (Vol Z)</p>
                <p className="text-xl font-mono font-black text-blue-500">{s.vol_z}</p>
              </div>
            </div>

            {/* BUY TARGET */}
            <div className="mt-6 bg-white/5 p-4 rounded-2xl border border-white/5 text-center">
              <p className="text-[10px] text-slate-400 uppercase font-bold mb-1">Exit Target</p>
              <p className="text-2xl font-black text-white">${s.target}</p>
            </div>

          </div>
        ))}
      </div>
    </main>
  );
}