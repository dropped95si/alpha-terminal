from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple

import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

def _req(method: str, path: str, params: Dict[str, str] | None = None, json_body: Any = None) -> requests.Response:
    if not SUPABASE_URL or not SERVICE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")
    url = f"{SUPABASE_URL}{path}"
    return requests.request(method, url, headers=HEADERS, params=params, json=json_body, timeout=30)

def _get(path: str, params: Dict[str, str]) -> Any:
    r = _req("GET", path, params=params)
    if r.status_code >= 300:
        raise RuntimeError(f"GET {path} failed: {r.status_code} {r.text}")
    return r.json()

def _upsert(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    r = _req("POST", path, json_body=rows)
    if r.status_code >= 300:
        raise RuntimeError(f"UPSERT {path} failed: {r.status_code} {r.text}")

def main() -> None:
    # Pull recent outcomes joined with signals (last ~180 days of scans)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat().replace("+00:00", "Z")

    # PostgREST embed: outcomes -> signals
    rows = _get(
        "/rest/v1/outcomes",
        params={
            "select": "horizon_days,return_pct,signal_id,signals(ticker,learned_top_rules)",
            "created_at": f"gte.{cutoff}",
            "limit": "10000",
        },
    )

    bucket: Dict[Tuple[str, str, int], List[float]] = defaultdict(list)

    for r in rows:
        sig = r.get("signals") or {}
        ticker = sig.get("ticker")
        if not ticker:
            continue
        horizon = int(r["horizon_days"])
        ret = float(r["return_pct"])

        rules = sig.get("learned_top_rules") or []
        # learned_top_rules might be list of dicts with 'rule' key or list of strings
        norm_rules: List[str] = []
        if isinstance(rules, list):
            for it in rules:
                if isinstance(it, str):
                    norm_rules.append(it)
                elif isinstance(it, dict) and it.get("rule"):
                    norm_rules.append(str(it["rule"]))
        if not norm_rules:
            norm_rules = ["UNSPECIFIED"]

        for rule in norm_rules:
            bucket[(ticker, rule, horizon)].append(ret)

    upserts: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for (ticker, rule, horizon), rets in bucket.items():
        samples = len(rets)
        wins = sum(1 for x in rets if x > 0)
        win_rate = wins / samples if samples else 0.0
        avg_return = sum(rets) / samples if samples else 0.0
        expectancy = avg_return  # simple v1

        upserts.append(
            {
                "ticker": ticker,
                "rule": rule,
                "horizon_days": horizon,
                "samples": samples,
                "win_rate": float(win_rate),
                "avg_return": float(avg_return),
                "expectancy": float(expectancy),
                "updated_at": now,
            }
        )

    # Upsert in chunks
    chunk = 500
    for i in range(0, len(upserts), chunk):
        _upsert("/rest/v1/rule_stats", upserts[i : i + chunk])

    print(f"Upserted rule_stats rows: {len(upserts)}")

if __name__ == "__main__":
    main()
