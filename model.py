"""ML baseline: TF-IDF (word + char n-grams for typo robustness) + Logistic Regression. Three separate models."""
import os, pickle
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, FeatureUnion
STOP = {"the","a","an","of","to","in","on","at","and","was","were","is","are","for","by","with","it","this","that","as","be","has","had"}  # negations deliberately kept
MODEL_NAME = "TF-IDF (word 1-2gram + char 3-5gram) + Logistic Regression (balanced)"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "data", "models.pkl")
DEFAULT_TRAIN_CSV = os.path.join(BASE_DIR, "data", "reports.csv")

def make_pipe():
    feats = FeatureUnion([("w", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words=list(STOP), strip_accents="unicode")),
                          ("c", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True))])
    return Pipeline([("f", feats), ("lr", LogisticRegression(max_iter=500, C=5, class_weight="balanced"))])
class SafetyModels:
    def fit(self, df):
        self.rel = make_pipe().fit(df.text, df.relevant)
        s = df[df.relevant == 1]
        self.typ = make_pipe().fit(s.text, s.report_type)
        self.sif = make_pipe().fit(s.text, s.sif_potential)
        return self

    def save(self, path=DEFAULT_MODEL_PATH):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f, protocol=4)
        return self

    @classmethod
    def load(cls, path=DEFAULT_MODEL_PATH):
        with open(path, "rb") as f:
            return pickle.load(f)

    @classmethod
    def get_or_train(cls, train_csv=DEFAULT_TRAIN_CSV, model_path=DEFAULT_MODEL_PATH):
        if model_path and os.path.exists(model_path):
            try:
                return cls.load(model_path)
            except Exception:
                pass
        df = pd.read_csv(train_csv) if isinstance(train_csv, str) else train_csv
        m = cls().fit(df)
        if model_path:
            try:
                m.save(model_path)
            except Exception:
                pass
        return m
    @staticmethod
    def _terms(pipe, text, label, k=4):
        f, lr = pipe.named_steps["f"], pipe.named_steps["lr"]
        x = f.transform([text]); names = f.get_feature_names_out()
        cl = list(lr.classes_); row = lr.coef_[0] if len(cl) == 2 else lr.coef_[cl.index(label)]
        if len(cl) == 2 and label == cl[0]: row = -row
        contrib = x.multiply(row).toarray()[0]
        idx = [i for i in np.argsort(-contrib) if contrib[i] > 0 and names[i].startswith("w__")][:k]
        return [names[i][3:] for i in idx]
    def _one(self, pipe, text):
        p = pipe.predict_proba([text])[0]; i = int(p.argmax()); lab = pipe.classes_[i]
        return {"label": lab.item() if hasattr(lab, "item") else lab, "confidence": round(float(p[i]), 3), "terms": self._terms(pipe, text, lab)}
    def predict(self, text, force=False):
        r = self._one(self.rel, text); out = {"model": MODEL_NAME, "confidence_note": "Model confidence estimate (uncalibrated), not a guarantee.", "relevant": r}
        if r["label"] == 1 or force:
            out["report_type"] = self._one(self.typ, text); s = self._one(self.sif, text)
            sp = float(self.sif.predict_proba([text])[0][list(self.sif.classes_).index(1)])
            s["sif_probability"] = round(sp, 3); s["sif_level"] = "High" if sp >= .7 else "Medium" if sp >= .4 else "Low"
            out["sif"] = s
        return out
