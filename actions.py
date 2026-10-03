"""Prototype action library, workflow (Open>In Progress>Resolved>Verified) and escalation. Requires HSE validation."""
import datetime as dt
from config import SLA_HOURS, ESCALATION
ORDER = ["Open", "In Progress", "Resolved", "Verified"]
LIB = {  # rule -> (department, owner role, [actions])
 "Confined Space": ("Site HSE", "Area Safety Officer", ["Stop non-essential entry", "Verify permit-to-work", "Verify gas testing", "Verify standby person", "Review rescue readiness", "Conduct toolbox talk"]),
 "Energy Isolation / LOTO": ("Maintenance", "Maintenance Supervisor", ["Verify isolation", "Review LOTO procedure", "Inspect lock/tag compliance", "Supervisor verification"]),
 "Working at Height": ("Site HSE", "Area Safety Officer", ["Verify fall protection", "Inspect scaffolding", "Check anchor points", "Supervisor inspection"]),
 "Lifting": ("Operations", "Lifting Supervisor", ["Verify lifting plan and rigging inspection", "Establish exclusion zone"]),
 "Line of Fire": ("Operations", "Shift Supervisor", ["Re-brief crew on line-of-fire hazards", "Mark exclusion zones"]),
 "Hot Work": ("Fire & Safety", "Fire Officer", ["Verify hot work permit and gas test", "Verify fire watch"]),
 "H2S / Toxic Gas": ("Site HSE", "Area Safety Officer", ["Verify gas detector availability and calibration", "Check breathing apparatus readiness"]),
 "Gas Leak": ("Operations", "Shift Incharge", ["Isolate and inspect leak source", "Verify ignition-source control"]),
 "Electrical Safety": ("Electrical", "Electrical Supervisor", ["Inspect and make safe exposed wiring", "Verify earthing"]),
 "Excavation": ("Civil", "Site Engineer", ["Verify shoring and edge barricading", "Check underground services drawings"]),
 "Permit to Work": ("Site HSE", "Area Safety Officer", ["Audit permit validity at worksite"]),
 "Driving / Vehicle Safety": ("Transport", "Transport Officer", ["Reinforce driving rules and spotter use"]),
 "PPE": ("Site HSE", "Area Safety Officer", ["Reinforce PPE compliance at job site"]),
 "Dropped Objects": ("Operations", "Shift Supervisor", ["Inspect tool tethering and overhead work areas"]),
}
def recommend(rules, level, now=None):
    if level not in ("HIGH", "CRITICAL"): return []
    now = now or dt.datetime.now(); due = (now + dt.timedelta(hours=SLA_HOURS[level])).isoformat(timespec="minutes"); out = []
    for r in rules or []:
        if r in LIB:
            dep, own, acts = LIB[r]; out += [{"action": f"[{r}] {a}", "priority": level, "department": dep, "owner": own, "due_date": due} for a in acts]
    return out or [{"action": "Supervisor review of report", "priority": level, "department": "Site HSE", "owner": "Area Safety Officer", "due_date": due}]
def advance(conn, action_id, new_status, person, resolution=None):
    a = conn.execute("SELECT status,resolver FROM actions WHERE id=?", (action_id,)).fetchone()
    if a is None: raise ValueError("Action not found.")
    if new_status not in ORDER or ORDER.index(new_status) != ORDER.index(a["status"]) + 1: raise ValueError(f"Invalid transition: {a['status']} -> {new_status}.")
    if not person or not person.strip(): raise ValueError("A person's name is required.")
    now = dt.datetime.now().isoformat(timespec="minutes")
    if new_status == "Resolved":
        if not resolution or not resolution.strip(): raise ValueError("A resolution description is required.")
        conn.execute("UPDATE actions SET status=?,resolution=?,resolver=?,resolved_at=? WHERE id=?", (new_status, resolution.strip()[:1000], person.strip(), now, action_id))
    elif new_status == "Verified":
        if person.strip().lower() == (a["resolver"] or "").lower(): raise ValueError("Verifier must be different from the resolver.")
        conn.execute("UPDATE actions SET status=?,verifier=?,verified_at=? WHERE id=?", (new_status, person.strip(), now, action_id))
    else: conn.execute("UPDATE actions SET status=? WHERE id=?", (new_status, action_id))
    conn.commit()
def is_overdue(action, now=None):
    now = now or dt.datetime.now(); return action["status"] in ("Open", "In Progress") and dt.datetime.fromisoformat(action["due_date"]) < now
def escalation_stage(action, now=None):
    "Prototype escalation workflow — configurable by organization. One stage per SLA-length of lateness."
    now = now or dt.datetime.now()
    if not is_overdue(action, now): return None
    late_h = (now - dt.datetime.fromisoformat(action["due_date"])).total_seconds() / 3600
    return ESCALATION[min(len(ESCALATION) - 1, int(late_h // SLA_HOURS.get(action["priority"], 24)))]
