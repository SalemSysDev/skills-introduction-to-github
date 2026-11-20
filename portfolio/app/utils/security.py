"""Authentication helpers and input sanitisation."""
import re
from datetime import timedelta
from functools import wraps
from urllib.parse import urlparse

from flask import current_app, flash, redirect, request, session, url_for

from ..extensions import db
from ..models import AdminUser, LoginAttempt, utcnow

EMAIL_RE = re.compile(r"^[^@\s<>\"']+@[^@\s<>\"']+\.[A-Za-z]{2,}$")


def client_ip() -> str:
    return (request.remote_addr or "unknown")[:64]


# ---------------------------------------------------------------- auth
def current_admin():
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    admin = db.session.get(AdminUser, admin_id)
    # Invalidate sessions after password change
    if admin is None or session.get("admin_pw") != admin.password_hash[-16:]:
        session.pop("admin_id", None)
        return None
    return admin


def login_admin(admin: AdminUser) -> None:
    lang = session.get("lang")
    session.clear()  # prevents session fixation
    if lang:
        session["lang"] = lang
    session.permanent = True
    session["admin_id"] = admin.id
    session["admin_pw"] = admin.password_hash[-16:]
    admin.last_login_at = utcnow()


def logout_admin() -> None:
    lang = session.get("lang")
    session.clear()
    if lang:
        session["lang"] = lang


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_admin() is None:
            flash("يرجى تسجيل الدخول أولاً.", "warning")
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapper


def is_locked_out(ip: str) -> bool:
    window = utcnow() - timedelta(minutes=current_app.config["LOGIN_LOCK_MINUTES"])
    failures = (
        LoginAttempt.query.filter(
            LoginAttempt.ip_address == ip,
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= window,
        ).count()
    )
    return failures >= current_app.config["LOGIN_MAX_ATTEMPTS"]


def record_attempt(ip: str, username: str, success: bool) -> None:
    db.session.add(LoginAttempt(ip_address=ip, username=(username or "")[:64], success=success))
    if success:  # clear failures for this IP after a successful login
        LoginAttempt.query.filter_by(ip_address=ip, success=False).delete()
    db.session.commit()


def safe_next(target: str | None, fallback: str) -> str:
    """Only allow relative redirects to this site (prevents open redirects)."""
    if not target:
        return fallback
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc or not target.startswith("/") or target.startswith("//"):
        return fallback
    return target


# ---------------------------------------------------------------- input
def clean(value, max_len: int | None = None) -> str:
    """Trim a text value and strip control characters."""
    text = (value or "").strip()
    text = "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32)
    text = text.replace("\r\n", "\n")
    return text[:max_len] if max_len else text


def clean_url(value, max_len: int = 255) -> str:
    """Accept only http(s) URLs; anything else becomes an empty string."""
    url = clean(value, max_len)
    if not url:
        return ""
    if re.match(r"^[a-z][a-z0-9+.-]*:(?!//)", url, re.I) and not re.match(r"^https?://", url, re.I):
        return ""  # javascript:, data:, mailto: ... are not allowed here
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parsed = urlparse(url)
    try:
        parsed.port  # raises ValueError on malformed ports
    except ValueError:
        return ""
    host = parsed.hostname or ""
    if parsed.scheme.lower() not in ("http", "https") or "." not in host or any(c.isspace() for c in url):
        return ""
    return url


def valid_email(value: str) -> bool:
    return bool(value) and len(value) <= 150 and bool(EMAIL_RE.match(value))


def to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def slugify(text: str, max_len: int = 120) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_len] or "item"
