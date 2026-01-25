from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import math
import time


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def _logit(p: float) -> float:
    p = _clamp(p, 1e-6, 1 - 1e-6)
    return math.log(p / (1 - p))


def wilson_ci(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% Wilson CI; robust for small n."""
    if n <= 0:
        return (0.0, 1.0)
    p = _clamp(p, 1e-6, 1 - 1e-6)
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2 * n)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p) / n) + (z * z) / (4 * n * n))
    return (_clamp(center - margin, 0.0, 1.0), _clamp(center + margin, 0.0, 1.0))


def confidence_from_ci(lo: float, hi: float) -> float:
    width = _clamp(hi - lo, 0.0, 1.0)
    return _clamp(1.0 - width, 0.0, 1.0)


WEIGHTS_PATH = Path("output/weights.json")


def load_weights() -> Dict[str, float]:
    if WEIGHTS_PATH.exists():
        try:
            return dict(json.loads(WEIGHTS_PATH.read_text(encoding="utf-8")))
        except Exception:
            return {}
    return {
        "prior": 0.55,
        "factor.volume_anomaly": 1.0,
        "factor.relative_strength": 1.0,
        "factor.learned_rule_edge": 1.0,
        "factor.fv_extension": 0.7,
        "factor.structure_breakout": 0.8,
        "factor.sentiment": 0.6,
    }


def save_weights(w: Dict[str, float]) -> None:
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS_PATH.write_text(json.dumps(w, indent=2, sort_keys=True), encoding="utf-8")


def state_buckets(card: Dict[str, Any]) -> Dict[str, str]:
    vol_z = float(card.get("vol_z") or 0.0)
    rs = float(card.get("rs_60d_vs_spy") or card.get("rs_vs_spy") or 0.0)
    labels = card.get("labels") or []

    plan = card.get("plan") or {}
    entry = (plan.get("entry") or {})
    style = str(entry.get("type", "unknown"))

    def b_vol(v: float) -> str:
        if v >= 2.5: return "vol_extreme"
        if v >= 1.2: return "vol_high"
        if v >= 0.4: return "vol_normal"
        return "vol_low"

    def b_rs(v: float) -> str:
        if v >= 0.12: return "rs_strong"
        if v >= 0.05: return "rs_pos"
        if v <= -0.05: return "rs_neg"
        return "rs_flat"

    stage = "ready" if "READY_CONFIRMED" in labels else "early_watch"
    return {"style": style, "vol": b_vol(vol_z), "rs": b_rs(rs), "stage": stage}


def extract_factors(card: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    vol_z = float(card.get("vol_z") or 0.0)
    rs = float(card.get("rs_60d_vs_spy") or card.get("rs_vs_spy") or 0.0)

    v_val = _clamp((vol_z - 0.5) / 2.0, -1.0, 1.0)
    out.append({"name": "volume_anomaly", "value": v_val, "conf": 0.9, "why": f"vol_z={vol_z:.2f}"})

    rs_val = _clamp(rs / 0.15, -1.0, 1.0)
    out.append({"name": "relative_strength", "value": rs_val, "conf": 0.9, "why": f"rs_vs_spy={rs:.4f}"})

    rules = card.get("learned_top_rules") or []
    if rules and isinstance(rules[0], dict):
        best = rules[0]
        h60 = best.get("h60") or {}
        wr = h60.get("win_rate", None)
        n = int(h60.get("samples", 0) or 0)
        if wr is not None:
            lr_val = _clamp((float(wr) - 0.5) / 0.2, -1.0, 1.0)
            lr_conf = _clamp(min(1.0, n / 80.0), 0.1, 1.0)
            out.append({
                "name": "learned_rule_edge",
                "value": lr_val,
                "conf": lr_conf,
                "why": f"rule={best.get('rule','?')} wr60={float(wr):.2f} n={n}",
            })
        else:
            out.append({"name": "learned_rule_edge", "value": 0.0, "conf": 0.2, "why": "no win_rate in learned rule"})
    else:
        out.append({"name": "learned_rule_edge", "value": 0.0, "conf": 0.2, "why": "no learned rules"})

    fv = card.get("fv") or {}
    try:
        price = float(card.get("price") or 0.0)
        fv_high = float(fv.get("high") or price)
        ext = (price - fv_high) / max(price, 1e-6)
        fv_val = _clamp(-ext * 6.0, -1.0, 1.0)
        out.append({"name": "fv_extension", "value": fv_val, "conf": 0.7, "why": f"price={price:.2f} fv_high={fv_high:.2f}"})
    except Exception:
        out.append({"name": "fv_extension", "value": 0.0, "conf": 0.0, "why": "missing fv/price"})

    labels = card.get("labels") or []
    out.append({"name": "structure_breakout", "value": 0.8 if "READY_CONFIRMED" in labels else 0.0, "conf": 0.6, "why": "READY_CONFIRMED" if "READY_CONFIRMED" in labels else "not confirmed"})

    s = card.get("sentiment_score", None)
    if s is not None:
        out.append({"name": "sentiment", "value": _clamp(float(s), -1, 1), "conf": float(card.get("sentiment_conf", 0.5)), "why": f"sent={float(s):.2f}"})

    return out


def _entry_ref(card: Dict[str, Any]) -> Optional[float]:
    plan = card.get("plan") or {}
    entry = (plan.get("entry") or {})
    if "trigger" in entry:
        return float(entry["trigger"])
    if "zone" in entry and isinstance(entry["zone"], dict):
        z = entry["zone"]
        return (float(z.get("low")) + float(z.get("high"))) / 2.0
    if "price" in card:
        return float(card["price"])
    return None


def _tp1_price(card: Dict[str, Any]) -> Optional[float]:
    plan = card.get("plan") or {}
    targets = plan.get("targets") or []
    if not targets:
        return None
    try:
        return float(targets[0].get("price"))
    except Exception:
        return None


def stop_candidates(card: Dict[str, Any]) -> List[Tuple[str, float, List[str]]]:
    plan = card.get("plan") or {}
    existing_stop = (plan.get("exit_if_wrong") or {}).get("stop", None)
    rng = (card.get("range") or {})
    range_low = rng.get("low", None)

    entry = _entry_ref(card)
    if entry is None:
        return []

    atr = float(card.get("atr_14") or 0.0)

    cands: List[Tuple[str, float, List[str]]] = []
    if existing_stop is not None:
        cands.append(("SL_plan", float(existing_stop), ["plan stop (structure/ATR)"]))
    if range_low is not None:
        cands.append(("SL_range_low", float(range_low), ["range low invalidation"]))

    if atr > 0:
        cands.append(("SL_atr_1_5", float(entry - 1.5 * atr), ["entry - 1.5*ATR (tighter)"]))
        cands.append(("SL_atr_2_5", float(entry - 2.5 * atr), ["entry - 2.5*ATR (wider)"]))

    out: Dict[str, Tuple[float, List[str]]] = {}
    for n, sp, why in cands:
        if math.isfinite(sp) and sp < entry:
            out[n] = (sp, why)
    return [(k, v[0], v[1]) for k, v in out.items()]


@dataclass(frozen=True)
class LadderRow:
    name: str
    stop_price: float
    p: float
    confidence: float
    rr: float
    ev: float
    why: List[str]


def score_card(
    card: Dict[str, Any],
    *,
    weights: Optional[Dict[str, float]] = None,
    outcome_lookup: Optional[Any] = None,
) -> Dict[str, Any]:
    t0 = time.time()
    weights = weights or load_weights()

    entry = _entry_ref(card)
    tp1 = _tp1_price(card)
    if entry is None or tp1 is None:
        return {"probability": 0.0, "confidence": 0.0, "stop_ladder": [], "chosen_stop": None, "why": ["missing entry/TP1"], "runtime_ms": int((time.time()-t0)*1000)}

    prior = float(_clamp(weights.get("prior", 0.55), 0.05, 0.95))
    lo = _logit(prior)

    st = state_buckets(card)
    factors = extract_factors(card)

    why_lines: List[str] = [f"state={st}"]
    for f in factors:
        w = float(weights.get(f"factor.{f['name']}", 1.0))
        v = float(f["value"])
        c = float(f["conf"])
        lo += _clamp(v, -1, 1) * _clamp(c, 0, 1) * w
        why_lines.append(f"{f['name']}: v={v:.2f} c={c:.2f} w={w:.2f} ({f['why']})")

    base_p = float(_sigmoid(lo))

    ladder: List[LadderRow] = []
    for name, sp, why0 in stop_candidates(card):
        p = base_p
        why = why_lines[:] + why0

        if outcome_lookup is not None:
            try:
                p2, n2, why2 = outcome_lookup(st, entry, tp1, sp)
                if p2 is not None:
                    p = float(_clamp(float(p2), 0.01, 0.99))
                    why = list(why2) + list(why0)
                    n = int(n2 or 0)
                else:
                    n = 0
            except Exception:
                n = 0
        else:
            n = 0

        lo_ci, hi_ci = wilson_ci(p, max(n, 1))
        conf = confidence_from_ci(lo_ci, hi_ci)

        risk = entry - sp
        reward = tp1 - entry
        rr = (reward / risk) if (risk > 0 and reward > 0) else 0.0
        ev = (p * rr - (1 - p)) if rr > 0 else -999.0

        ladder.append(LadderRow(name=name, stop_price=sp, p=p, confidence=conf, rr=float(rr), ev=float(ev), why=why))

    ladder.sort(key=lambda x: x.ev, reverse=True)
    chosen = ladder[0] if ladder else None

    return {
        "probability": float(chosen.p) if chosen else base_p,
        "confidence": float(chosen.confidence) if chosen else 0.0,
        "stop_ladder": [r.__dict__ for r in ladder],
        "chosen_stop": (chosen.__dict__ if chosen else None),
        "why": (chosen.why[:8] if chosen else why_lines[:6]),
        "runtime_ms": int((time.time()-t0)*1000),
    }
