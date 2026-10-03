"""Integration and route test suite for SafetySignal AI using Flask test_client."""
import sys, os, io, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as flask_app
import database as db

client = flask_app.app.test_client()

def test_phase6_main_page():
    r = client.get("/")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    html = r.data.decode("utf-8")
    assert "<title>SafetySignal AI" in html
    assert "analyze a safety report" in html.lower()
    assert 'name="text"' in html
    assert "Analyze" in html
    print("Main page: OK")

    css = client.get("/static/style.css")
    assert css.status_code == 200 and len(css.data) > 500
    print(f"CSS loaded: OK ({len(css.data)} bytes)")

    js = client.get("/static/app.js")
    assert js.status_code == 200 and len(js.data) > 500
    print(f"JavaScript loaded: OK ({len(js.data)} bytes)")

    chart_js = client.get("/static/chart.umd.min.js")
    assert chart_js.status_code == 200 and len(chart_js.data) > 100000
    print(f"Offline Chart.js loaded: OK ({len(chart_js.data)} bytes)")

    for route in ["/dashboard", "/reports", "/alerts", "/actions", "/review", "/evaluation"]:
        res = client.get(route)
        assert res.status_code == 200, f"Failed route {route}: {res.status_code}"
        print(f"Route {route}: OK")

    api = client.get("/api/dashboard")
    assert api.status_code == 200
    data = api.get_json()
    assert "kpi" in data and "total" in data["kpi"]
    print(f"API /api/dashboard: OK, total reports = {data['kpi']['total']}")

def test_phase7_safety_report_analysis():
    print("\n--- Testing Phase 7: Safety Report Analysis ---")
    # TEST 1 - UNSAFE CONDITION
    t1 = "Oil was spilled near the main walkway. No one was injured, but workers could slip and fall."
    r1 = client.post("/", data={"text": t1, "site": "Duliajan", "severity": "Medium"})
    assert r1.status_code == 200
    assert "Risk" in r1.data.decode("utf-8")
    print("Test 1 (Unsafe condition): OK - Status 200, Result returned.")

    # TEST 2 - HIGH-RISK EVENT
    t2 = "A worker entered a restricted area without required PPE and was nearly struck by moving equipment. Immediate intervention was required."
    r2 = client.post("/", data={"text": t2, "site": "Duliajan", "severity": "High"})
    assert r2.status_code == 200
    h2 = r2.data.decode("utf-8")
    assert ("CRITICAL" in h2 or "HIGH" in h2)
    print("Test 2 (High-risk event): OK - Recognized HIGH/CRITICAL.")

    # TEST 3 - NEAR MISS
    t3 = "A forklift came very close to hitting a pedestrian at the warehouse entrance. No injury occurred."
    r3 = client.post("/", data={"text": t3, "site": "Duliajan", "severity": "Medium"})
    assert r3.status_code == 200
    assert "Risk" in r3.data.decode("utf-8")
    print("Test 3 (Near miss): OK - Status 200, Result returned.")

    # TEST 4 - UNSAFE ACT
    t4 = "A worker was operating machinery without wearing the required safety helmet."
    r4 = client.post("/", data={"text": t4, "site": "Duliajan", "severity": "Medium"})
    assert r4.status_code == 200
    assert "Risk" in r4.data.decode("utf-8")
    print("Test 4 (Unsafe act): OK - Status 200, Result returned.")

    # TEST 5 - AMBIGUOUS INPUT
    t5 = "Something is wrong near the machine."
    r5 = client.post("/", data={"text": t5, "site": "Duliajan", "severity": "Low"})
    assert r5.status_code == 200
    print("Test 5 (Ambiguous input): OK - Handled safely without crash.")

    # TEST 6 - EMPTY INPUT
    r6 = client.post("/", data={"text": "", "site": "Duliajan", "severity": "Low"})
    assert r6.status_code == 200
    h6 = r6.data.decode("utf-8").lower()
    assert "empty" in h6 or "too short" in h6 or "flash err" in h6
    print("Test 6 (Empty input): OK - Handled with validation message.")

    # TEST 7 - INVALID INPUT
    r7 = client.post("/", data={"text": "???!!!@@@ 12345 67890", "site": "Unknown", "severity": "InvalidSeverity"})
    assert r7.status_code == 200
    print("Test 7 (Invalid input): OK - Handled gracefully without crash.")

def test_phase8_repeat_duplicate_detection():
    print("\n--- Testing Phase 8: Duplicate / Repeat Detection ---")
    t1 = "Oil spill found near the warehouse entrance."
    r1 = client.post("/", data={"text": t1, "site": "Duliajan", "severity": "Medium"})
    assert r1.status_code == 200

    t2 = "There is an oil spill close to the warehouse entry area."
    r2 = client.post("/", data={"text": t2, "site": "Duliajan", "severity": "Medium"})
    assert r2.status_code == 200
    html = r2.data.decode("utf-8")
    sim_matches = re.findall(r"(\d+\.?\d*)%", html)
    print(f"Similar reports identified on live page: {len(sim_matches)}")
    assert len(sim_matches) > 0

def test_phase9_early_warning_and_trends():
    print("\n--- Testing Phase 9: Early Warning & Trends ---")
    r = client.get("/alerts")
    assert r.status_code == 200
    assert "Statistical Early Warning" in r.data.decode("utf-8")
    print("Alerts page rendered: OK")
    
    api = client.get("/api/dashboard").get_json()
    alerts = api.get("alerts", [])
    print(f"Active early warning alerts in system: {len(alerts)}")
    for a in alerts:
        print(f"  Alert: Site '{a['site']}' | Hazard '{a['hazard']}' | Level: {a['level']} | Prev: {a['previous_count']} -> Cur: {a['current_count']}")
    
    assert "weekly_sif" in api and "weekly_hc" in api and "types" in api and "sites" in api
    print("Trend metrics (weekly SIF, weekly High/Critical, types, site density): OK")

def test_phase10_actions_and_routing():
    print("\n--- Testing Phase 10: Action & Routing Logic ---")
    r = client.get("/actions")
    assert r.status_code == 200
    assert "corrective action" in r.data.decode("utf-8").lower()
    
    api = client.get("/api/dashboard").get_json()
    print(f"Open actions: {api['kpi']['open_actions']}, Overdue actions: {api['kpi']['overdue']}")

def test_phase11_csv_upload():
    print("\n--- Testing Phase 11: CSV Upload ---")
    valid_csv = "text,site,severity\nWorker observed without harness at height on scaffold,Duliajan,High\nGas detector calibration expired on drilling rig,Digboi,Medium\n"
    r1 = client.post("/upload", data={"file": (io.BytesIO(valid_csv.encode("utf-8")), "test_valid.csv")}, content_type="multipart/form-data", follow_redirects=True)
    assert r1.status_code == 200
    assert "Saved" in r1.data.decode("utf-8")
    print("1. Valid CSV upload: OK - Successfully processed and saved.")

    bad_csv = "description,location\nOil spill on road,Zone 1\n"
    r2 = client.post("/upload", data={"file": (io.BytesIO(bad_csv.encode("utf-8")), "bad_col.csv")}, content_type="multipart/form-data", follow_redirects=True)
    assert r2.status_code == 200
    assert "Missing required column: text" in r2.data.decode("utf-8")
    print("2. Missing 'text' column CSV: OK - Clear error message flashed.")

    empty_csv = "text,site\n"
    r3 = client.post("/upload", data={"file": (io.BytesIO(empty_csv.encode("utf-8")), "empty.csv")}, content_type="multipart/form-data", follow_redirects=True)
    assert r3.status_code == 200
    assert "no rows with report text" in r3.data.decode("utf-8").lower()
    print("3. Empty CSV: OK - Clear error message flashed.")

    r4 = client.post("/upload", data={"file": (io.BytesIO(b"random text"), "test.txt")}, content_type="multipart/form-data", follow_redirects=True)
    assert r4.status_code == 200
    assert "Only .csv files are accepted" in r4.data.decode("utf-8")
    print("4. Non-CSV file rejection: OK - Rejected with error message.")

    r5 = client.post("/upload", data={"file": (io.BytesIO(b""), "")}, content_type="multipart/form-data", follow_redirects=True)
    assert r5.status_code == 200
    assert "No file selected" in r5.data.decode("utf-8")
    print("5. No file selected: OK - Handled gracefully.")

def test_phase12_database_integrity():
    print("\n--- Testing Phase 12: Database Integrity ---")
    conn = flask_app.conn()
    df_rep = db.reports_df(conn)
    df_act = db.df(conn, "actions")
    df_alr = db.df(conn, "alerts")
    print(f"Database reports: {len(df_rep)}, actions: {len(df_act)}, alerts: {len(df_alr)}")
    assert len(df_rep) > 0
    assert "risk_score" in df_rep.columns
    assert "report_type" in df_rep.columns
    print("Database queries and schemas: OK")

def test_phase13_validation_edge_cases():
    print("\n--- Testing Phase 13: Validation Edge Cases ---")
    r_short = client.post("/", data={"text": "small fire", "site": "Duliajan", "severity": "Low"})
    assert r_short.status_code == 200
    assert "too short" in r_short.data.decode("utf-8").lower()
    print("1. Short text rejected: OK")

    long_text = "Gas leak detected near compressor station valve. " * 70
    r_long = client.post("/", data={"text": long_text, "site": "Duliajan", "severity": "High"})
    assert r_long.status_code == 200
    assert "Risk" in r_long.data.decode("utf-8")
    print("2. Long text handled safely: OK")

    r_spec = client.post("/", data={"text": "⚠️ H2S gas alarm triggered in sector #4 — worker escaped safely! \u26a0\ufe0f", "site": "Duliajan", "severity": "High"})
    assert r_spec.status_code == 200
    assert "Risk" in r_spec.data.decode("utf-8")
    print("3. Unicode and special chars: OK")

def test_phase10_action_and_review_workflow():
    print("\n--- Testing Action Transition & Human Review Workflow ---")
    conn = flask_app.conn()
    open_act = conn.execute("SELECT id FROM actions WHERE status='Open' LIMIT 1").fetchone()
    if open_act:
        aid = open_act[0]
        r_act = client.post("/actions", data={"id": aid, "to": "In Progress", "person": "Inspector John"}, follow_redirects=True)
        assert r_act.status_code == 200
        cur_status = conn.execute("SELECT status FROM actions WHERE id=?", (aid,)).fetchone()[0]
        assert cur_status == "In Progress"
        print(f"Action #{aid} transitioned to 'In Progress': OK")

    pending_rep = conn.execute("SELECT id FROM reports WHERE review_status='Pending' AND risk_level IN ('HIGH', 'CRITICAL') LIMIT 1").fetchone()
    if pending_rep:
        rid = pending_rep[0]
        r_rev = client.post("/review", data={"id": rid, "decision": "Confirmed", "reviewer": "HSE Auditor", "comment": "Verified on site"}, follow_redirects=True)
        assert r_rev.status_code == 200
        rev_status = conn.execute("SELECT review_status, reviewer FROM reports WHERE id=?", (rid,)).fetchone()
        assert rev_status[0] == "Confirmed" and rev_status[1] == "HSE Auditor"
        print(f"Report #{rid} review confirmed: OK")

def test_api_dashboard_json_validity():
    print("\n--- Testing API Dashboard Strict JSON Validity ---")
    res = client.get("/api/dashboard")
    assert res.status_code == 200
    raw = res.data.decode("utf-8")
    assert "NaN" not in raw
    parsed = json.loads(raw)
    assert parsed["kpi"]["total"] > 0
    print("API /api/dashboard returns strictly valid JSON without NaN: OK")

if __name__ == "__main__":
    test_phase6_main_page()
    test_phase7_safety_report_analysis()
    test_phase8_repeat_duplicate_detection()
    test_phase9_early_warning_and_trends()
    test_phase10_actions_and_routing()
    test_phase11_csv_upload()
    test_phase12_database_integrity()
    test_phase13_validation_edge_cases()
    test_phase10_action_and_review_workflow()
    test_api_dashboard_json_validity()
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
