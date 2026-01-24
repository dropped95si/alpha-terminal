import type { Card, CardsFile } from "./types";

export type Signal = {
  id?: string;

  as_of: string; // ISO timestamp of scan
  ticker: string;

  label: string; // READY_CONFIRMED | EARLY | WATCH (or any custom label)
  plan_type: string;

  entry: any;
  stop: { price: number };
  targets: Array<{ price: number }>;

  confidence?: number;
  rr?: number;

  vol_z?: number;
  rs_vs_spy?: number;

  learned_top_rules?: any[];
  source?: string;
  interval?: string;

  [k: string]: any;
};

export function cardToSignal(card: Card, as_of: string, defaultLabel: string): Signal {
  const labels = Array.isArray(card.labels) ? card.labels : [];
  const label = labels[0] ?? defaultLabel;

  const plan: any = card.plan ?? {};
  const entry =
    plan.entry?.type === "breakout_confirmation"
      ? { type: "breakout_confirmation", trigger: plan.entry.trigger, why: plan.entry.why }
      : plan.entry?.type === "value_zone"
        ? { type: "value_zone", zone: plan.entry.zone, why: plan.entry.why }
        : { price: card.price };

  const stopPrice =
    typeof plan.exit_if_wrong?.stop === "number" ? plan.exit_if_wrong.stop : (card as any)?.stop?.price;

  const targets =
    Array.isArray(plan.targets)
      ? plan.targets.map((t: any) => ({ price: Number(t.price) }))
      : Array.isArray((card as any)?.targets)
        ? (card as any).targets
        : [];

  return {
    as_of,
    ticker: card.ticker,
    label,
    plan_type: plan.entry?.type ?? "unknown",
    entry,
    stop: { price: Number(stopPrice ?? 0) },
    targets,
    vol_z: card.vol_z,
    rs_vs_spy: (card as any).rs_vs_spy ?? card.rs_60d_vs_spy,
    learned_top_rules: card.learned_top_rules,
    ...card,
  };
}

export function cardsFileToSignals(file: CardsFile, defaultLabel: string): Signal[] {
  const as_of = file.as_of ?? new Date().toISOString();
  return (file.cards ?? []).map((c) => cardToSignal(c, as_of, defaultLabel));
}
