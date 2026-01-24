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



export async function POST(req: Request) {
  const supabase = getSupabase();
  const token = req.headers
    .get("authorization")
    ?.replace("Bearer ", "");

  if (!process.env.INGEST_TOKEN || token !== process.env.INGEST_TOKEN) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const { as_of, source, interval, history_years, auto_thresholds, signals } = body;

  if (!as_of || !Array.isArray(signals)) {
    return NextResponse.json({ error: "bad payload" }, { status: 400 });
  }

  const { data: scanRun, error: scanErr } = await supabase
    .from("scan_runs")
    .insert({
      as_of,
      source: source ?? "unknown",
      interval: interval ?? "1d",
      history_years: history_years ?? 5,
      auto_thresholds: auto_thresholds ?? {},
    })
    .select()
    .single();

  if (scanErr) {
    return NextResponse.json({ error: scanErr.message }, { status: 500 });
  }

  const rows = signals.map((s: any) => ({
    scan_run_id: scanRun.id,
    ...s,
  }));

  const { error: sigErr } = await supabase
    .from("signals")
    .insert(rows);

  if (sigErr) {
    return NextResponse.json({ error: sigErr.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true, scan_run_id: scanRun.id });
}
