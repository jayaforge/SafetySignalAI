"""Generates SYNTHETIC demo data (data/reports.csv) and a hand-written frozen challenge set. Run: python data_gen.py"""
import random, csv, datetime as dt
random.seed(7)
UA, UC, NM, NS = "Unsafe Act", "Unsafe Condition", "Near Miss", "Non-Safety"
# (family, type, sif, [paraphrases])
FAM = [
 ("confined_entry", UA, 1, ["Worker entered the tank without gas testing and no standby person at the manhole.", "Contractor went inside the vessel for cleaning, gas test not done, permit not displayed.", "Tank ke andar bina gas check kiye operator ghus gaya, attendant bhi nahi tha."]),
 ("loto_missing", UA, 1, ["Fitter started repairing the pump motor without lockout, breaker was still energized.", "Maintenance team worked on a live panel, isolation not verified and no tags applied.", "Isolation nahi kiya gaya aur electrician ne cable change kar diya."]),
 ("height_noharness", UA, 1, ["Rigger working on scaffold platform at height without harness.", "Contractor climbed the derrick ladder with no fall protection attached.", "Man was at height on the pipe rack, harness not hooked to any anchor point."]),
 ("suspended_load", NM, 1, ["Suspended load swung unexpectedly during crane lift and narrowly missed a worker.", "Sling slipped while lifting, the load dropped near the crew, nobody hurt.", "Crane load swung close to a helper standing under it, near miss."]),
 ("gas_detector_off", UC, 1, ["Gas detector was unavailable near the process area during maintenance.", "H2S monitor on the wellhead was not working, alarm bypassed.", "Portable gas detector battery dead at the separator, crew continued work."]),
 ("hotwork_nopermit", UA, 1, ["Welding was carried out near the flange without hot work permit.", "Grinding sparks near the hydrocarbon area, no fire watch posted.", "Hot work started before gas check, fire watch missing."]),
 ("gas_leak", NM, 1, ["Flange leak noticed on gas line, strong smell, area cleared in time.", "Hydrocarbon leak from valve gland near compressor, no ignition, isolated quickly.", "Gas leakage at wellhead valve found by operator during round, controlled."]),
 ("excavation", UC, 1, ["Trench excavation deeper than 1.5 m with no shoring and no ladder for exit.", "Excavation edge unbarricaded near pipeline route, soil loose.", "Trench was dug without checking underground cable drawings."]),
 ("interlock_bypass", UA, 1, ["Operator bypassed the high pressure trip interlock to keep the separator running.", "Safety alarm was jumpered out by technician during startup.", "Pressure relief valve found isolated on the vessel, nobody was aware."]),
 ("electrical_exposed", UC, 1, ["Exposed wiring at the distribution board in the pump room, door open.", "Damaged cable insulation on welding machine, no earthing.", "Junction box cover missing with live terminals visible."]),
 ("fire_nm", NM, 1, ["Small fire at the generator exhaust, put out with extinguisher before it spread.", "Spark from cutting set fire to oily rags, extinguished in time.", "Flash fire near the sample point, operator escaped without injury."]),
 ("dropped_obj_nm", NM, 1, ["A spanner dropped from the monkey board and landed beside a floorman.", "Tool fell from scaffold level, hit the ground near the crew, no injury.", "Pipe clamp fell from the pipe rack close to a passing worker."]),
 ("vehicle", UA, 0, ["Driver was not wearing seatbelt while moving the vehicle inside the site.", "Pickup was overspeeding near the rig gate.", "Forklift reversing without spotter near the store."]),
 ("ppe_missing", UA, 0, ["Worker in the yard was without helmet and safety shoes.", "Contractor not wearing gloves while handling pipes.", "Operator forgot safety glasses during sampling."]),
 ("housekeeping", UC, 0, ["Oil spill on walkway near the pump house, slip hazard.", "Loose hoses lying across the access path at the drill site.", "Cables across the floor in the control room created a trip hazard."]),
 ("guard_missing", UC, 0, ["Coupling guard missing on the pump, rotating shaft exposed.", "Belt guard removed from the compressor fan and not refitted.", "Fan guard broken on the cooling motor."]),
 ("chemical_store", UC, 0, ["Chemical drums stored without secondary containment near the drain.", "Corrosion inhibitor leaking from a barrel, no spill kit available.", "Chemical containers unlabeled in the store."]),
 ("ptw_lapse", UA, 0, ["Work continued under an expired permit at the tank farm.", "Job started without permit, supervisor not aware.", "Permit copy not available at the worksite."]),
 ("slip_nm", NM, 0, ["Operator slipped on wet stairs but held the handrail, no injury.", "Technician tripped over a pipe support, was not hurt.", "Helper lost footing on muddy ramp, caught himself."]),
 ("lighting", UC, 0, ["Poor lighting at the walkway near the generator room.", "Emergency exit sign not illuminated in the workshop.", "Several lamps out along the pipeline access road."]),
 ("ns_admin", NS, 0, ["The canteen food was good today.", "I want to apply for casual leave next week.", "Please approve my travel allowance bill."]),
 ("ns_misc", NS, 0, ["Please share the training timetable for the new batch.", "How to reset my password for the HR portal?", "Guest house wifi is very slow."]),
 ("ns_misc2", NS, 0, ["Township shuttle bus timing needs to change.", "Request new chairs for the admin office.", "Delivery of the stationery order was delayed again."]),
]
SITES = ["Duliajan", "Digboi", "Naharkatiya", "Moran", "Jaisalmer", "Baghjan"]
LOCS = ["GGS-2", "OCS Main Yard", "Rig-14", "Workshop Bay 3", "CPF Area B", "Store Yard", "Well Pad 12", "Compressor Station"]
ACTS = ["maintenance", "drilling", "workover", "inspection", "construction", "operations round", "shutdown job"]
ROLES = ["Operator", "Supervisor", "Contractor", "Engineer", "Safety Officer", "Fitter"]
def typo(t):
    w = t.split(); c = [i for i, x in enumerate(w) if len(x) > 4]
    if c:
        i = random.choice(c); x = w[i]; j = random.randrange(1, len(x) - 2); w[i] = x[:j] + x[j+1] + x[j] + x[j+2:]
    return " ".join(w)
def noisy(t, loc):
    if random.random() < .45: t = f"At {loc}: {t}"
    if random.random() < .25: t = t.lower()
    if random.random() < .15: t = typo(t)
    if random.random() < .20: t = t.rstrip(".") + random.choice([", reported during routine round.", ", immediate supervisor informed.", ", please review."])
    return t
def make():
    rows, start, end = [], dt.datetime(2026, 3, 1), dt.datetime(2026, 9, 30, 18)
    i = 0
    for fam, typ, sif, paras in FAM:
        for pi, p in enumerate(paras):
            for _ in range(9 if fam == 'confined_entry' else 4 if sif else 15):
                site, loc = random.choice(SITES), random.choice(LOCS)
                when = start + dt.timedelta(seconds=random.randrange(int((end - start).total_seconds())))
                if fam == "confined_entry" and random.random() < .55:   # injected DEMO surge: mostly in the latest 7 days, a few in the 7 before
                    cur = random.random() < .8
                    site, when = "Duliajan", end - dt.timedelta(hours=random.randrange(0, 24 * 7) if cur else random.randrange(24 * 7, 24 * 14))
                if typ == NS: sev = ""
                elif sif: sev = random.choices(["Low", "Medium", "High"], [.25, .35, .4])[0]
                else: sev = random.choices(["Low", "Medium", "High"], [.65, .3, .05])[0]
                i += 1
                rows.append(dict(id=i, reported_at=when.strftime("%Y-%m-%d %H:%M"), text=noisy(p, loc), site=site, location=loc,
                  activity=random.choice(ACTS), reporter_role=random.choice(ROLES), severity=sev, report_type=typ,
                  sif_potential=sif, relevant=int(typ != NS), status=random.choice(["Open", "Closed"]),
                  scenario_family=fam, paraphrase_group=f"{fam}_{pi}"))
    random.shuffle(rows); return rows
CH = [  # (text, type, sif) hand-written, NOT used for training
 ("Pipe slipped from the crane sling and crashed down a metre from the rigger, he jumped back", NM, 1),
 ("gas smell near seperator, crew evacuated, found flange leking", NM, 1),
 ("Operator nearly fell off the tank roof when the handrail gave way, caught the pipe", NM, 1),
 ("Spark flew from grinder towards oily waste, put out immediately", NM, 1),
 ("Truck reversed fast and almost hit the banksman", NM, 1),
 ("Hose whipped when coupling failed, missed the roustabout by inches", NM, 1),
 ("Trench wall collapsed partially, labourer had just climbed out", NM, 1),
 ("Helper entered the sump to retrieve tools, atmosphere not tested", UA, 1),
 ("Electrician opened the live MCC panel for checking, no isolation done", UA, 1),
 ("Fitter on pipe rack at 6m not tied off", UA, 1),
 ("Contractor started cutting job near wellhead w/o PTW", UA, 1),
 ("Supervisor allowed work inside vessel with expired permit and no standby", UA, 1),
 ("Operator bypassed low level trip on the separator for 2 hours", UA, 1),
 ("bina harness ke scaffold pe kaam kar rahe the", UA, 1),
 ("Workers stood under the lifted skid while it was being moved", UA, 1),
 ("H2S alarm not functioning at the sour gas manifold", UC, 1),
 ("Exposed live terminals in the junction box, cover missing, area wet", UC, 1),
 ("Unbarricaded open excavation next to the access road", UC, 1),
 ("Fire extinguishers empty at the gas compressor shed", UC, 1),
 ("Scaffold lacks toe boards and handrail on third level", UC, 1),
 ("Visitor entered process area without safety glasses", UA, 0),
 ("Driver was talking on phone while driving in the field", UA, 0),
 ("Operator did not wear gloves during sampling", UA, 0),
 ("Contractor smoking behind the store", UA, 0),
 ("Waste left at the site after the job, no housekeeping", UC, 0),
 ("Wet floor with no sign in the workshop corridor", UC, 0),
 ("Fan guard cracked on the cooling tower motor", UC, 0),
 ("Torn hose pipe lying on the walkway", UC, 0),
 ("Helper slipped on an oil patch but didnt fall", NM, 0),
 ("Door swung and hit the operator's shoulder, minor", NM, 0),
 ("Small tool fell from the table, no one was near", NM, 0),
 ("Please approve my travel allowance bill", NS, 0), ("Cafeteria chai was cold today", NS, 0),
 ("Wifi is slow in the guest house", NS, 0), ("Need the training schedule for next month's batch", NS, 0),
 ("Which form is needed for LTC claim?", NS, 0), ("Happy Diwali to the entire team", NS, 0),
 ("The new safety poster in the lobby looks great", NS, 0), ("Delivery truck arrived late with spare parts", NS, 0),
 ("Live cricket match was shown in the recreation hall", NS, 0),
]
if __name__ == "__main__":
    rows = make()
    with open("data/reports.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open("data/challenge_set.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "text", "report_type", "sif_potential", "relevant"])
        for k, (t, ty, s) in enumerate(CH, 1): w.writerow([k, t, ty, s, int(ty != NS)])
    print(len(rows), "training rows;", len(CH), "challenge rows")
