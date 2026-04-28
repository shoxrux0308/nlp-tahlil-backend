import os
import jwt
import datetime
import hashlib
import secrets

# JWT secret: prefer env; otherwise persist a dev-generated secret to .jwt_secret
def _load_secret() -> str:
    env = os.environ.get("JWT_SECRET")
    if env:
        return env
    path = os.path.join(os.path.dirname(__file__), ".jwt_secret")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    generated = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as f:
        f.write(generated)
    return generated


SECRET = _load_secret()
ALGO = "HS256"
TOKEN_TTL_DAYS = int(os.environ.get("TOKEN_TTL_DAYS", "7"))


def create_token(data: dict) -> str:
    payload = {
        **data,
        "exp": datetime.datetime.utcnow()
        + datetime.timedelta(days=TOKEN_TTL_DAYS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def hash_password(password: str, salt: str | None = None) -> str:
    """Return 'salt$hash' — salted SHA-256."""
    if salt is None:
        salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, salt) == stored
