"""Grouped cross-validation + frozen challenge-set evaluation. Writes data/eval_results.json. Nothing here is hard-coded."""
import json, numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, confusion_matrix, average_precision_score, recall_score
from model import make_pipe, SafetyModels
from config import DISCLAIMER
def oof(df, y, groups, k=5):
    pred = np.empty(len(df), dtype=(np.int64 if pd.api.types.is_integer_dtype(y) else object)); proba = None
    for tr, te in GroupKFold(n_splits=k).split(df, y, groups):
        m = make_pipe().fit(df.text.iloc[tr], y.iloc[tr]); pred[te] = m.predict(df.text.iloc[te])
        if proba is None: proba = np.zeros((len(df), len(m.classes_)))
        proba[te] = m.predict_proba(df.text.iloc[te])
    return pred, proba
def gboot(y, p, g, fn, n=500, seed=0):
    rng = np.random.default_rng(seed); ug = np.unique(g); idx = {u: np.where(g == u)[0] for u in ug}; v = []
    for _ in range(n):
        s = np.concatenate([idx[u] for u in rng.choice(ug, len(ug))]); 
        try: v.append(fn(y[s], p[s]))
        except Exception: pass
    return [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)]
def task_report(y, pred):
    labs = sorted(set(y)); r = classification_report(y, pred, labels=labs, output_dict=True, zero_division=0)
    return {"n": int(len(y)), "per_class": {str(l): {k: round(r[str(l)][k], 3) for k in ("precision", "recall", "f1-score")} | {"support": int(r[str(l)]["support"])} for l in labs},
            "macro_f1": round(r["macro avg"]["f1-score"], 3), "labels": [str(l) for l in labs], "confusion_matrix": confusion_matrix(y, pred, labels=labs).tolist()}
def run():
    df = pd.read_csv("data/reports.csv").fillna({"severity": ""}); ch = pd.read_csv("data/challenge_set.csv")
    assert not set(ch.text) & set(df.text), "LEAKAGE: challenge text appears in training data"
    res = {"disclaimer": DISCLAIMER, "dataset": {"rows": len(df), "scenario_families": int(df.scenario_family.nunique()), "paraphrase_groups": int(df.paraphrase_group.nunique()),
           "safety_rows": int(df.relevant.sum()), "sif_rows": int(df.sif_potential.sum())}, "methodology": {}}
    sub = df[df.relevant == 1].reset_index(drop=True)
    for gname, col in (("paraphrase_group", "paraphrase_group"), ("scenario_family", "scenario_family")):
        out = {}
        pr, pp = oof(df, df.relevant, df[col]); out["relevance"] = task_report(df.relevant.values, pr)
        pt, _ = oof(sub, sub.report_type, sub[col]); out["report_type"] = task_report(sub.report_type.values, pt)
        ps, pps = oof(sub, sub.sif_potential, sub[col]); t = task_report(sub.sif_potential.values, ps)
        yb, g = sub.sif_potential.values, sub[col].values; pos = pps[:, 1]
        t["sif_recall"] = round(float(recall_score(yb, ps.astype(int))), 3)
        t["sif_recall_95ci_group_bootstrap"] = gboot(yb, ps.astype(int), g, recall_score)
        t["pr_auc"] = round(float(average_precision_score(yb, pos)), 3); t["pr_auc_baseline_prevalence"] = round(float(yb.mean()), 3)
        out["sif"] = t; res["methodology"][f"GroupKFold(5) by {gname}"] = out
    m = SafetyModels().fit(df); c = {}
    P = [m.predict(t) for t in ch.text]
    c["relevance"] = task_report(ch.relevant.values, np.array([p["relevant"]["label"] for p in P]))
    sc = ch.relevant.values == 1
    pt = np.array([p["report_type"]["label"] if "report_type" in p else "Non-Safety" for p in P])
    c["report_type (gold-relevant rows only)"] = task_report(ch.report_type.values[sc], pt[sc])
    ps = np.array([int(p["sif"]["label"]) if "sif" in p else 0 for p in P]); c["sif (gold-relevant rows only)"] = task_report(ch.sif_potential.values[sc], ps[sc])
    c["sif (gold-relevant rows only)"]["sif_recall"] = round(float(recall_score(ch.sif_potential.values[sc], ps[sc])), 3)
    res["challenge_set"] = c | {"note": "Frozen, hand-written, never used for training. Small n: wide uncertainty. Single labeller so far; Cohen's kappa needs a 2nd independent labeller."}
    json.dump(res, open("data/eval_results.json", "w"), indent=1); return res
if __name__ == "__main__":
    r = run(); print(r["dataset"])
    for g, o in r["methodology"].items():
        print("\n", g)
        for k, v in o.items(): print(f"  {k:12s} n={v['n']} macroF1={v['macro_f1']}", {x: v[x] for x in v if x in ("sif_recall", "sif_recall_95ci_group_bootstrap", "pr_auc", "pr_auc_baseline_prevalence")})
    print("\nCHALLENGE")
    for k, v in r["challenge_set"].items():
        if isinstance(v, dict): print(f"  {k}: n={v['n']} macroF1={v['macro_f1']}", v.get("sif_recall", ""))
