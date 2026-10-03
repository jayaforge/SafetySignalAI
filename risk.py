"""Transparent configurable risk engine. Weights are PROTOTYPE values (see config.py)."""
from config import RISK_WEIGHTS as W, RISK_LEVELS
def level_for(score):
    for floor, name in RISK_LEVELS:
        if score >= floor: return name
def compute_risk(sif_conf, severity, report_type, n_rules, n_barriers, repeat_count=0, emerging=False, safety_relevant=True):
    if not safety_relevant:
        return {"score": None, "level": "N/A", "reasons": ["Non-safety input: no safety risk level assigned"]}
    parts = []
    sif = round(max(0.0, min(1.0, sif_conf)) * W["sif_max"])
    parts.append((sif, "SIF potential (model confidence estimate)"))
    parts.append((W["severity"].get(severity, 0), f"Reported severity: {severity}"))
    parts.append((W["type"].get(report_type, 0), f"Report type: {report_type}"))
    if n_rules: parts.append((W["life_saving_rule"], "Life-Saving Rule triggered"))
    if n_barriers: parts.append((W["barrier_failure"], "Barrier failure"))
    if repeat_count >= 1: parts.append((min(W["repeat_max"], 5 * repeat_count), f"Repeat hazard ({repeat_count} similar)"))
    if emerging: parts.append((W["emerging"], "Active emerging-risk alert"))
    parts = [(p, r) for p, r in parts if p > 0]
    score = min(100, sum(p for p, _ in parts))
    return {"score": score, "level": level_for(score), "reasons": [f"+{p} {r}" for p, r in parts]}
