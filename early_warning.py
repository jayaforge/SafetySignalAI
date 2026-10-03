"""Statistical Early Warning (windowed count comparison). NOT AI prediction."""
import pandas as pd
from math import exp, factorial
from config import EARLY_WARNING as EW, EW_CRITICAL as EC, EW_NOTE
def poisson_sf(k, mu): return 1 - sum(exp(-mu) * mu ** i / factorial(i) for i in range(k))
def _level(cur, prev):
    if prev == 0: return "CRITICAL" if cur >= EC["min_current_if_new"] else "HIGH"
    return "CRITICAL" if cur >= EC["min_current"] and cur >= EC["growth_factor"] * prev else "HIGH"
def detect_emerging(d, now=None):
    """d needs site, reported_at, rules(list). Trigger: current >= min_current AND current >= factor x previous."""
    if d.empty: return []
    d = d.copy(); d["t"] = pd.to_datetime(d.reported_at); now = pd.to_datetime(now) if now is not None else d.t.max()
    w = pd.Timedelta(days=EW["window_days"]); e = d.explode("rules").dropna(subset=["rules"]); out = []
    for (site, rule), g in e.groupby(["site", "rules"]):
        cur = int(((g.t > now - w) & (g.t <= now)).sum()); prev = int(((g.t > now - 2 * w) & (g.t <= now - w)).sum())
        if cur >= EW["min_current"] and cur >= EW["growth_factor"] * prev:
            growth_pct = round((cur - prev) / prev * 100, 1) if prev > 0 else None
            signal_text = "NEW SPIKE" if prev == 0 else f"+{growth_pct:.1f}%"
            out.append({
                "site": site, "hazard": rule, "window_start": str(now - w), "window_end": str(now),
                "previous_count": prev, "current_count": cur,
                "growth_percent": growth_pct, "signal": signal_text,
                "level": _level(cur, prev),
                "p_value_indicative": round(poisson_sf(cur, max(prev, 0.5)), 4),
                "reason": f"Rapid increase in repeated {rule} observations ({prev} -> {cur} reports in {EW['window_days']}-day windows).",
                "note": EW_NOTE
            })
    return sorted(out, key=lambda a: (a["level"] != "CRITICAL", -a["current_count"]))
def cross_site_clusters(d, now=None, min_sites=3):
    """Same hazard rising across several sites in the current window."""
    if d.empty: return []
    d = d.copy(); d["t"] = pd.to_datetime(d.reported_at); now = pd.to_datetime(now) if now is not None else d.t.max(); w = pd.Timedelta(days=EW["window_days"])
    e = d.explode("rules").dropna(subset=["rules"]); out = []
    for rule, g in e.groupby("rules"):
        c = g[(g.t > now - w) & (g.t <= now)]; p = g[(g.t > now - 2 * w) & (g.t <= now - w)]
        if c.site.nunique() >= min_sites and len(c) > len(p):
            out.append({"hazard": rule, "sites": sorted(c.site.unique()), "current_count": len(c), "previous_count": len(p),
                        "message": f"{rule} observations increased across {c.site.nunique()} sites in the last {EW['window_days']} days.", "note": EW_NOTE})
    return out
