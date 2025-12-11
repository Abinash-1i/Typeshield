# TypeShield Authenticator

Behavioural password authentication with FastAPI, SQLModel, PostgreSQL, and keystroke dynamics.

## Features
- Password + keystroke dynamics (dwell, flight, total time, error count, speed) with device-aware weighting (touch vs keyboard).
- Behavioural similarity scoring (pure math, no AI) with a default threshold of 75% and hard guards for key-count/tempo drift.
- FastAPI backend, Jinja2 + Bootstrap UI, JavaScript keystroke capture (mobile-friendly fallback), SQLModel ORM, PostgreSQL storage.
- Dashboard with recent attempt history and charts (success/failure counts and scored attempts).

## Project Layout
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

## Setup
1. Install Python dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   (Includes Starlette session dependency `itsdangerous`.)
2. Configure environment (optional overrides):
   - `DATABASE_URL` (default `postgresql+psycopg2://postgres:postgres@localhost:5432/keyrythm`)
   - `SECRET_KEY` for session/JWT signing
   - `BEHAVIOUR_THRESHOLD` (default `75.0`)
3. Ensure PostgreSQL is running and the database exists. Example:
   ```bash
   createdb keyrythm
   ```

## Running
```bash
uvicorn app.main:app --reload
```
- Register at `/register` (keystroke data captured while typing the password).
- Log in at `/login`; access is granted only if password is correct **and** behavioural similarity meets/exceeds the threshold. The latest similarity score is shown on the dashboard.
- Dashboard shows recent attempts and success/failure breakdown from the database.

## Behaviour Scoring
Similarity blends multiple components (weights differ for touch vs keyboard):
- Dwell time
- Flight time
- Total duration
- Typing speed (keys/sec)
- Length alignment (key count)
- Error count

Guards:
- Reject if keystroke count differs by more than one.
- Reject if typing tempo or total duration drifts outside ~0.6x–1.6x of enrolled pattern.
Scores are clamped to 0–100%. A score ≥ threshold (default 75%) is required to authenticate.

## Frontend Behaviour Capture
- `app/static/behaviour.js` records timing on the password field; adds `device_type` to inform scoring weights.
- Dwell time: keyup - keydown per key (with mobile-friendly input fallback).
- Flight time: gap between previous keyup and next keydown.
- Total typing time: first keydown/input → last keyup/input.
- Error count: number of Backspace presses.
- Data is sent as JSON in a hidden form field `behaviour_data`.

## Notes
- Password hashes use PBKDF2-SHA256 via `passlib` to avoid bcrypt length/back-end issues.
- Behaviour templates are stored as JSON vectors via SQLModel/JSON columns; AuthAttempt stores per-login outcomes.
- Sessions use FastAPI/Starlette `SessionMiddleware`; JWT creation is provided for future API use.
