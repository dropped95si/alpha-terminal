import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const runtime = "nodejs";

function getSupabase() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY");
  return createClient(url, key);
}

function assertAuth(req: Request) {
  const want = process.env.INGEST_TOKEN;
  if (!want) return; // dev mode: no token set
  const got =
    req.headers.get("x-ingest-token") ??
    req.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ??
    "";
  if (got !== want) throw new Error("Unauthorized ingest");
}

export async function POST(req: Request) {
  try {
    assertAuth(req);

    const supabase = getSupabase();
    const payload = await req.json();

    const scan_runs = payload?.scan_runs;
    const signals = payload?.signals;

    if (!scan_runs || !signals || !Array.isArray(signals)) {
      return NextResponse.json({ error: "Invalid payload: expected { scan_runs, signals[] }" }, { status: 400 });
    }

    const { data: scanRun, error: scanErr } = await supabase
      .from("scan_runs")
      .insert(scan_runs)
      .select("*")
      .single();

    if (scanErr) return NextResponse.json({ error: scanErr.message }, { status: 500 });

    const rows = signals.map((s: any) => ({ scan_run_id: scanRun.id, ...s }));
    const { error: sigErr } = await supabase.from("signals").insert(rows);
    if (sigErr) return NextResponse.json({ error: sigErr.message }, { status: 500 });

    return NextResponse.json({ ok: true, scan_run_id: scanRun.id, inserted: rows.length });
  } catch (e: any) {
    return NextResponse.json({ error: e?.message ?? "Unknown error" }, { status: 401 });
  }
}
