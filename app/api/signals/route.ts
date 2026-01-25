import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { readFile } from "node:fs/promises";
import path from "node:path";

import type { CardsFile } from "@/lib/types";
import { cardsFileToSignals, type Signal } from "@/lib/signal";

export const runtime = "nodejs";

function getSupabase() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY");
  return createClient(url, key);
}

function normalizeEntry(entry: any) {
  if (!entry) return {};
  // keep entry as an object, but ensure numeric price-like fields are numbers when present
  const out = { ...entry };
  if (typeof out.trigger !== "undefined") out.trigger = Number(out.trigger);
  if (out.zone && typeof out.zone === "object") {
    if (typeof out.zone.low !== "undefined") out.zone.low = Number(out.zone.low);
    if (typeof out.zone.high !== "undefined") out.zone.high = Number(out.zone.high);
  }
  // Some scanners store entry price directly
  if (typeof out.price !== "undefined") out.price = Number(out.price);
  return out;
}

function normalizeStop(stop: any) {
  if (!stop) return { price: 0 };
  if (typeof stop === "number") return { price: stop };
  const price = stop.price ?? stop.stop ?? stop.stop_price ?? 0;
  return { ...stop, price: Number(price ?? 0) };
}

function extractAi(entry: any) {
  const ai = entry?.ai ?? entry?.AI ?? null;
  if (!ai) return null;
  return {
    probability: ai.probability ?? null,
    confidence: ai.confidence ?? null,
    why: ai.why ?? null,
    chosen_stop: ai.chosen_stop ?? null,
    stop_ladder: ai.stop_ladder ?? null,
    runtime_ms: ai.runtime_ms ?? null,
  };
}

async function fallbackSignals(): Promise<Signal[]> {
  // Reads local JSON outputs when Supabase is down / missing env
  const base = path.join(process.cwd(), "market_ai_kit", "output");

  const tryRead = async (fname: string): Promise<CardsFile | null> => {
    try {
      const raw = await readFile(path.join(base, fname), "utf-8");
      return JSON.parse(raw);
    } catch {
      return null;
    }
  };

  const ready = await tryRead("ready.json");
  const early = await tryRead("early.json");
  const watch = await tryRead("watch.json");

  const out: Signal[] = [];
  if (ready) out.push(...cardsFileToSignals(ready, "READY_CONFIRMED"));
  if (early) out.push(...cardsFileToSignals(early, "EARLY"));
  if (watch) out.push(...cardsFileToSignals(watch, "WATCH"));

  // sort by as_of desc
  out.sort((a: any, b: any) => String(b.created_at ?? b.as_of ?? "").localeCompare(String(a.created_at ?? a.as_of ?? "")));
  return out;
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const limit = Math.min(Number(url.searchParams.get("limit") ?? "200"), 1000);
  const label = url.searchParams.get("label");

  try {
    const supabase = getSupabase();
    let q = supabase.from("signals").select("*").order("created_at", { ascending: false }).limit(limit);
    if (label) q = q.eq("label", label);

    const { data, error } = await q;
    if (error) {
      const fb = await fallbackSignals();
      const as_of = (fb as any)?.[0]?.created_at ?? (fb as any)?.[0]?.as_of ?? null;
      return NextResponse.json({ source: "fallback_after_db_error", as_of, error: error.message, signals: fb });
    }

    const normalized = (data ?? []).map((s: any) => {
      const entry = normalizeEntry(s.entry);
      const ai = extractAi(entry);
      return {
        ...s,
        entry,
        stop: normalizeStop(s.stop),
        targets: Array.isArray(s.targets) ? s.targets : [],
        probability: ai?.probability ?? s.probability ?? null,
        confidence: ai?.confidence ?? s.confidence ?? null,
        why: ai?.why ?? s.why ?? null,
        chosen_stop: ai?.chosen_stop ?? s.chosen_stop ?? null,
        stop_ladder: ai?.stop_ladder ?? s.stop_ladder ?? null,
      };
    });

    const as_of = normalized?.[0]?.created_at ?? null;
    return NextResponse.json({ source: "supabase", as_of, signals: normalized });
  } catch (e: any) {
    const fb = await fallbackSignals();
    const filtered = label ? fb.filter((s: any) => s.label === label) : fb;
    const sliced = filtered.slice(0, Math.min(filtered.length, limit));
    const as_of = (sliced as any)?.[0]?.created_at ?? (sliced as any)?.[0]?.as_of ?? null;
    return NextResponse.json({ source: "fallback", as_of, error: e?.message ?? "unknown", signals: sliced });
  }
}
