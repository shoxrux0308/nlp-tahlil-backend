import os
import time
import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from auth import create_token, verify_token, hash_password, verify_password
from nlp_engine import NLPEngine, detect_language

TZ = ZoneInfo("Asia/Tashkent")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger("nlp")

app = FastAPI(
    title="NLP Tahlil Tizimi API",
    version="1.1.0",
    description="Uzbek NLP analysis backend: morphology, semantics, lexicon.",
)

# CORS
_cors_env = os.environ.get("CORS_ORIGINS")
if _cors_env:
    _origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    _origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

nlp = NLPEngine()
security = HTTPBearer()

DB_PATH = os.path.join(os.path.dirname(__file__), "nlp_data.db")


# ============================================================
# DB
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        "group" TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, title TEXT, text TEXT, analysis_type TEXT,
        word_count INTEGER, language TEXT, result TEXT,
        avg_confidence REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""
    )
    cols = {r[1] for r in conn.execute("PRAGMA table_info(analyses)").fetchall()}
    if "title" not in cols:
        conn.execute("ALTER TABLE analyses ADD COLUMN title TEXT")
    if "avg_confidence" not in cols:
        conn.execute("ALTER TABLE analyses ADD COLUMN avg_confidence REAL")

    # Seed default user if missing
    row = conn.execute(
        "SELECT id FROM users WHERE email=?", ("muhabbat@university.uz",)
    ).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO users (id, email, name, \"group\", password_hash) VALUES (?,?,?,?,?)",
            (
                "u1",
                "muhabbat@university.uz",
                "Shamsiddinova Muhabbat",
                "DI22-11",
                hash_password("password123"),
            ),
        )
    conn.commit()
    conn.close()


init_db()


# ============================================================
# MODELS
# ============================================================
class LoginReq(BaseModel):
    email: str
    password: str


class RegisterReq(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=80)
    group: str = Field(default="", max_length=40)
    password: str = Field(min_length=6, max_length=120)


class AnalyzeReq(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    analysis_type: str = "morphological"
    options: Optional[dict] = {}


# ============================================================
# MIDDLEWARE — logging + uncaught exception handler
# ============================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)
        log.info(
            "%s %s -> %s (%dms)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response
    except Exception as e:
        log.exception("Unhandled: %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Ichki server xatoligi: {type(e).__name__}"},
        )


# ============================================================
# AUTH HELPERS
# ============================================================
def auth(c: HTTPAuthorizationCredentials = Depends(security)):
    p = verify_token(c.credentials)
    if not p:
        raise HTTPException(401, "Token yaroqsiz yoki muddati oʻtgan")
    return p


def user_by_email(email: str):
    conn = get_db()
    row = conn.execute(
        'SELECT id, email, name, "group", password_hash FROM users WHERE email=?',
        (email,),
    ).fetchone()
    conn.close()
    return row


# ============================================================
# AUTH ENDPOINTS
# ============================================================
@app.post("/auth/login")
def login(req: LoginReq):
    row = user_by_email(req.email)
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(401, "Email yoki parol notoʻgʻri")
    token = create_token({"user_id": row["id"], "email": row["email"]})
    return {
        "token": token,
        "user": {
            "id": row["id"],
            "email": row["email"],
            "name": row["name"],
            "group": row["group"],
        },
    }


@app.post("/auth/register")
def register(req: RegisterReq):
    if user_by_email(req.email):
        raise HTTPException(409, "Bu email allaqachon roʻyxatdan oʻtgan")
    import uuid

    uid = "u_" + uuid.uuid4().hex[:10]
    conn = get_db()
    conn.execute(
        'INSERT INTO users (id, email, name, "group", password_hash) VALUES (?,?,?,?,?)',
        (uid, req.email, req.name, req.group, hash_password(req.password)),
    )
    conn.commit()
    conn.close()
    token = create_token({"user_id": uid, "email": req.email})
    return {
        "token": token,
        "user": {
            "id": uid,
            "email": req.email,
            "name": req.name,
            "group": req.group,
        },
    }


@app.get("/auth/me")
def me(user=Depends(auth)):
    row = user_by_email(user["email"])
    if not row:
        raise HTTPException(404, "Foydalanuvchi topilmadi")
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "group": row["group"],
    }


# ============================================================
# ANALYZE
# ============================================================
@app.post("/analyze")
def analyze(req: AnalyzeReq, user=Depends(auth)):
    if not req.text.strip():
        raise HTTPException(400, "Matn boʻsh boʻlishi mumkin emas")
    start = time.time()
    result = nlp.analyze(req.text, req.analysis_type, req.options or {})
    result["processing_time"] = round(time.time() - start, 3)
    result["analysis_type"] = req.analysis_type

    words = req.text.split()
    lang = detect_language(req.text)
    title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
    conf = (result.get("morphological") or {}).get("avg_confidence")

    conn = get_db()
    conn.execute(
        "INSERT INTO analyses (user_id, title, text, analysis_type, word_count, language, result, avg_confidence, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            user["user_id"],
            title,
            req.text,
            req.analysis_type,
            len(words),
            lang,
            json.dumps(result, ensure_ascii=False),
            conf,
            datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()

    result["title"] = title
    return result


# ============================================================
# STATS
# ============================================================
@app.get("/stats")
def stats(user=Depends(auth)):
    conn = get_db()
    today_str = datetime.now(TZ).date().isoformat()

    total = conn.execute(
        "SELECT COUNT(*) FROM analyses WHERE user_id=?", (user["user_id"],)
    ).fetchone()[0]
    today_count = conn.execute(
        "SELECT COUNT(*) FROM analyses WHERE user_id=? AND DATE(created_at)=?",
        (user["user_id"], today_str),
    ).fetchone()[0]
    all_texts = conn.execute(
        "SELECT text FROM analyses WHERE user_id=?", (user["user_id"],)
    ).fetchall()
    all_words = set()
    for row in all_texts:
        if row[0]:
            for w in row[0].split():
                all_words.add(w.lower().strip(".,!?;:\"'()[]{}"))
    vocab_size = len(all_words)

    lang_rows = conn.execute(
        "SELECT language, COUNT(*) as cnt FROM analyses WHERE user_id=? GROUP BY language",
        (user["user_id"],),
    ).fetchall()

    avg_conf_row = conn.execute(
        "SELECT AVG(avg_confidence) FROM analyses WHERE user_id=? AND avg_confidence IS NOT NULL",
        (user["user_id"],),
    ).fetchone()
    conn.close()

    lang_dist = {"uzbek": 0, "russian": 0, "english": 0}
    total_lang = sum(r["cnt"] for r in lang_rows) or 1
    for r in lang_rows:
        if r["language"] in lang_dist:
            lang_dist[r["language"]] = round(r["cnt"] / total_lang * 100)

    avg_conf = (
        avg_conf_row[0] if avg_conf_row and avg_conf_row[0] is not None else None
    )
    accuracy = round(avg_conf * 100, 1) if avg_conf is not None else 0.0

    return {
        "total_analyses": total,
        "today_analyses": today_count,
        "vocabulary_size": vocab_size,
        "accuracy": accuracy,
        "language_distribution": lang_dist,
    }


# ============================================================
# HISTORY
# ============================================================
@app.get("/history")
def history(user=Depends(auth)):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, text, analysis_type, word_count, created_at FROM analyses WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
        (user["user_id"],),
    ).fetchall()
    conn.close()

    items = []
    today = datetime.now(TZ).date().isoformat()
    for r in rows:
        words = (r["text"] or "").split()
        title = " ".join(words[:6]) + ("..." if len(words) > 6 else "")
        created = r["created_at"][:10] if r["created_at"] else ""
        if created == today:
            time_part = r["created_at"][11:16] if r["created_at"] else ""
            date_str = f"Bugun, {time_part}"
        elif created:
            from datetime import date as dt

            try:
                d = dt.fromisoformat(created)
                diff = (dt.today() - d).days
                time_part = r["created_at"][11:16] if r["created_at"] else ""
                date_str = (
                    f"Kecha, {time_part}"
                    if diff == 1
                    else f"{created}, {time_part}"
                )
            except Exception:
                date_str = created
        else:
            date_str = ""

        type_map = {
            "morphological": "Morfologik",
            "semantic": "Semantik",
            "lexical": "Leksik",
            "full": "Toʻliq",
        }
        items.append(
            {
                "id": str(r["id"]),
                "title": title or "Tahlil",
                "date": date_str,
                "type": type_map.get(r["analysis_type"], r["analysis_type"]),
                "word_count": r["word_count"] or 0,
            }
        )
    return {"items": items}


@app.delete("/history/{item_id}")
def delete_history(item_id: int, user=Depends(auth)):
    conn = get_db()
    conn.execute(
        "DELETE FROM analyses WHERE id=? AND user_id=?",
        (item_id, user["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/history/{item_id}/full")
def history_full(item_id: int, user=Depends(auth)):
    conn = get_db()
    row = conn.execute(
        "SELECT result FROM analyses WHERE id=? AND user_id=?",
        (item_id, user["user_id"]),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Tahlil topilmadi")
    return json.loads(row["result"] or "{}")


# ============================================================
# HEALTH
# ============================================================
@app.get("/health")
def health():
    return {"status": "ok", "version": app.version}


# ============================================================
# STATIC FRONTEND (Flutter web release build)
# Mounted LAST so API routes take precedence.
# ============================================================
_web_env = os.environ.get("WEB_BUILD_DIR")
if _web_env:
    _WEB_DIR = _web_env if os.path.isabs(_web_env) else os.path.join(os.path.dirname(__file__), _web_env)
else:
    _WEB_DIR = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "nlp_project", "build", "web")
    )


@app.get("/")
def _spa_root():
    index = os.path.join(_WEB_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return JSONResponse({"message": "NLP Tahlil Tizimi API", "web_build": False})


if os.path.isdir(_WEB_DIR):
    log.info("Serving Flutter web from %s", _WEB_DIR)

    @app.get("/{path:path}")
    def _spa_fallback(path: str):
        # API routes are registered first and take precedence.
        # This only catches static assets and SPA deep links.
        candidate = os.path.normpath(os.path.join(_WEB_DIR, path))
        if not candidate.startswith(_WEB_DIR):
            raise HTTPException(400, "Invalid path")
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        index = os.path.join(_WEB_DIR, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        raise HTTPException(404, "Not found")
else:
    log.warning(
        "Web build not found at %s — frontend will not be served", _WEB_DIR
    )
