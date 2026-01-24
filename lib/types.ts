export type AutoThresholds = {
  vol_z_min: number;
  near_breakout_pct: number;
  fv_max_extension_atr: number;
  ready_confirm_closes: number;
};

export type Plan =
  | {
      entry: { type: "breakout_confirmation"; trigger: number; why?: string[] };
      exit_if_wrong: { stop: number; why?: string[] };
      targets: { price: number; why?: string }[];
    }
  | {
      entry: { type: "value_zone"; zone: { low: number; high: number }; why?: string[] };
      exit_if_wrong: { stop: number; why?: string[] };
      targets: { price: number; why?: string }[];
    };

export type Card = {
  ticker: string;
  price: number;

  avg_dollar_volume?: number;
  rs_60d_vs_spy?: number;
  vol_z?: number;

  fv?: { vwap_20: number; low: number; high: number };
  range?: { low: number; high: number };

  labels?: string[];
  plan: Plan;

  learned_top_rules?: any[];
  [k: string]: any;
};

export type CardsFile = {
  as_of: string;
  auto_thresholds?: AutoThresholds;
  cards: Card[];
};

export type IndustriesFile = {
  as_of: string;
  auto_thresholds?: AutoThresholds;
  rankings: { ticker: string; score: number }[];
};
