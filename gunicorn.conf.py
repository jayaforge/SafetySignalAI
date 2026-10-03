import os

# Render dynamically assigns PORT; default to 5000 locally
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Concurrency & timeout tailored for Render Free Tier (0.1 CPU / 512 MB RAM)
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("PYTHON_MAX_THREADS", "2"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = 5

# Preload application so model and database readiness happen before workers serve traffic
preload_app = True

# Stream logs directly to stdout/stderr for Render logs
accesslog = "-"
errorlog = "-"
loglevel = "info"
