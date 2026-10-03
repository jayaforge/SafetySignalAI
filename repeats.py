"""Similarity matching (TF-IDF cosine) and repeat-hazard counting. Similarity matching, not ML prediction."""
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import SIMILARITY, REPEAT_WINDOW_DAYS
from rules import detect_rules
def with_rules(d):
    d = d.copy(); d["rules"] = d.text.map(lambda t: [r["rule"] for r in detect_rules(t)]); return d
class SimilarityIndex:
    def __init__(self, hist):
        self.h = hist.reset_index(drop=True); self.v = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(self.h.text); self.m = self.v.transform(self.h.text)
    def query(self, text, top=5, floor=0.2):
        s = cosine_similarity(self.v.transform([text]), self.m)[0]; out = []
        for i in s.argsort()[::-1][:top]:
            if s[i] < floor: break
            r = self.h.iloc[i]; kind = "Duplicate / near duplicate" if s[i] >= SIMILARITY["duplicate"] else "Similar / related hazard" if s[i] >= SIMILARITY["similar"] else "Weakly related"
            out.append({"id": int(r["id"]), "similarity_pct": round(float(s[i]) * 100, 1), "kind": kind, "reported_at": str(r["reported_at"]), "site": r["site"], "status": r.get("status", ""), "text": r["text"]})
        return out
def repeat_count(hist, site, rule, when, window_days=REPEAT_WINDOW_DAYS):
    """hist needs columns/keys site, reported_at, rules (list). Counts prior same-site same-rule reports inside the window."""
    if hist is None or len(hist) == 0: return 0
    t = pd.to_datetime(when)
    start = t - pd.Timedelta(days=window_days)
    if isinstance(hist, list):
        cnt = 0
        for r in hist:
            if r.get("site") == site and rule in r.get("rules", ()):
                dt_val = r.get("_dt")
                if dt_val is None:
                    dt_val = pd.to_datetime(r.get("reported_at"))
                if start < dt_val <= t:
                    cnt += 1
        return cnt
    if "_dt" in hist.columns: d = hist["_dt"]
    elif pd.api.types.is_datetime64_any_dtype(hist["reported_at"]): d = hist["reported_at"]
    else: d = pd.to_datetime(hist["reported_at"])
    m = (hist["site"] == site) & (d <= t) & (d > start) & hist["rules"].map(lambda r: rule in r)
    return int(m.sum())
def repeat_summary(hist, site, rule, when, window_days=REPEAT_WINDOW_DAYS):
    n = repeat_count(hist, site, rule, when, window_days)
    return f"{n} similar {rule} reports recorded at {site} within the last {window_days} days." if n else None
