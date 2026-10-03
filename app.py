import os, json, io, math
import pandas as pd, numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import database as db, actions as A, trends as T
from pipeline import Engine, ingest, seed, refresh_alerts, clean, SEVS
from early_warning import cross_site_clusters
import config as C
def sanitize_json(v):
    if isinstance(v, float) and (math.isnan(v) or pd.isna(v)): return None
    if isinstance(v, dict): return {k: sanitize_json(x) for k, x in v.items()}
    if isinstance(v, list): return [sanitize_json(x) for x in v]
    return v
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)       # no hardcoded secret
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024                      # 2 MB upload limit
DB = os.environ.get("SAFETYSIGNAL_DB", "safetysignal.db"); _eng = None
def engine():
    global _eng
    if _eng is None: _eng = Engine()
    return _eng
def conn():
    c = db.connect(DB)
    if c.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0 and os.path.exists("data/reports.csv"): seed(c, engine())
    return c
def asof(d): return pd.to_datetime(d.reported_at).max().to_pydatetime() if len(d) else pd.Timestamp.now().to_pydatetime()
@app.context_processor
def ctx(): return dict(DISCLAIMER=C.DISCLAIMER, RISK_NOTE=C.RISK_NOTE)
@app.route("/", methods=["GET", "POST"])
def index():
    result = None; c = conn()
    if request.method == "POST":
        f = request.form; sev = f.get("severity", "Unspecified"); sev = sev if sev in SEVS else "Unspecified"
        h = db.reports_df(c); site = clean(f.get("site"), 60) or "Unknown"
        al = db.df(c, "alerts"); active = frozenset(zip(al.site, al.hazard))
        result = engine().analyze(f.get("text"), site, clean(f.get("location"), 60), clean(f.get("activity"), 60), clean(f.get("role"), 40), sev, None, h if len(h) else None, active)
        if result.get("relevant") and result.get("relevance_uncertain") and not f.get("confirm"): result["needs_confirm"] = dict(f)
        elif result.get("relevant"):
            rid = db.add_report(c, result["row"]); db.add_actions(c, rid, result["actions"]); result["saved_id"] = rid; refresh_alerts(c)
    sites = sorted(db.df(c).site.dropna().unique()); return render_template("index.html", result=result, sites=sites, note=C.ACTION_NOTE)
@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("file")
    if not f or not f.filename: flash("No file selected.", "err"); return redirect(url_for("reports"))
    if not f.filename.lower().endswith(".csv"): flash("Only .csv files are accepted.", "err"); return redirect(url_for("reports"))
    try: d = pd.read_csv(io.BytesIO(f.read()), dtype=str, encoding_errors="replace").fillna("")
    except Exception: flash("Could not read this file as CSV. Check the format and try again.", "err"); return redirect(url_for("reports"))
    d.columns = [str(x).strip().lower() for x in d.columns]
    if "text" not in d.columns: flash("Missing required column: text. Optional: reported_at, site, location, activity, reporter_role, severity.", "err"); return redirect(url_for("reports"))
    d = d[d.text.str.strip() != ""]
    if d.empty: flash("The CSV has no rows with report text.", "err"); return redirect(url_for("reports"))
    if len(d) > 2000: flash("Too many rows (limit 2000 per upload).", "err"); return redirect(url_for("reports"))
    c = conn(); h = db.reports_df(c); al = db.df(c, "alerts"); keys = frozenset(zip(al.site, al.hazard))
    saved, rej = ingest(c, engine(), d.to_dict("records"), h if len(h) else None, lambda w: keys); refresh_alerts(c)
    flash(f"Saved {saved} safety reports. Rejected/screened out {len(rej)}." + (" First issues: " + "; ".join(f"row {r}: {m}" for r, m in rej[:5]) if rej else ""), "ok")
    return redirect(url_for("reports"))
@app.route("/reports")
def reports():
    d = db.reports_df(conn()); q = request.args
    if q.get("site"): d = d[d.site == q["site"]]
    if q.get("level"): d = d[d.risk_level == q["level"]]
    if q.get("hidden"): d = T.hidden_risk(d)
    return render_template("reports.html", rows=d.sort_values("reported_at", ascending=False).head(200).to_dict("records"), total=len(d), q=q)
@app.route("/actions", methods=["GET", "POST"])
def actions():
    c = conn()
    if request.method == "POST":
        try: A.advance(c, int(request.form["id"]), request.form["to"], request.form.get("person"), request.form.get("resolution")); flash("Action updated.", "ok")
        except (ValueError, KeyError) as e: flash(str(e), "err")
        return redirect(url_for("actions"))
    now = asof(db.df(c)); a = db.df(c, "actions"); rows = []
    for r in a.to_dict("records"):
        r["overdue"] = A.is_overdue(r, now); r["escalate"] = A.escalation_stage(r, now); r["next"] = A.ORDER[A.ORDER.index(r["status"]) + 1] if r["status"] != "Verified" else None; rows.append(r)
    rows.sort(key=lambda r: (not r["overdue"], r["status"] == "Verified", r["due_date"] or "")); return render_template("actions.html", rows=rows[:300], note=C.ESCALATION_NOTE, asof=now, total=len(rows))
@app.route("/alerts")
def alerts():
    c = conn(); d = db.reports_df(c); al = db.df(c, "alerts")
    alerts_data = [sanitize_json(r) for r in al.to_dict("records")]
    return render_template("alerts.html", alerts=alerts_data, clusters=cross_site_clusters(d) if len(d) else [], note=C.EW_NOTE)
@app.route("/review", methods=["GET", "POST"])
def review():
    c = conn()
    if request.method == "POST":
        try:
            nt = request.form.get("new_type") or None
            if nt not in (None, "Unsafe Act", "Unsafe Condition", "Near Miss"): raise ValueError("Invalid report type.")
            db.review_report(c, int(request.form["id"]), request.form["decision"], request.form.get("reviewer", ""), request.form.get("comment", ""), nt); flash("Review saved.", "ok")
        except (ValueError, KeyError) as e: flash(str(e), "err")
        return redirect(url_for("review"))
    d = db.reports_df(c); q = d[(d.review_status == "Pending") & d.risk_level.isin(["HIGH", "CRITICAL"])].sort_values("risk_score", ascending=False)
    audited = d[d.review_status.isin(["Confirmed", "Overridden"])].sort_values("reviewed_at", ascending=False).head(25)
    return render_template("review.html", rows=q.head(50).to_dict("records"), total=len(q), audited=audited.to_dict("records"), audited_total=len(audited))
@app.route("/evaluation")
def evaluation():
    p = "data/eval_results.json"; r = json.load(open(p)) if os.path.exists(p) else None; return render_template("evaluation.html", r=r)
@app.route("/dashboard")
def dashboard(): return render_template("dashboard.html")
@app.route("/api/dashboard")
def api_dashboard():
    c = conn(); d = db.reports_df(c); a = db.df(c, "actions"); al = db.df(c, "alerts"); now = asof(d)
    od = sum(A.is_overdue(r, now) for r in a.to_dict("records")); hc = d.risk_level.isin(["HIGH", "CRITICAL"])
    wk = lambda m: [{"week": str(r["week"])[:10], "count": int(r["count"])} for r in T.weekly(d, m).to_dict("records")]
    dens = T.site_sif_density(d).reset_index().to_dict("records"); rf = T.rule_frequency(d)
    bar = pd.Series([b["barrier"] for l in d.barriers for b in l]).value_counts() if len(d) else pd.Series(dtype=int)
    rec = d[d.reported_at >= str(pd.Timestamp(now) - pd.Timedelta(days=30))]
    rep = [{"site": s, "hazard": h, "count": int(n)} for (s, h), n in rec.explode("rules").dropna(subset=["rules"]).groupby(["site", "rules"]).size().items() if n >= 3]
    cols = ["id", "reported_at", "site", "severity", "risk_score", "risk_level", "sif_prediction", "text"]
    
    total_reports = len(d)
    sif_count = int(d.sif_flag.sum())
    hc_count = int(hc.sum())
    hc_pct = round(hc_count / total_reports * 100, 1) if total_reports > 0 else 0
    sif_pct = round(sif_count / total_reports * 100, 1) if total_reports > 0 else 0
    open_actions = int((a.status != "Verified").sum())
    clusters = cross_site_clusters(d) if len(d) else []
    
    try:
        asof_date_str = now.strftime("%d %b %Y")
    except Exception:
        asof_date_str = "02 Oct 2026"
    asof_formatted = f"Demo Data Snapshot • {asof_date_str}"
    
    payload = dict(
        asof=asof_formatted,
        asof_raw=str(now)[:16],
        kpi=dict(
            total=total_reports,
            sif=sif_count,
            high_critical=hc_count,
            open_actions=open_actions,
            overdue=int(od),
            emerging=len(al),
            hc_pct=hc_pct,
            sif_pct=sif_pct
        ),
        pulse=dict(
            total_reports=total_reports,
            hc_count=hc_count,
            hc_pct=hc_pct,
            sif_count=sif_count,
            sif_pct=sif_pct,
            emerging_count=len(al),
            cluster_count=len(clusters),
            pending_reviews=int(((d.review_status == "Pending") & hc).sum()),
            overdue_actions=int(od)
        ),
        alerts=al.to_dict("records"),
        clusters=clusters,
        weekly_sif=wk(d.sif_flag == 1),
        weekly_hc=wk(hc),
        types=T.type_distribution(d).to_dict(),
        sites=dens,
        rules=rf.to_dict(),
        barriers=bar.to_dict(),
        repeats=sorted(rep, key=lambda x: -x["count"])[:10],
        hidden=T.hidden_risk(d)[cols].sort_values("risk_score", ascending=False).head(8).to_dict("records"),
        critical=d[d.risk_level == "CRITICAL"][cols].sort_values("reported_at", ascending=False).head(8).to_dict("records"),
        review_pending=int(((d.review_status == "Pending") & hc).sum())
    )
    return jsonify(sanitize_json(payload))
@app.errorhandler(413)
def too_big(e): flash("File too large (limit 2 MB).", "err"); return redirect(url_for("reports"))
@app.errorhandler(500)
def err(e): return render_template("index.html", result={"error": "Something went wrong. Please check your input and try again."}, sites=[], note=""), 500
if __name__ == "__main__": app.run(debug=False)
