# TypeShield Authenticator – Engineering Project Abstract

## Problem
Traditional password-based authentication is vulnerable to credential theft and replay. Adding behavioural biometrics (keystroke dynamics) can harden auth, but integrating capture, scoring, and UX with a web stack needs a cohesive implementation.

## Objective
Deliver a web application that combines password verification with keystroke-dynamics-based behavioural matching to reduce impersonation risk while keeping the user experience familiar.

## System Overview
- **Frontend**: FastAPI-served Bootstrap UI with session-backed forms for register/login. Client-side script (`app/static/behaviour.js`) records dwell/flight times while the user types and submits them with the password.
- **Backend**: FastAPI endpoints backed by SQLModel + Postgres. Passwords hashed with PBKDF2-SHA256; keystroke templates stored as JSON blobs linked to users. Session cookies track authenticated users.
- **Behaviour Engine**: Captured vectors compared against stored templates using normalized percentage differences. Scoring blends dwell, flight, total time, and error count; threshold configurable via `BEHAVIOUR_THRESHOLD`.
- **Config**: Environment-driven settings (`app/config.py`) with `pydantic-settings`; secret key/DB URL/threshold are overridable via `.env`.

## Key Features
- Dual-factor style: password plus keystroke behavioural signature.
- Registration captures a template; login compares attempts and blocks mismatches.
- Session-based web flows with inline error handling and refreshed UI.
- Bootstrap styling for professional UX; celebratory feedback on successful auth.

## Data Flow
1. User types password on register → frontend captures keystroke timings → POST `/register` with password + JSON timings.
2. Backend hashes password, stores `BehaviourTemplate` (dwell/flight/total_time/error_count) tied to `User`.
3. Login repeats capture → POST `/login` → backend verifies password, loads template, computes similarity score, enforces threshold → issues session + JWT on success.

## Scoring Logic
- Dwell/flight vectors: average percentage difference with length mismatch penalties.
- Total duration: relative deviation from template.
- Error count: deviation impact.
- Weighted blend: dwell 35%, flight 35%, total 20%, errors 10%. Match if score ≥ `behaviour_threshold`.

## Security Considerations
- Hashing: PBKDF2-SHA256 to avoid bcrypt length limits and backend issues.
- Sessions: Starlette `SessionMiddleware` with secret key; JWT issued for API-style token needs.
- Input validation: Pydantic schemas ensure timing vectors are non-negative; errors handled without leaking sensitive detail.
- Environment management: secrets and DB URLs read from `.env`.

## Setup & Run
1. Install deps: `pip install -r requirements.txt`.
2. Set env vars as needed (`SECRET_KEY`, `DATABASE_URL`, `BEHAVIOUR_THRESHOLD`).
3. Start app: `uvicorn app.main:app --reload`.
4. Register to create a template; login to test behavioural matching.

## Future Enhancements
- Multi-sample enrollment to build stronger templates and variance models.
- Adaptive thresholds per user and anomaly alerting.
- Optional WebAuthn or OTP fallback for step-up auth.
- Analytics dashboard for match rates and drift monitoring.
