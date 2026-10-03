"""Ties validation -> relevance -> ML (type, SIF) -> rule engine -> barriers -> repeats -> risk -> actions. Seeds the demo DB."""
import os, re, random, datetime as dt
import pandas as pd
import database as db
from validation import validate_text, is_safety_relevant, NOT_SAFETY_MSG
from rules import detect_rules, detect_barriers
from risk import compute_risk
from model import SafetyModels
from repeats import SimilarityIndex, repeat_count
from actions import recommend
from early_warning import detect_emerging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "data", "models.pkl")
DEFAULT_TRAIN_CSV = os.path.join(BASE_DIR, "data", "reports.csv")

SEVS = ("Low", "Medium", "High")
def clean(s, n=3000): return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", str(s or "")).strip()[:n]
class Engine:
    def __init__(self, train_csv=DEFAULT_TRAIN_CSV, model_path=DEFAULT_MODEL_PATH):
        self.models = SafetyModels.get_or_train(train_csv, model_path)
    def analyze(self, text, site="Unknown", location="", activity="", role="", severity="Unspecified", reported_at=None, hist=None, active=frozenset(), with_similar=True):
        ok, t = validate_text(clean(text))
        if not ok: return {"error": t}
        ml = self.models.predict(t, force=True); rules, bars = detect_rules(t), detect_barriers(t); gate, _ = is_safety_relevant(t)
        # Relevance = rule-engine evidence, OR keyword gate confirmed by the ML relevance model.
        ml_rel = ml["relevant"]["label"] == 1; confirmed = bool(rules or bars or (gate and ml_rel))
        # Conservative policy: reject only when BOTH keyword gate and ML say non-safety. Disagreement -> kept, flagged for human review.
        if not (confirmed or gate or ml_rel):
            return {"relevant": False, "message": NOT_SAFETY_MSG, "risk": compute_risk(0, severity, "", 0, 0, safety_relevant=False)}
        when = pd.to_datetime(reported_at) if reported_at else pd.Timestamp.now()
        rtype, sif = ml["report_type"], ml["sif"]; names = [r["rule"] for r in rules]
        rep = max([repeat_count(hist, site, n, when) for n in names], default=0) if hist is not None and len(hist) else 0
        emerging = any((site, n) in active for n in names)
        risk = compute_risk(sif["sif_probability"], severity, rtype["label"], len(rules), len(bars), rep, emerging)
        why = []
        if not confirmed: why.append("Relevance uncertain: keyword gate and ML model disagree. Human review recommended.")
        if rules: why.append("Life-Saving Rule evidence: " + "; ".join(f'{r["rule"]} ("{r["evidence"]}")' for r in rules))
        if bars: why.append("Barrier failures: " + "; ".join(b["barrier"] for b in bars))
        if sif["terms"]: why.append("Words that pushed the SIF model: " + ", ".join(sif["terms"]))
        why.append(f'Classified {rtype["label"]} (model confidence estimate {rtype["confidence"]})')
        if rep: why.append(f"{rep} similar reports at {site} in the last 30 days")
        if emerging: why.append("Active statistical early-warning alert for this site and hazard")
        sim = SimilarityIndex(hist).query(t) if with_similar and hist is not None and len(hist) else []
        row = dict(reported_at=str(when)[:16], text=t, site=site, location=location, activity=activity, reporter_role=role, severity=severity, report_type=rtype["label"],
                   sif_prediction=sif["sif_level"], sif_confidence=sif["sif_probability"], risk_score=risk["score"], risk_level=risk["level"], risk_reasons=risk["reasons"],
                   hazards=names, life_saving_rules=rules, barriers=bars, repeat_count=rep)
        return {"relevant": True, "relevance_uncertain": not confirmed, "row": row, "risk": risk, "ml": ml, "rules": rules, "barriers": bars, "explanations": why, "similar": sim,
                "actions": recommend(names, risk["level"], when.to_pydatetime())}
def ingest(conn, eng, rows, hist=None, active_fn=None, keep_uncertain=False):
    saved, rej = 0, []
    hist_list = [] if hist is None else (hist if isinstance(hist, list) else hist.to_dict("records"))
    for i, r in enumerate(rows, start=2):
        sev = clean(r.get("severity")).title() or "Unspecified"
        if sev not in SEVS + ("Unspecified",): rej.append((i, f"Invalid severity '{sev[:20]}'")); continue
        try: when = pd.to_datetime(r.get("reported_at")) if clean(r.get("reported_at")) else pd.Timestamp.now()
        except Exception: rej.append((i, "Invalid date")); continue
        if pd.isna(when): rej.append((i, "Invalid date")); continue
        act = active_fn(when) if active_fn else frozenset()
        a = eng.analyze(r.get("text"), clean(r.get("site"), 60) or "Unknown", clean(r.get("location"), 60), clean(r.get("activity"), 60), clean(r.get("reporter_role"), 40), sev, when, hist_list, act, with_similar=False)
        if "error" in a: rej.append((i, a["error"])); continue
        if not a["relevant"]: rej.append((i, "Not a safety report (screened out)")); continue
        if a.get("relevance_uncertain") and not keep_uncertain: rej.append((i, "Relevance uncertain (not saved; submit singly to confirm)")); continue
        rid = db.add_report(conn, a["row"], commit=False); db.add_actions(conn, rid, a["actions"], commit=False); saved += 1
        nr = {**a["row"], "id": rid, "rules": a["row"]["hazards"], "_dt": when}
        hist_list.append(nr)
    conn.commit()
    return saved, rej
def refresh_alerts(conn):
    d = db.reports_df(conn); conn.execute("DELETE FROM alerts"); al = detect_emerging(d) if len(d) else []
    for a in al: db.add_alert(conn, a)
    return al
def seed(conn, eng=None, csv=DEFAULT_TRAIN_CSV):
    """Loads SYNTHETIC demo reports chronologically. Predictions on seeded rows are in-sample (model trained on same file) - demo only."""
    if eng is None:
        eng = Engine(train_csv=csv)
    d = pd.read_csv(csv).sort_values("reported_at"); rows = d.fillna("").to_dict("records")
    tmp = pd.DataFrame({"site": d.site, "reported_at": d.reported_at, "rules": [[r["rule"] for r in detect_rules(t)] for t in d.text]})
    al = detect_emerging(tmp); now = pd.to_datetime(d.reported_at).max(); start = now - pd.Timedelta(days=7)
    keys = {(a["site"], a["hazard"]) for a in al}
    ingest(conn, eng, rows, active_fn=lambda w: keys if w > start else frozenset(), keep_uncertain=True)
    refresh_alerts(conn); rnd = random.Random(3)
    for a in conn.execute("SELECT a.id,a.report_id FROM actions a JOIN reports r ON r.id=a.report_id WHERE r.reported_at < ?", (str(now - pd.Timedelta(days=3))[:16],)).fetchall():
        x = rnd.random()
        if x < .7: conn.execute("UPDATE actions SET status='Verified',resolution='(demo seed) completed',resolver='Demo Resolver',verifier='Demo Verifier',verified_at=? WHERE id=?", (str(now)[:16], a["id"]))
        elif x < .85: conn.execute("UPDATE actions SET status='In Progress' WHERE id=?", (a["id"],))
    conn.commit()
