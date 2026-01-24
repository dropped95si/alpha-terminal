import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { readFile } from "node:fs/promises";
import path from "node:path";

import type { CardsFile } from "@/lib/types";
import { cardsFileToSignals, type Signal } from "@/lib/signal";

export const runtime = "nodejs";


function normalizeEntry(entry: any) {
  if (!entry) return { price: null };
  if (typeof entry === "number") return { price: entry };
  if (typeof entry.price === "number") return entry;
  if (typeof entry.trigger === "number") return { ...entry, price: entry.trigger };
  if (entry.zone && typeof entry.zone.low === "number" && typeof entry.zone.high === "number") {
    return { ...entry, price: (entry.zone.low + entry.zone.high) / 2 };
  }
  return entry;
}

function supabaseIfConfigured() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  return createClient(url, key);
}

async function readJsonFromPublic<T>(rel: string): Promise<T> {
  const full = path.join(process.cwd(), "public", rel);
  const raw = await readFile(full, "utf-8");
  return JSON.parse(raw) as T;
}

async function fallbackSignals(): Promise<Signal[]> {
  const [ready, early, watch] = await Promise.all([
    readJsonFromPublic<CardsFile>("data/ready.json"),
    readJsonFromPublic<CardsFile>("data/early.json"),
    readJsonFromPublic<CardsFile>("data/watch.json"),
  ]);

  return [
    ...cardsFileToSignals(ready, "READY_CONFIRMED"),
    ...cardsFileToSignals(early, "EARLY"),
    ...cardsFileToSignals(watch, "WATCH"),
  ].map((s: any) => ({ ...s, entry: normalizeEntry(s.entry) }));
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const limit = Number(url.searchParams.get("limit") ?? "200");
  const label = url.searchParams.get("label"); // optional

  const supabase = supabaseIfConfigured();

  if (supabase) {
    let q = supabase
      .from("signals")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(Math.min(Math.max(limit, 1), 1000));

    if (label) q = q.eq("label", label);

    const { data, error } = await q;

    if (error) {
      const fb = await fallbackSignals();
      return NextResponse.json({ source: "fallback_after_db_error", error: error.message, signals: fb });
    }

    const normalized = (data ?? []).map((s: any) => ({ ...s, entry: normalizeEntry(s.entry) }));
    return NextResponse.json({ source: "supabase", signals: normalized });
  }

  const fb = await fallbackSignals();
  const filtered = label ? fb.filter((s) => s.label === label) : fb;
  return NextResponse.json({ source: "fallback", signals: filtered.slice(0, Math.min(filtered.length, limit)) });
}
