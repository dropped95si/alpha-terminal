"use client";

import React, { useMemo } from "react";
import { Line } from "react-chartjs-2";
import { Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend } from "chart.js";
import annotationPlugin from "chartjs-plugin-annotation";
import type { Card } from "@/lib/types";

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend, annotationPlugin);

function sparklineFromCard(c: Card) {
  const p = c.price;
  const lo = c.range?.low ?? (p * 0.92);
  const hi = c.range?.high ?? (p * 1.08);
  const mid = (lo + hi) / 2;
  return [lo, mid, p, p, null, null];
}

export function NeonChart({ card, accent }: { card: Card; accent: "primary" | "purple" }) {
  const data = useMemo(() => {
    const series = sparklineFromCard(card);
    const pred = [null, null, null, series[3] ?? card.price, card.price * 1.03, card.price * 1.06];
    return {
      labels: ["-5", "-3", "-1", "0", "+1", "+2"],
      datasets: [
        { label: "Historical", data: series, borderColor: "#fff", borderWidth: 2, tension: 0.4, pointRadius: 3, pointBackgroundColor: "#000", pointBorderColor: "#fff" },
        { label: "Scenario Path", data: pred, borderColor: accent === "primary" ? "#00f3ff" : "#bc13fe", borderWidth: 2, borderDash: [5, 5], tension: 0.4, pointRadius: 3, pointBackgroundColor: "#000", pointBorderColor: accent === "primary" ? "#00f3ff" : "#bc13fe" },
      ],
    };
  }, [card, accent]);

  const entry = card.plan.entry as any;
  const entryLine = entry.type === "breakout_confirmation" ? entry.trigger : entry.zone.high;

  const options: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      annotation: {
        annotations: {
          entryLine: { type: "line", yMin: entryLine, yMax: entryLine, borderColor: "#0aff0a", borderWidth: 1, label: { display: true, content: "ENTRY", backgroundColor: "#0aff0a", color: "#000", position: "start" } },
          stopLine: { type: "line", yMin: card.plan.exit_if_wrong.stop, yMax: card.plan.exit_if_wrong.stop, borderColor: "#ff003c", borderWidth: 1, label: { display: true, content: "STOP", color: "#ff003c", position: "start" } },
        },
      },
    },
    scales: {
      y: { grid: { color: "#111" }, ticks: { color: "#555" } },
      x: { grid: { display: false }, ticks: { color: "#555" } },
    },
  };

  return (
    <div className="panel h-[400px] flex flex-col">
      <div className="panel-header flex justify-between">
        <span>
          <strong className="text-white text-lg">{card.ticker}</strong> // SETUP VIEW
        </span>
        <span className={accent === "primary" ? "text-cyber-primary text-xs" : "text-cyber-purple text-xs"}>
          {entry.type === "breakout_confirmation" ? "BREAKOUT CONFIRM" : "FV VALUE ZONE"}
        </span>
      </div>
      <div className="flex-grow relative p-4 bg-[#050505]">
        <Line data={data as any} options={options} />
      </div>
    </div>
  );
}
