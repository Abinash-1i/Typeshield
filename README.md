# TypeShield Authenticator

Behavioural password authentication with FastAPI, SQLModel, PostgreSQL, and keystroke dynamics.

## What it does
- Password plus keystroke dynamics (dwell, flight, total time, speed, errors, length) with device-aware weighting for touch vs keyboard.
- Pure-math similarity scoring (no ML) with hard guards for key-count drift and tempo drift; default threshold 75%.
- FastAPI + Jinja2 UI with session cookies, PBKDF2-SHA256 hashing, and optional JWT issuance.
- Dashboard with recent attempts, success/failure breakdown, and Chart.js visualizations.
- Auto-creates tables on startup via SQLModel; no migrations needed for first run.

## Prerequisites
- Python 3.11+
- PostgreSQL 14+ running locally (or any Postgres-compatible URL)
- `pip` / `virtualenv`; optional `createdb` CLI for quick DB creation

## Quickstart
1) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Create a database (default name `keyrythm`)
```bash
createdb keyrythm
```
3) Configure environment (optional overrides) — `.env` example:
```bash
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/keyrythm
SECRET_KEY=super-secret-key-change-me
BEHAVIOUR_THRESHOLD=75.0
```
4) Run the app (dev hot-reload)
```bash
uvicorn app.main:app --reload
```

Production-style launch is also available via `Procfile`:
```bash
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Usage
- Visit `/register`, type your password; keystroke vectors are captured client-side and stored as your template.
- Visit `/login` to authenticate; access is granted only if the password matches **and** your behaviour score meets the threshold (rejection reasons are shown when available).
- `/dashboard` shows your latest score, attempt history (last 10), and charts for success/failure, scores, and hourly activity.
- `/logout` clears the session.

## Behaviour scoring (server-side)
- Components: dwell, flight, total duration, typing speed, length alignment, error count.
- Device-aware weights: coarser thresholds on touch devices (uses `device_type` from the frontend).
- Guards: reject if key-count differs by more than one, or if typing tempo/total duration is outside ~0.6x–1.6x of the enrolled pattern.
- Scores are clamped to 0–100%; match requires score ≥ `BEHAVIOUR_THRESHOLD`.

## Frontend capture
- `app/static/behaviour.js` records timing on the password field; falls back to input-based capture on touch keyboards.
- Sends JSON in hidden form field `behaviour_data` with dwell/flight vectors, total time, error count, and `device_type`.
- Stats and progress bars update live while typing; alerts if you try to submit without captured data.

## Project layout
```
keyrythm_webauth/
├── app/
│   ├── main.py            # FastAPI entry point and routes
│   ├── config.py          # Environment configuration and thresholds
│   ├── database.py        # SQLModel engine and session helpers
│   ├── models.py          # User, BehaviourTemplate, AuthAttempt models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── auth.py            # Password hashing and JWT helpers
│   ├── behaviour.py       # Similarity scoring logic
│   ├── utils.py           # Helper utilities
│   ├── templates/         # Jinja2 templates (register, login, dashboard)
│   └── static/            # Frontend JS (behaviour capture)
└── requirements.txt
```

## Notes & tips
- Use a `postgresql+psycopg2://...` URL; if your host gives `postgres://`, update it to include the `psycopg2` driver.
- Tables are created automatically on startup; rerun with a clean DB to reset.
- Keep `SECRET_KEY` unique per environment to protect sessions; JWT signing uses the same key.
