"""Configurable PROTOTYPE values. Not official OIL values; require HSE validation."""
RISK_WEIGHTS = {"sif_max": 40, "severity": {"Low": 0, "Medium": 5, "High": 10},
                "type": {"Near Miss": 10, "Unsafe Act": 5, "Unsafe Condition": 5},
                "life_saving_rule": 10, "barrier_failure": 5, "repeat_max": 15, "emerging": 10}
RISK_LEVELS = [(75, "CRITICAL"), (55, "HIGH"), (30, "MEDIUM"), (0, "LOW")]
SLA_HOURS = {"CRITICAL": 24, "HIGH": 72, "MEDIUM": 168, "LOW": 336}
ESCALATION = ["Site HSE", "Area Manager", "GM-HSE"]
REPEAT_WINDOW_DAYS = 30
EARLY_WARNING = {"window_days": 7, "min_current": 3, "growth_factor": 2.0}
MIN_TEXT_CHARS = 15
DISCLAIMER = "Demo system using synthetic data. Metrics demonstrate the methodology, not field accuracy at OIL."
RISK_NOTE = "Risk weights and thresholds are configurable prototype values and require HSE validation."
SIMILARITY = {"duplicate": 0.80, "similar": 0.35}   # prototype thresholds on TF-IDF cosine similarity
EW_CRITICAL = {"min_current": 6, "growth_factor": 3.0, "min_current_if_new": 5}   # prototype
ESCALATION_NOTE = "Prototype escalation workflow — configurable by organization."
ACTION_NOTE = "Prototype action recommendation — requires HSE validation."
EW_NOTE = "Statistical Early Warning: this is statistical trend detection, not guaranteed prediction."
