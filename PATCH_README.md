## Patch v2 audit improvements
- UI + API now normalize entry types (price/trigger/zone)
- daily-scan workflow posts scan payload to ingest endpoint

# Patch: Ingest Token + Signals API (Supabase-first with fallback)

## What this patch adds
- Fixes TypeScript `lib/types.ts` (removes invalid `...`)
- Adds `lib/signal.ts` canonical signal schema + normalizer
- Adds `app/api/signals` (reads Supabase if configured, otherwise falls back to public/data JSON)
- Hardens `app/api/ingest-scan` with `INGEST_TOKEN` auth and clearer errors
- Updates homepage to load via `/api/signals` (no direct browser-to-Supabase dependency)

## Required env vars on Vercel (server)
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `INGEST_TOKEN`  (new)

## Required secrets on GitHub Actions
- `INGEST_URL` (e.g. https://<your-vercel-domain>/api/ingest-scan)
- `INGEST_TOKEN` (must match Vercel)

## Quick curl test
curl -X POST "$INGEST_URL" -H "Content-Type: application/json" -H "x-ingest-token: $INGEST_TOKEN" --data-binary @market_ai_kit/output/full_scan_payload.json

