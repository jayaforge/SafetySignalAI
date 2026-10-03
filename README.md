# # SafetySignal AI — AI-Powered Industrial Safety Intelligence Platform
Demo system using synthetic data. Metrics demonstrate the methodology, not field accuracy at OIL.

## Run (Windows, PowerShell)
    python -m venv venv ; venv\Scripts\activate
    pip install -r requirements.txt
    python data_gen.py        # synthetic data + frozen challenge set
    python evaluation.py      # grouped CV + challenge metrics -> data/eval_results.json
    python run_tests.py       # or: pytest tests
    python app.py             # http://127.0.0.1:5000  (first start seeds safetysignal.db)
Dashboard charts load Chart.js from a CDN, so the browser needs internet once. Delete safetysignal.db to reseed.

## What is what
- Machine learning: TF-IDF + Logistic Regression (relevance, UA/UC/NM, SIF). Output is a *model confidence estimate*, uncalibrated.
- Rule engine: Life-Saving Rules, barrier failures, keyword relevance gate, risk score, action library, escalation.
- Statistical trend detection: windowed count comparison (early warning); not prediction.
- Similarity matching: TF-IDF cosine for duplicate / similar reports.
- Human review: confirm/override with stored original prediction; never used to retrain automatically.
All weights, thresholds, SLAs and actions are configurable prototype values (config.py, actions.py) requiring HSE validation.

## Known limitations
- All data is synthetic. Seeded demo predictions are in-sample (model trained on the same file).
- Dashboard "now" is the latest report timestamp (demo clock). Seeded action progress is simulated.
- Challenge set: 40 examples, one labeller; Cohen's kappa not computed. Do not tune on it.
- ML relevance model is weak on unseen non-safety text; uncertain cases are held for confirmation.
- Local prototype: no authentication; not production security.
