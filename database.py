"""SQLite layer. All queries are parameterized."""
import sqlite3, json, datetime as dt
import pandas as pd
SCHEMA = """
CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, reported_at TEXT, text TEXT NOT NULL,
 site TEXT, location TEXT, activity TEXT, reporter_role TEXT, severity TEXT, report_type TEXT, sif_prediction TEXT, sif_confidence REAL,
 risk_score INTEGER, risk_level TEXT, risk_reasons TEXT, hazards TEXT, life_saving_rules TEXT, barriers TEXT, repeat_count INTEGER DEFAULT 0,
 status TEXT DEFAULT 'Open', review_status TEXT DEFAULT 'Pending', reviewer TEXT, review_comment TEXT, original_prediction TEXT, reviewed_at TEXT);
CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER, action TEXT NOT NULL, priority TEXT, department TEXT,
 owner TEXT, due_date TEXT, status TEXT DEFAULT 'Open', resolution TEXT, resolver TEXT, resolved_at TEXT, verifier TEXT, verified_at TEXT,
 FOREIGN KEY(report_id) REFERENCES reports(id));
CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT, hazard TEXT, window_start TEXT, window_end TEXT,
 previous_count INTEGER, current_count INTEGER, growth_percent REAL, level TEXT, status TEXT DEFAULT 'Active', created_at TEXT);
"""
JSON_COLS = ("risk_reasons", "hazards", "life_saving_rules", "barriers")
def connect(path="safetysignal.db"):
    c = sqlite3.connect(path); c.row_factory = sqlite3.Row; c.executescript(SCHEMA); return c
def add_report(conn, r, commit=True):
    r = dict(r); r.setdefault("created_at", dt.datetime.now().isoformat(timespec="seconds"))
    for k in JSON_COLS:
        if k in r and not isinstance(r[k], str): r[k] = json.dumps(r[k])
    cols = [k for k in r if k in {x[1] for x in conn.execute("PRAGMA table_info(reports)")}]
    cur = conn.execute(f"INSERT INTO reports({','.join(cols)}) VALUES({','.join('?'*len(cols))})", [r[k] for k in cols])
    if commit: conn.commit()
    return cur.lastrowid
def add_actions(conn, report_id, actions, commit=True):
    for a in actions:
        conn.execute("INSERT INTO actions(report_id,action,priority,department,owner,due_date) VALUES(?,?,?,?,?,?)",
                     (report_id, a["action"], a["priority"], a["department"], a["owner"], a["due_date"]))
    if commit: conn.commit()
def add_alert(conn, a):
    conn.execute("INSERT INTO alerts(site,hazard,window_start,window_end,previous_count,current_count,growth_percent,level,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                 (a["site"], a["hazard"], a["window_start"], a["window_end"], a["previous_count"], a["current_count"], a["growth_percent"], a["level"], dt.datetime.now().isoformat(timespec="seconds"))); conn.commit()
def review_report(conn, report_id, decision, reviewer, comment="", new_type=None):
    """Human-in-the-loop. Stores original prediction; never feeds model training."""
    if decision not in ("Confirmed", "Overridden"): raise ValueError("Decision must be Confirmed or Overridden.")
    if not reviewer or not reviewer.strip(): raise ValueError("Reviewer name is required.")
    row = conn.execute("SELECT report_type,sif_prediction,risk_level FROM reports WHERE id=?", (report_id,)).fetchone()
    if row is None: raise ValueError("Report not found.")
    conn.execute("UPDATE reports SET review_status=?,reviewer=?,review_comment=?,original_prediction=?,reviewed_at=?,report_type=COALESCE(?,report_type) WHERE id=?",
                 (decision, reviewer.strip(), (comment or "")[:1000], json.dumps(dict(row)), dt.datetime.now().isoformat(timespec="seconds"), new_type, report_id)); conn.commit()
def df(conn, table="reports"):
    d = pd.read_sql_query(f"SELECT * FROM {'actions' if table == 'actions' else 'alerts' if table == 'alerts' else 'reports'}", conn)
    if table == "alerts" and not d.empty:
        d["growth_percent"] = d.apply(lambda r: None if (r["previous_count"] == 0 or pd.isna(r["growth_percent"])) else float(r["growth_percent"]), axis=1)
        d["signal"] = d.apply(lambda r: "NEW SPIKE" if r["previous_count"] == 0 else (f"+{r['growth_percent']:.1f}%" if r["growth_percent"] is not None else "NEW SPIKE"), axis=1)
    return d

def reports_df(conn):
    d = df(conn)
    for c in JSON_COLS: d[c] = d[c].map(lambda s: json.loads(s) if isinstance(s, str) and s else [])
    d["rules"] = d.life_saving_rules.map(lambda l: [x["rule"] if isinstance(x, dict) else x for x in l])
    d["sif_flag"] = (d.sif_confidence.fillna(0) >= 0.5).astype(int)
    return d
