"""Minimal runner (works without pytest): python run_tests.py. `pytest tests` also works if installed."""
import sys, glob, importlib.util, os
sys.path.insert(0, "."); bad = 0
for f in sorted(glob.glob("tests/test_*.py")):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3], f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    for n in [x for x in dir(m) if x.startswith("test_")]:
        try: getattr(m, n)(); print("PASS", n)
        except Exception as e: bad += 1; print("FAIL", n, repr(e)[:200])
sys.exit(1 if bad else 0)
