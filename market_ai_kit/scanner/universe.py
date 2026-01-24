from __future__ import annotations

from typing import Dict, List


def build_universe(cfg: Dict) -> Dict[str, List[str]]:
    u = cfg.get("universe", {})
    core_etfs: List[str] = u.get("core_etfs", [])
    us_large_caps: List[str] = u.get("us_large_caps", [])
    china_watchlist: List[str] = u.get("china_watchlist", [])

    scan_list: List[str] = []
    scan_list += core_etfs
    scan_list += us_large_caps
    scan_list += china_watchlist

    # de-dupe, preserve order
    seen = set()
    deduped: List[str] = []
    for t in scan_list:
        if not t or t in seen:
            continue
        seen.add(t)
        deduped.append(t)

    return {
        "scan_list": deduped,
        "core_etfs": list(dict.fromkeys(core_etfs)),
        "us_large_caps": list(dict.fromkeys(us_large_caps)),
        "china_watchlist": list(dict.fromkeys(china_watchlist)),
    }
