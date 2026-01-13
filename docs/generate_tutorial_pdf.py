from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

PAGE_WIDTH = 595  # A4 points
PAGE_HEIGHT = 842
LEFT_MARGIN = 50
RIGHT_MARGIN = 50
TOP_MARGIN = 50
BOTTOM_MARGIN = 50
FOOTER_SPACE = 25

FONT_NORMAL = "F1"
FONT_BOLD = "F2"
FONT_CODE = "F3"

@dataclass
class Line:
    text: str
    font: str
    size: int
    x: int
    y: int


@dataclass
class Block:
    kind: str
    text: str | List[str]
    level: int = 0
    snippet_id: str | None = None
    snippet_title: str | None = None
    snippet_file: str | None = None


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_text(text: str, max_chars: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        if not current:
            current.append(word)
            continue
        candidate = " ".join(current + [word])
        if len(candidate) <= max_chars:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def max_chars_for_font(font_size: int, is_code: bool = False) -> int:
    # Conservative estimate of average character width.
    width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    factor = 0.6 if is_code else 0.55
    return max(20, int(width / (font_size * factor)))


def layout_blocks(blocks: List[Block]) -> Tuple[List[List[Line]], Dict[str, int]]:
    pages: List[List[Line]] = [[]]
    snippet_pages: Dict[str, int] = {}
    y = PAGE_HEIGHT - TOP_MARGIN
    page_num = 1

    def new_page() -> None:
        nonlocal y, page_num
        pages.append([])
        page_num += 1
        y = PAGE_HEIGHT - TOP_MARGIN

    def add_line(text: str, font: str, size: int, indent: int = 0) -> None:
        nonlocal y
        leading = size + 4
        if y - leading < BOTTOM_MARGIN + FOOTER_SPACE:
            new_page()
        line = Line(text=text, font=font, size=size, x=LEFT_MARGIN + indent, y=y)
        pages[-1].append(line)
        y -= leading

    for block in blocks:
        if block.kind == "h1":
            for line in wrap_text(block.text, max_chars_for_font(20)):
                add_line(line, FONT_BOLD, 20)
            y -= 6
        elif block.kind == "h2":
            for line in wrap_text(block.text, max_chars_for_font(16)):
                add_line(line, FONT_BOLD, 16)
            y -= 4
        elif block.kind == "h3":
            for line in wrap_text(block.text, max_chars_for_font(13)):
                add_line(line, FONT_BOLD, 13)
            y -= 2
        elif block.kind == "p":
            lines = wrap_text(block.text, max_chars_for_font(11))
            for line in lines:
                add_line(line, FONT_NORMAL, 11)
            y -= 4
        elif block.kind == "bullets":
            for item in block.text:  # type: ignore[assignment]
                bullet_lines = wrap_text(item, max_chars_for_font(11) - 4)
                for i, line in enumerate(bullet_lines):
                    prefix = "- " if i == 0 else "  "
                    add_line(prefix + line, FONT_NORMAL, 11, indent=8)
            y -= 4
        elif block.kind == "code":
            if block.snippet_id and block.snippet_id not in snippet_pages:
                snippet_pages[block.snippet_id] = page_num
            title = f"{block.snippet_title} ({block.snippet_file})"
            for line in wrap_text(title, max_chars_for_font(12)):
                add_line(line, FONT_BOLD, 12)
            for line in block.text:  # type: ignore[assignment]
                add_line(line, FONT_CODE, 9, indent=10)
            y -= 6
        else:
            raise ValueError(f"Unknown block type: {block.kind}")

    return pages, snippet_pages


def build_blocks() -> List[Block]:
    blocks: List[Block] = []

    blocks.append(Block("h1", "TypeShield Authenticator Tutorial"))
    blocks.append(Block("p", "This beginner-friendly guide explains how the project works, step by step. It also explains each file and the important code sections so you can follow the flow without prior security or biometrics knowledge."))

    blocks.append(Block("h2", "1) What This Project Does"))
    blocks.append(Block("p", "TypeShield Authenticator combines a normal password with keystroke dynamics. That means it measures how you type (timing and rhythm) in addition to what you type."))
    blocks.append(Block("bullets", [
        "During registration, the app stores your password hash and a typing template.",
        "During login, it checks the password and compares your typing pattern.",
        "If the timing is too different, login is rejected even if the password is correct.",
    ]))

    blocks.append(Block("h2", "2) Quick Start (Beginner Setup)"))
    blocks.append(Block("p", "Run these steps from the project folder:"))
    blocks.append(Block("code", [
        "$ python3 -m venv .venv",
        "$ source .venv/bin/activate",
        "$ pip install -r requirements.txt",
        "$ createdb keyrythm",
        "$ uvicorn app.main:app --reload",
    ], snippet_id="setup", snippet_title="Snippet 1: Local setup commands", snippet_file="requirements.txt"))
    blocks.append(Block("p", "Open a browser and visit http://127.0.0.1:8000. Register first, then login."))

    blocks.append(Block("h2", "3) Project Structure"))
    blocks.append(Block("p", "Important files in this project:"))
    blocks.append(Block("bullets", [
        "app/main.py: FastAPI entry point and web routes.",
        "app/config.py: Environment settings (database URL, secret key, threshold).",
        "app/database.py: SQLModel engine and session helper.",
        "app/models.py: Database tables for users, templates, and attempts.",
        "app/schemas.py: Pydantic models that validate behaviour data.",
        "app/auth.py: Password hashing and JWT creation.",
        "app/behaviour.py: Scoring logic for typing similarity.",
        "app/utils.py: Helper math utilities.",
        "app/static/behaviour.js: Frontend capture of typing rhythm.",
        "app/templates/*.html: HTML pages for register, login, dashboard.",
    ]))

    blocks.append(Block("h2", "4) Configuration (app/config.py)"))
    blocks.append(Block("p", "Settings are loaded from environment variables. The most important values are the database URL, secret key, and behaviour threshold."))
    blocks.append(Block("code", [
        "class Settings(BaseSettings):",
        "    app_name: str = \"TypeShield Authenticator\"",
        "    secret_key: str = Field(\"super-secret-key-change-me\", env=\"SECRET_KEY\")",
        "    database_url: str = Field(DEFAULT_DB_URL, env=\"DATABASE_URL\")",
        "    behaviour_threshold: float = Field(75.0, env=\"BEHAVIOUR_THRESHOLD\")",
    ], snippet_id="config", snippet_title="Snippet 2: Settings model", snippet_file="app/config.py"))
    blocks.append(Block("p", "Beginner tip: put these values in a .env file so you do not hard-code secrets in code."))

    blocks.append(Block("h2", "5) Database Layer (app/database.py)"))
    blocks.append(Block("p", "The database engine is created once, and FastAPI uses a session dependency for each request."))
    blocks.append(Block("code", [
        "engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)",
        "",
        "def init_db() -> None:",
        "    SQLModel.metadata.create_all(engine)",
        "",
        "def get_session() -> Iterator[Session]:",
        "    session = Session(engine)",
        "    try:",
        "        yield session",
        "        session.commit()",
        "    except Exception:",
        "        session.rollback()",
        "        raise",
        "    finally:",
        "        session.close()",
    ], snippet_id="database", snippet_title="Snippet 3: Engine and session dependency", snippet_file="app/database.py"))
    blocks.append(Block("p", "FastAPI injects the session into route handlers with Depends(get_session)."))

    blocks.append(Block("h2", "6) Data Models (app/models.py)"))
    blocks.append(Block("p", "SQLModel classes become database tables. Each user has one behaviour template, and every login attempt is stored."))
    blocks.append(Block("code", [
        "class User(SQLModel, table=True):",
        "    id: Optional[int] = Field(default=None, primary_key=True)",
        "    username: str = Field(index=True, unique=True)",
        "    hashed_password: str",
        "",
        "class BehaviourTemplate(SQLModel, table=True):",
        "    user_id: int = Field(foreign_key=\"user.id\")",
        "    dwell_times: List[float] = Field(default_factory=list, sa_column=Column(JSON))",
        "    flight_times: List[float] = Field(default_factory=list, sa_column=Column(JSON))",
        "    total_time: float",
        "    error_count: int = Field(default=0)",
    ], snippet_id="models", snippet_title="Snippet 4: User and BehaviourTemplate", snippet_file="app/models.py"))

    blocks.append(Block("h2", "7) Request Validation (app/schemas.py)"))
    blocks.append(Block("p", "Pydantic ensures the timing values are valid and non-negative."))
    blocks.append(Block("code", [
        "class BehaviourData(BaseModel):",
        "    dwell_times: List[float] = Field(default_factory=list)",
        "    flight_times: List[float] = Field(default_factory=list)",
        "    total_time: float",
        "    error_count: int = 0",
        "    device_type: str = \"fine\"",
        "",
        "    @validator(\"total_time\")",
        "    def validate_total_time(cls, v: float) -> float:",
        "        if v < 0:",
        "            raise ValueError(\"total_time must be non-negative\")",
        "        return v",
    ], snippet_id="schemas", snippet_title="Snippet 5: BehaviourData validation", snippet_file="app/schemas.py"))

    blocks.append(Block("h2", "8) Password Hashing (app/auth.py)"))
    blocks.append(Block("p", "Passwords are never stored in plain text. They are hashed with PBKDF2-SHA256."))
    blocks.append(Block("code", [
        "pwd_context = CryptContext(schemes=[\"pbkdf2_sha256\"], deprecated=\"auto\")",
        "",
        "def hash_password(password: str) -> str:",
        "    return pwd_context.hash(password)",
        "",
        "def verify_password(plain_password: str, hashed_password: str) -> bool:",
        "    return pwd_context.verify(plain_password, hashed_password)",
    ], snippet_id="auth", snippet_title="Snippet 6: Password hashing helpers", snippet_file="app/auth.py"))

    blocks.append(Block("h2", "9) Behaviour Scoring (app/behaviour.py)"))
    blocks.append(Block("p", "The scoring function compares the stored template with the new attempt. It returns a score from 0 to 100 and checks a threshold."))
    blocks.append(Block("code", [
        "def similarity_score(stored: BehaviourTemplate, attempt: BehaviourData) -> tuple[float, dict]:",
        "    dwell_component = dwell_score(stored, attempt)",
        "    flight_component = flight_score(stored, attempt)",
        "    total_component = total_time_score(stored, attempt)",
        "    speed_component = speed_score(stored, attempt)",
        "    error_component = error_score(stored, attempt)",
        "    length_component = length_score(stored, attempt)",
        "    combined = (",
        "        weights[\"dwell\"] * dwell_component",
        "        + weights[\"flight\"] * flight_component",
        "        + weights[\"total\"] * total_component",
        "        + weights[\"speed\"] * speed_component",
        "        + weights[\"length\"] * length_component",
        "        + weights[\"error\"] * error_component",
        "    )",
        "    score = round(clamp(combined), 2)",
        "    return score, components",
    ], snippet_id="behaviour", snippet_title="Snippet 7: Similarity score", snippet_file="app/behaviour.py"))
    blocks.append(Block("p", "The is_behaviour_match function adds strong guards (key count and tempo) before accepting a score."))

    blocks.append(Block("h2", "10) Utility Math (app/utils.py)"))
    blocks.append(Block("p", "Two helpers handle clamping and average percentage difference between vectors."))
    blocks.append(Block("code", [
        "def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:",
        "    return max(minimum, min(maximum, value))",
        "",
        "def average_percentage_difference(reference: List[float], sample: List[float]) -> float:",
        "    if not reference or not sample:",
        "        return 100.0",
        "    diffs = []",
        "    for ref_val, sample_val in zip(reference[:min_len], sample[:min_len]):",
        "        denominator = ref_val if ref_val != 0 else 1e-6",
        "        diffs.append(abs(ref_val - sample_val) / denominator * 100)",
        "    return sum(diffs) / max_len if max_len else 100.0",
    ], snippet_id="utils", snippet_title="Snippet 8: Clamp and average difference", snippet_file="app/utils.py"))

    blocks.append(Block("h2", "11) FastAPI Routes (app/main.py)"))
    blocks.append(Block("p", "The main file wires everything together: app startup, register, login, dashboard, and logout."))
    blocks.append(Block("code", [
        "app = FastAPI(title=settings.app_name)",
        "app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)",
        "",
        "@app.on_event(\"startup\")",
        "def on_startup() -> None:",
        "    init_db()",
    ], snippet_id="main_setup", snippet_title="Snippet 9: App setup", snippet_file="app/main.py"))
    blocks.append(Block("p", "On startup, init_db creates tables if they do not exist."))

    blocks.append(Block("code", [
        "@app.post(\"/register\")",
        "def register(...):",
        "    statement = select(User).where(User.username == username)",
        "    if session.exec(statement).first():",
        "        return error",
        "    behaviour_parsed = BehaviourData.parse_raw(behaviour_data)",
        "    user = User(username=username, hashed_password=hash_password(password))",
        "    session.add(user)",
        "    session.flush()",
        "    template = BehaviourTemplate(user_id=user.id, ...)",
        "    session.add(template)",
        "    session.commit()",
        "    request.session[\"user_id\"] = user.id",
        "    return RedirectResponse(url=\"/dashboard\", status_code=302)",
    ], snippet_id="register", snippet_title="Snippet 10: Register flow", snippet_file="app/main.py"))

    blocks.append(Block("code", [
        "@app.post(\"/login\")",
        "def login(...):",
        "    user = session.exec(select(User).where(User.username == username)).first()",
        "    if not user or not verify_password(password, user.hashed_password):",
        "        return invalid credentials",
        "    stored_template = session.exec(select(BehaviourTemplate).where(...)).first()",
        "    behaviour_parsed = BehaviourData.parse_raw(behaviour_data)",
        "    is_match, score, reasons = behaviour.is_behaviour_match(stored_template, behaviour_parsed)",
        "    if not is_match:",
        "        return behaviour mismatch",
        "    request.session[\"user_id\"] = user.id",
        "    request.session[\"score\"] = score",
        "    return RedirectResponse(url=\"/dashboard\", status_code=302)",
    ], snippet_id="login", snippet_title="Snippet 11: Login flow", snippet_file="app/main.py"))

    blocks.append(Block("h2", "12) Frontend Capture (app/static/behaviour.js)"))
    blocks.append(Block("p", "The browser script captures dwell time (keydown to keyup) and flight time (gap between keys). It also tracks errors (backspace)."))
    blocks.append(Block("code", [
        "passwordInput.addEventListener(\"keydown\", (event) => {",
        "    if (event.key === \"Backspace\") {",
        "        errorCount += 1;",
        "        dwellTimes.pop();",
        "        flightTimes.pop();",
        "        return;",
        "    }",
        "    if (startTime === null) startTime = now;",
        "    if (lastKeyUp !== null) flightTimes.push(now - lastKeyUp);",
        "    pendingDown = now;",
        "});",
    ], snippet_id="behaviour_js", snippet_title="Snippet 12: Keydown capture", snippet_file="app/static/behaviour.js"))

    blocks.append(Block("h2", "13) Templates (HTML)"))
    blocks.append(Block("p", "Jinja2 templates render the forms and dashboard. They also include the behaviour.js script on register and login pages."))
    blocks.append(Block("code", [
        "<form method=\"post\" action=\"/login\">",
        "    <input type=\"text\" name=\"username\" required>",
        "    <input type=\"password\" id=\"password\" name=\"password\" required>",
        "    <input type=\"hidden\" id=\"behaviour_data\" name=\"behaviour_data\">",
        "</form>",
        "<script src=\"/static/behaviour.js\"></script>",
    ], snippet_id="template", snippet_title="Snippet 13: Login form captures behaviour", snippet_file="app/templates/login.html"))

    blocks.append(Block("h2", "14) Step-by-Step Data Flow"))
    blocks.append(Block("h3", "Register"))
    blocks.append(Block("bullets", [
        "User types password; behaviour.js records timing vectors.",
        "Form submits username, password, and behaviour JSON.",
        "Backend hashes password and stores BehaviourTemplate.",
        "Session is created and user is redirected to /dashboard.",
    ]))
    blocks.append(Block("h3", "Login"))
    blocks.append(Block("bullets", [
        "Password is checked with verify_password.",
        "Stored template is loaded from database.",
        "Behaviour score is computed; must be above threshold.",
        "On success, session and score are stored for dashboard.",
    ]))

    blocks.append(Block("h2", "15) Common Beginner Questions"))
    blocks.append(Block("bullets", [
        "Why store timing vectors? They capture how you type, not just what you type.",
        "Why JSON columns? Timing arrays fit naturally as JSON lists.",
        "What is behaviour_threshold? The minimum score required to accept a login.",
        "What happens on touch devices? The script switches to coarse capture.",
    ]))

    blocks.append(Block("h2", "16) Where To Explore Next"))
    blocks.append(Block("bullets", [
        "Try changing BEHAVIOUR_THRESHOLD to see stricter or softer matching.",
        "Add more charts or logs to the dashboard.",
        "Store multiple templates per user for more robust matching.",
    ]))

    return blocks


def build_index(snippet_pages: Dict[str, int]) -> List[Block]:
    entries = [
        ("setup", "Snippet 1: Local setup commands", "requirements.txt"),
        ("config", "Snippet 2: Settings model", "app/config.py"),
        ("database", "Snippet 3: Engine and session dependency", "app/database.py"),
        ("models", "Snippet 4: User and BehaviourTemplate", "app/models.py"),
        ("schemas", "Snippet 5: BehaviourData validation", "app/schemas.py"),
        ("auth", "Snippet 6: Password hashing helpers", "app/auth.py"),
        ("behaviour", "Snippet 7: Similarity score", "app/behaviour.py"),
        ("utils", "Snippet 8: Clamp and average difference", "app/utils.py"),
        ("main_setup", "Snippet 9: App setup", "app/main.py"),
        ("register", "Snippet 10: Register flow", "app/main.py"),
        ("login", "Snippet 11: Login flow", "app/main.py"),
        ("behaviour_js", "Snippet 12: Keydown capture", "app/static/behaviour.js"),
        ("template", "Snippet 13: Login form captures behaviour", "app/templates/login.html"),
    ]

    blocks: List[Block] = [Block("h2", "Code Snippets Index")]
    bullets = []
    for key, title, file_path in entries:
        page = snippet_pages.get(key, 0)
        bullets.append(f"{title} ({file_path}) - page {page}")
    blocks.append(Block("bullets", bullets))
    return blocks


def build_pdf(pages: List[List[Line]], output_path: str) -> None:
    objects: List[bytes] = []

    def add_object(data: str | bytes) -> int:
        if isinstance(data, str):
            data_bytes = data.encode("ascii")
        else:
            data_bytes = data
        objects.append(data_bytes)
        return len(objects)

    font1 = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font2 = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font3 = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_objects: List[int] = []
    content_objects: List[int] = []

    for idx, lines in enumerate(pages, start=1):
        content_lines = []
        for line in lines:
            text = escape_pdf_text(line.text)
            content_lines.append(
                f"BT /{line.font} {line.size} Tf 1 0 0 1 {line.x} {line.y} Tm ({text}) Tj ET"
            )
        # Footer with page number.
        footer_text = escape_pdf_text(f"Page {idx}")
        footer_x = PAGE_WIDTH // 2 - 20
        footer_y = BOTTOM_MARGIN - 10
        content_lines.append(
            f"BT /{FONT_NORMAL} 9 Tf 1 0 0 1 {footer_x} {footer_y} Tm ({footer_text}) Tj ET"
        )
        stream = "\n".join(content_lines)
        stream_bytes = stream.encode("ascii")
        content_obj = add_object(
            f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream"
        )
        content_objects.append(content_obj)

        page_obj = add_object(
            f"<< /Type /Page /Parent 0 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R /F3 {font3} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        page_objects.append(page_obj)

    pages_obj = add_object(
        "<< /Type /Pages /Kids ["
        + " ".join(f"{obj} 0 R" for obj in page_objects)
        + f"] /Count {len(page_objects)} >>"
    )

    # Fix parent references now that pages object is known.
    fixed_objects: List[bytes] = []
    for i, obj in enumerate(objects, start=1):
        if b"/Type /Page" in obj:
            fixed_objects.append(obj.replace(b"/Parent 0 0 R", f"/Parent {pages_obj} 0 R".encode("ascii")))
        else:
            fixed_objects.append(obj)
    objects = fixed_objects

    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>")

    # Write PDF.
    xref_offsets = []
    with open(output_path, "wb") as f:
        f.write(b"%PDF-1.4\n")
        for idx, obj in enumerate(objects, start=1):
            xref_offsets.append(f.tell())
            f.write(f"{idx} 0 obj\n".encode("ascii"))
            f.write(obj)
            f.write(b"\nendobj\n")
        xref_start = f.tell()
        f.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        f.write(b"0000000000 65535 f \n")
        for offset in xref_offsets:
            f.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        f.write(b"trailer\n")
        f.write(
            f"<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\n".encode("ascii")
        )
        f.write(b"startxref\n")
        f.write(f"{xref_start}\n".encode("ascii"))
        f.write(b"%%EOF\n")


def main() -> None:
    blocks = build_blocks()
    pages, snippet_pages = layout_blocks(blocks)
    index_blocks = build_index(snippet_pages)
    final_pages, _ = layout_blocks(blocks + index_blocks)
    build_pdf(final_pages, "docs/TypeShield_Tutorial.pdf")


if __name__ == "__main__":
    main()
