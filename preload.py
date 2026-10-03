"""Preload script for Render build / setup.
Ensures data/models.pkl is trained/saved and safetysignal.db is seeded before server starts.
"""
import os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from model import SafetyModels
from pipeline import Engine, seed
import database as db

def preload():
    model_path = os.path.join(BASE_DIR, "data", "models.pkl")
    train_csv = os.path.join(BASE_DIR, "data", "reports.csv")
    db_path = os.environ.get("SAFETYSIGNAL_DB", os.path.join(BASE_DIR, "safetysignal.db"))

    print("[Preload] Ensuring ML model is ready...", flush=True)
    SafetyModels.get_or_train(train_csv=train_csv, model_path=model_path)
    print(f"[Preload] ML model ready at {model_path}.", flush=True)

    print("[Preload] Ensuring database is ready...", flush=True)
    conn = db.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        if count == 0 and os.path.exists(train_csv):
            print(f"[Preload] Seeding demo database from {train_csv}...", flush=True)
            eng = Engine(train_csv=train_csv, model_path=model_path)
            seed(conn, eng, csv=train_csv)
            count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
            print(f"[Preload] Seeded {count} reports.", flush=True)
        else:
            print(f"[Preload] Database ready with {count} reports.", flush=True)
    finally:
        conn.close()
    print("[Preload] All models and demo data are fully initialized.", flush=True)

if __name__ == "__main__":
    preload()
