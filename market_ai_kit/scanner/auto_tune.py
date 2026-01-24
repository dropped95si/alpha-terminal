from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
import numpy as np

@dataclass
class AutoThresholds:
    vol_z_min: float
    near_breakout_pct: float
    fv_max_extension_atr: float
    ready_confirm_closes: int

def tune_thresholds(preview: List[Dict], cfg: Dict) -> AutoThresholds:
    if not preview:
        return AutoThresholds(vol_z_min=0.4, near_breakout_pct=0.995, fv_max_extension_atr=0.75, ready_confirm_closes=1)

    volzs = np.array([float(x.get("vol_z", 0.0)) for x in preview], dtype=float)
    volzs = volzs[np.isfinite(volzs)]
    if len(volzs) == 0:
        vol_z_min = 0.4
        med = 0.0
    else:
        q = float(cfg.get("auto", {}).get("vol_z_quantile", 0.60))
        vol_z_min = float(np.quantile(volzs, q))
        med = float(np.median(volzs))

    near_breakout_pct = float(cfg.get("auto", {}).get("near_breakout_pct", 0.995))
    fv_max_extension_atr = float(cfg.get("auto", {}).get("fv_max_extension_atr", 0.75))
    ready_confirm_closes = 2 if med < 0.20 else 1

    return AutoThresholds(
        vol_z_min=round(vol_z_min, 2),
        near_breakout_pct=near_breakout_pct,
        fv_max_extension_atr=fv_max_extension_atr,
        ready_confirm_closes=ready_confirm_closes,
    )
