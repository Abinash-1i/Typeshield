import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from starlette.middleware.sessions import SessionMiddleware

from . import behaviour
from .auth import create_access_token, hash_password, verify_password
from .config import settings
from .database import get_session, init_db
from sqlalchemy import func

from .models import AuthAttempt, BehaviourTemplate, User
from .schemas import BehaviourData

app = FastAPI(title=settings.app_name)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def log_attempt(
    db,
    username: str | None,
    status: str,
    score: float | None,
    user_id: int | None = None,
) -> None:
    db.add(
        AuthAttempt(
            username=username,
            status=status,
            score=score,
            user_id=user_id,
        )
    )


def get_current_user(request: Request, session=Depends(get_session)) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    statement = select(User).where(User.id == user_id)
    result = session.exec(statement).first()
    return result


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/login")


@app.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    behaviour_data: str = Form(...),
    session=Depends(get_session),
):
    statement = select(User).where(User.username == username)
    if session.exec(statement).first():
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already taken"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        behaviour_parsed = BehaviourData.parse_raw(behaviour_data)
    except Exception as exc:  # pragma: no cover - defensive
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Invalid behaviour payload"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(username=username, hashed_password=hash_password(password))
    session.add(user)
    session.flush()  # assign id

    template = BehaviourTemplate(
        user_id=user.id,
        dwell_times=behaviour_parsed.dwell_times,
        flight_times=behaviour_parsed.flight_times,
        total_time=behaviour_parsed.total_time,
        error_count=behaviour_parsed.error_count,
    )
    session.add(template)
    session.commit()

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["score"] = 100

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None, "error_details": None})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    behaviour_data: str = Form(...),
    session=Depends(get_session),
):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if not user or not verify_password(password, user.hashed_password):
        log_attempt(session, username, "failure", None, user_id=user.id if user else None)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials", "error_details": None},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    template_statement = select(BehaviourTemplate).where(BehaviourTemplate.user_id == user.id)
    stored_template = session.exec(template_statement).first()
    if not stored_template:
        log_attempt(session, username, "failure", None, user_id=user.id)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Behaviour profile missing. Please register again.",
                "error_details": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        behaviour_parsed = BehaviourData.parse_raw(behaviour_data)
    except Exception:
        log_attempt(session, username, "failure", None, user_id=user.id)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid behaviour data", "error_details": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    is_match, score, reasons = behaviour.is_behaviour_match(stored_template, behaviour_parsed)
    if not is_match:
        log_attempt(session, username, "failure", score, user_id=user.id)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": f"Behavioural pattern mismatch. Similarity score: {score}%",
                "error_details": reasons,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token = create_access_token({"sub": str(user.id), "username": user.username})
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["score"] = score
    log_attempt(session, username, "success", score, user_id=user.id)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/dashboard")
def dashboard(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    session=Depends(get_session),
):
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    success_count_raw = session.exec(
        select(func.count()).select_from(AuthAttempt).where(AuthAttempt.user_id == user.id, AuthAttempt.status == "success")
    ).one()
    failure_count_raw = session.exec(
        select(func.count()).select_from(AuthAttempt).where(AuthAttempt.user_id == user.id, AuthAttempt.status == "failure")
    ).one()
    success_count = success_count_raw[0] if isinstance(success_count_raw, tuple) else success_count_raw or 0
    failure_count = failure_count_raw[0] if isinstance(failure_count_raw, tuple) else failure_count_raw or 0
    recent_attempts = session.exec(
        select(AuthAttempt).where(AuthAttempt.user_id == user.id).order_by(AuthAttempt.created_at.desc()).limit(10)
    ).all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "score": request.session.get("score", "N/A"),
            "attempt_totals": {"success": success_count, "failure": failure_count},
            "attempts_log": [
                {
                    "timestamp": attempt.created_at.isoformat() + "Z",
                    "status": attempt.status,
                    "score": attempt.score,
                }
                for attempt in recent_attempts
            ],
        },
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
