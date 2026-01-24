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



function requireTeachToken(req: Request) {
  const token = req.headers.get("authorization")?.replace("Bearer ", "");
  return Boolean(process.env.TEACH_TOKEN && token === process.env.TEACH_TOKEN);
}

export async function POST(req: Request) {
  const supabase = getSupabase();
  if (!requireTeachToken(req)) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const body = await req.json();

  // Minimal validation
  const required = ["ticker", "mode", "idea_source", "timeframe", "exit_intent", "confidence"];
  for (const k of required) {
    if (body[k] === undefined || body[k] === null || body[k] === "") {
      return NextResponse.json({ error: `missing ${k}` }, { status: 400 });
    }
  }

  const entry_reasons = Array.isArray(body.entry_reasons) ? body.entry_reasons.slice(0, 2) : [];

  const row = {
    ticker: body.ticker,
    mode: body.mode,
    idea_source: body.idea_source,
    timeframe: body.timeframe,
    entry_reasons,
    exit_intent: body.exit_intent,
    confidence: Number(body.confidence),
    notes: body.notes ?? null,

    scan_run_id: body.scan_run_id ?? null,
    signal_id: body.signal_id ?? null,
  };

  const { data, error } = await supabase.from("teach_labels").insert(row).select("id").single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ ok: true, id: data.id });
}
