"""Statistical trend views. Each answers one safety question."""
import pandas as pd
def weekly(d, mask=None, col="reported_at"):
    "Q: Is the number of (SIF / high-risk) reports rising week over week?"
    x = d if mask is None else d[mask]; t = pd.to_datetime(x[col])
    return t.dt.to_period("W").dt.start_time.value_counts().sort_index().rename("count").reset_index().rename(columns={"reported_at": "week", "index": "week"})
def site_sif_density(d, sif_col="sif_flag"):
    "Q: Which sites have the highest share of SIF-potential reports? (counts shown so small samples are visible)"
    g = d.groupby("site")[sif_col].agg(sif="sum", total="count"); g["density_pct"] = (100 * g.sif / g.total).round(1); return g.sort_values("density_pct", ascending=False)
def activity_risk(d, sif_col="sif_flag"):
    "Q: Which activities carry the most SIF-potential reports?"
    g = d.groupby("activity")[sif_col].agg(sif="sum", total="count"); g["density_pct"] = (100 * g.sif / g.total).round(1); return g.sort_values("sif", ascending=False)
def rule_frequency(d):
    "Q: Which Life-Saving Rules are triggered most?"
    return d.explode("rules").dropna(subset=["rules"]).rules.value_counts()
def type_distribution(d): return d.report_type.value_counts()
def hidden_risk(d):
    "Q: Which reports were logged Low/Medium but scored HIGH/CRITICAL by the risk engine?"
    return d[d.severity.isin(["Low", "Medium"]) & d.risk_level.isin(["HIGH", "CRITICAL"])]
