import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const runtime = "nodejs";


function getSupabase() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("Supabase env vars missing (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)");
  }
  return createClient(url, key);
}


function mustAuth(req: Request) {
  const token = req.headers.get("authorization")?.replace("Bearer ", "");
  if (!process.env.TEACH_TOKEN || token !== process.env.TEACH_TOKEN) {
    return false;
  }
  return true;
}


export async function GET(req: Request) {
  const supabase = getSupabase();
  if (!mustAuth(req)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  // 1) latest scan run
  const { data: scanRun, error: scanErr } = await supabase
    .from("scan_runs")
    .select("id, as_of")
    .order("as_of", { ascending: false })
    .limit(1)
    .single();

  if (scanErr || !scanRun) {
    return NextResponse.json({ error: scanErr?.message ?? "no scan_runs found" }, { status: 500 });
  }

  // 2) pull candidate signals from that run
  // prioritize READY, then EARLY, then WATCH, then best RS/vol
  const { data: signals, error: sigErr } = await supabase
    .from("signals")
    .select("id, ticker, label, plan_type, rs_vs_spy, vol_z")
    .eq("scan_run_id", scanRun.id)
    .limit(300);

  if (sigErr) {
    return NextResponse.json({ error: sigErr.message }, { status: 500 });
  }

  const labelRank = (lbl: string) => {
    if (lbl === "READY_CONFIRMED") return 0;
    if (String(lbl).includes("EARLY")) return 1;
    if (lbl === "WATCH") return 2;
    return 3;
  };

  const sorted = (signals ?? [])
    .slice()
    .sort((a: any, b: any) => {
      const la = labelRank(a.label);
      const lb = labelRank(b.label);
      if (la !== lb) return la - lb;
      const rsA = Number(a.rs_vs_spy ?? 0);
      const rsB = Number(b.rs_vs_spy ?? 0);
      if (rsA !== rsB) return rsB - rsA;
      const vzA = Number(a.vol_z ?? 0);
      const vzB = Number(b.vol_z ?? 0);
      return vzB - vzA;
    })
    .slice(0, 10);

  // 3) mark “already labeled for this as_of”
  const tickers = sorted.map((x: any) => x.ticker);
  const { data: labeled } = await supabase
    .from("teach_labels")
    .select("ticker")
    .eq("as_of", scanRun.as_of)
    .in("ticker", tickers);

  const labeledSet = new Set((labeled ?? []).map((x: any) => x.ticker));

  return NextResponse.json({
    ok: true,
    as_of: scanRun.as_of,
    scan_run_id: scanRun.id,
    candidates: sorted.map((s: any) => ({
      ...s,
      already_labeled_today: labeledSet.has(s.ticker),
    })),
  });
}
