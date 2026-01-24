from __future__ import annotations

import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

HORIZONS = [20, 60, 90]

def _req(method: str, path: str, params: Optional[Dict[str, str]] = None, json_body: Any = None) -> requests.Response:
    if not SUPABASE_URL or not SERVICE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY env vars")
    url = f"{SUPABASE_URL}{path}"
    r = requests.request(method, url, headers=HEADERS, params=params, json=json_body, timeout=30)
    return r

def _get_json(method: str, path: str, params: Optional[Dict[str, str]] = None) -> Any:
    r = _req(method, path, params=params)
    if r.status_code >= 300:
        raise RuntimeError(f"{method} {path} failed: {r.status_code} {r.text}")
    return r.json()

def _post_json(path: str, rows: List[Dict[str, Any]]) -> None:
    r = _req("POST", path, json_body=rows)
    if r.status_code >= 300:
        raise RuntimeError(f"POST {path} failed: {r.status_code} {r.text}")

def _iso_to_dt(s: str) -> datetime:
    # Supabase returns ISO with Z
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

def _nearest_idx(df: pd.DataFrame, ts: datetime) -> Optional[pd.Timestamp]:
    if df.empty:
        return None
    # Use index as tz-aware; yfinance returns tz-naive timestamps in UTC for daily, often.
    idx = df.index
    # Make comparable
    if getattr(idx, "tz", None) is None:
        ts2 = ts.replace(tzinfo=None)
    else:
        ts2 = ts.astimezone(idx.tz)
    # Find nearest
    pos = idx.get_indexer([ts2], method="nearest")[0]
    if pos < 0:
        return None
    return idx[pos]

def _fetch_window(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    # yfinance needs strings
    df = yf.download(
        ticker,
        start=start.date().isoformat(),
        end=(end.date() + timedelta(days=1)).isoformat(),
        interval="1d",
        progress=False,
        auto_adjust=False,
    )
    if df is None or df.empty:
        return pd.DataFrame()
    # Normalize columns
    df = df.rename(columns={c: c.lower() for c in df.columns})
    return df

def _calc_outcome(df: pd.DataFrame, as_of: datetime, horizon_days: int, stop_price: Optional[float], tp_price: Optional[float]) -> Optional[Dict[str, Any]]:
    if df.empty:
        return None

    entry_idx = _nearest_idx(df, as_of)
    if entry_idx is None:
        return None

    entry_close = float(df.loc[entry_idx, "close"])
    # horizon in trading days, not calendar days: use row offset
    entry_pos = df.index.get_loc(entry_idx)
    end_pos = entry_pos + horizon_days
    if end_pos >= len(df.index):
        return None  # not enough future data yet

    window = df.iloc[entry_pos : end_pos + 1].copy()
    end_close = float(window["close"].iloc[-1])
    ret_pct = (end_close / entry_close - 1.0) * 100.0

    mfe_pct = (float(window["high"].max()) / entry_close - 1.0) * 100.0
    mae_pct = (float(window["low"].min()) / entry_close - 1.0) * 100.0

    hit_stop = False
    hit_tp = False
    if stop_price and stop_price > 0:
        hit_stop = bool((window["low"] <= float(stop_price)).any())
    if tp_price and tp_price > 0:
        hit_tp = bool((window["high"] >= float(tp_price)).any())

    return {
        "horizon_days": int(horizon_days),
        "return_pct": float(ret_pct),
        "hit_tp": bool(hit_tp),
        "hit_stop": bool(hit_stop),
        "mfe_pct": float(mfe_pct),
        "mae_pct": float(mae_pct),
    }

def main() -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(HORIZONS) + 5)

    # Get recent scan runs (up to 50)
    scan_runs = _get_json(
        "GET",
        "/rest/v1/scan_runs",
        params={
            "select": "id,as_of",
            "order": "as_of.desc",
            "limit": "50",
        },
    )

    total_inserts = 0

    for run in scan_runs:
        run_id = run["id"]
        as_of = _iso_to_dt(run["as_of"])
        if as_of > cutoff:
            continue  # too recent, can't score 90d yet

        # signals for that run
        signals = _get_json(
            "GET",
            "/rest/v1/signals",
            params={
                "select": "id,ticker,stop,targets",
                "scan_run_id": f"eq.{run_id}",
                "limit": "5000",
            },
        )
        if not signals:
            continue

        for s in signals:
            signal_id = s["id"]
            ticker = s["ticker"]
            stop_price = None
            try:
                stop_price = float((s.get("stop") or {}).get("stop") or (s.get("stop") or {}).get("price") or 0) or None
            except Exception:
                stop_price = None
            tp_price = None
            try:
                targets = s.get("targets") or []
                if targets and isinstance(targets, list):
                    tp_price = float(targets[0].get("price") or 0) or None
            except Exception:
                tp_price = None

            # Skip if outcomes already exist for this signal (cheap check per horizon)
            existing = _get_json(
                "GET",
                "/rest/v1/outcomes",
                params={
                    "select": "id,horizon_days",
                    "signal_id": f"eq.{signal_id}",
                    "limit": "200",
                },
            )
            existing_h = {int(x["horizon_days"]) for x in existing} if existing else set()

            # Fetch window once per ticker & run
            start = as_of - timedelta(days=10)
            end = as_of + timedelta(days=200)  # enough for 90 trading days usually
            df = _fetch_window(ticker, start, end)
            if df.empty:
                continue

            rows_to_insert: List[Dict[str, Any]] = []
            for h in HORIZONS:
                if h in existing_h:
                    continue
                out = _calc_outcome(df, as_of, h, stop_price, tp_price)
                if out is None:
                    continue
                out["signal_id"] = signal_id
                rows_to_insert.append(out)

            if rows_to_insert:
                _post_json("/rest/v1/outcomes", rows_to_insert)
                total_inserts += len(rows_to_insert)
                time.sleep(0.1)  # be nice to APIs

    print(f"Inserted outcomes rows: {total_inserts}")

if __name__ == "__main__":
    main()
