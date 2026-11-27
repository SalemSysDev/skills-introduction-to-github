"""Application factory."""
import os
import secrets

from flask import Flask, g, render_template, request, session
from markupsafe import Markup, escape

from config import Config
from .extensions import csrf, db
from .i18n import LANGUAGES, get_lang, t, tr
from .icons import ICON_NAMES, icon


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    config_class.validate(app.config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    if app.config.get("PROXY_FIX"):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    csrf.init_app(app)

    from .admin.routes import bp as admin_bp
    from .public.routes import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix=app.config["ADMIN_URL_PREFIX"])

    from .cli import register_cli

    register_cli(app)
    _register_request_hooks(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    return app


def _register_request_hooks(app):
    @app.before_request
    def set_language_and_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)
        requested = request.args.get("lang")
        if requested in LANGUAGES:
            session["lang"] = requested
        lang = session.get("lang", app.config["DEFAULT_LANG"])
        g.lang = lang if lang in LANGUAGES else "ar"

    @app.after_request
    def security_headers(response):
        nonce = getattr(g, "csp_nonce", "")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'",
        )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.blueprint == "admin":
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        if app.config.get("SESSION_COOKIE_SECURE"):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def _register_template_helpers(app):
    @app.template_filter("paragraphs")
    def paragraphs(text):
        """Escape user text and render blank-line separated paragraphs."""
        if not text:
            return ""
        blocks = [b.strip() for b in str(text).replace("\r\n", "\n").split("\n\n") if b.strip()]
        html = "".join(f"<p>{escape(b).replace(chr(10), Markup('<br>'))}</p>" for b in blocks)
        return Markup(html)

    # Globals are visible inside imported macros too (context processors are not).
    app.jinja_env.globals.update(icon=icon, t=t, tr=tr, icon_names=ICON_NAMES)

    @app.template_filter("lines")
    def lines(text):
        return [line.strip(" -•\t") for line in (text or "").splitlines() if line.strip(" -•\t")]

    @app.context_processor
    def inject_globals():
        from .content import get_profile, visible_sections

        lang = get_lang()
        return {
            "lang": lang,
            "dir": LANGUAGES[lang]["dir"],
            "other_lang": "en" if lang == "ar" else "ar",
            "profile": get_profile(),
            "nav_sections": visible_sections(),
            "csp_nonce": getattr(g, "csp_nonce", ""),
            "site_url": app.config.get("SITE_URL") or request.url_root.rstrip("/"),
        }


def _register_error_handlers(app):
    def render_error(code):
        try:
            return render_template("errors/error.html", code=code), code
        except Exception:  # noqa: BLE001 - e.g. database down while rendering an error
            return f"Error {code}", code

    @app.errorhandler(404)
    def not_found(_e):
        return render_error(404)

    @app.errorhandler(413)
    def too_large(_e):
        return render_error(413)

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return render_error(500)
