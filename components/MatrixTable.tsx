"use client";

import { Card } from "@/lib/types";
import { Badge } from "./Badge";

function fmt(n?: number, digits=2) {
  if (n === undefined || n === null || Number.isNaN(n)) return "";
  return n.toFixed(digits);
}

function entryText(c: Card) {
  const e = c.plan.entry as any;
  if (e.type === "breakout_confirmation") return `$${fmt(e.trigger)} (breakout)`;
  return `$${fmt(e.zone.low)} - $${fmt(e.zone.high)} (value)`;
}

export function MatrixTable({ title, subtitle, cards }: { title: string; subtitle?: string; cards: Card[] }) {
  return (
    <section className="panel overflow-hidden">
      <div className="panel-header bg-[#080808] flex justify-between items-center py-3">
        <h3 className="text-lg font-bold text-white uppercase tracking-wider">
          {title} <span className="text-gray-600 text-xs ml-2">{subtitle ?? ""}</span>
        </h3>
        <div className="flex gap-2 text-[10px]">
          <Badge tone="success">● READY</Badge>
          <Badge tone="warning">● EARLY</Badge>
          <Badge tone="muted">● WATCH</Badge>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs md:text-sm">
          <thead>
            <tr className="bg-[#111] text-gray-500 uppercase tracking-widest border-b border-[#222]">
              <th className="p-4 font-normal">Ticker</th>
              <th className="p-4 font-normal text-center">RS (60d vs SPY)</th>
              <th className="p-4 font-normal text-center">Vol Z</th>
              <th className="p-4 font-normal text-center text-cyber-primary">Price</th>
              <th className="p-4 font-normal text-cyber-success">Buy Zone / Trigger</th>
              <th className="p-4 font-normal text-cyber-danger">Stop</th>
              <th className="p-4 font-normal text-cyber-primary">Take Profit (1 / 2)</th>
              <th className="p-4 font-normal">Labels</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-[#1a1a1a]">
            {cards.length === 0 ? (
              <tr><td className="p-4 text-gray-500" colSpan={8}>No rows.</td></tr>
            ) : cards.map((c) => {
              const labels = (c.labels ?? []).join(", ");
              const tp1 = c.plan.targets?.[0]?.price;
              const tp2 = c.plan.targets?.[1]?.price;
              const tone = labels.includes("READY_CONFIRMED") ? "success" : (labels.includes("EARLY") ? "warning" : "muted");
              return (
                <tr key={c.ticker} className="hover:bg-[#111] transition-colors group">
                  <td className="p-4">
                    <div className="font-bold text-white text-lg group-hover:text-cyber-primary transition">{c.ticker}</div>
                    <div className="mt-1"><Badge tone={tone as any}>{labels.includes("READY_CONFIRMED") ? "READY" : (labels.includes("EARLY") ? "EARLY" : "WATCH")}</Badge></div>
                  </td>
                  <td className="p-4 text-center text-gray-300">{fmt(c.rs_60d_vs_spy, 4)}</td>
                  <td className="p-4 text-center text-gray-300">{fmt(c.vol_z, 2)}</td>
                  <td className="p-4 text-center font-bold text-white">${fmt(c.price, 2)}</td>
                  <td className="p-4 font-mono text-cyber-success font-bold">{entryText(c)}</td>
                  <td className="p-4 font-mono text-cyber-danger">${fmt(c.plan.exit_if_wrong.stop, 2)}</td>
                  <td className="p-4 font-mono text-cyber-primary font-bold">${fmt(tp1, 2)} / ${fmt(tp2, 2)}</td>
                  <td className="p-4 text-gray-400">{labels}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
