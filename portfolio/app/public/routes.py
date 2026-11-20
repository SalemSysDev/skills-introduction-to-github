"""Public (visitor-facing) routes."""
from collections import OrderedDict
from datetime import timedelta

from flask import (
    Blueprint, abort, current_app, flash, jsonify, make_response, redirect,
    render_template, request, session, url_for,
)

from ..content import is_section_visible, visible_sections
from ..extensions import db
from ..i18n import LANGUAGES, t
from ..models import (
    GalleryImage, Message, Project, ProjectCategory, Service, SkillCategory,
    TimelineEntry, utcnow,
)
from ..utils.mailer import notify_new_message
from ..utils.security import clean, client_ip, safe_next, valid_email

bp = Blueprint("public", __name__)


# ------------------------------------------------------------------ data loaders
def _skill_categories():
    return SkillCategory.query.order_by(SkillCategory.sort_order, SkillCategory.id).all()


def _services():
    return Service.query.filter_by(is_visible=True).order_by(Service.sort_order, Service.id).all()


def _published_projects():
    return Project.query.filter_by(is_published=True).order_by(
        Project.is_featured.desc(), Project.sort_order, Project.id.desc()
    )


def _project_categories():
    """Only categories that contain at least one published project."""
    return (
        ProjectCategory.query.join(Project)
        .filter(Project.is_published.is_(True))
        .distinct()
        .order_by(ProjectCategory.sort_order, ProjectCategory.id)
        .all()
    )


def _timeline_groups():
    entries = (
        TimelineEntry.query.filter_by(is_visible=True)
        .order_by(TimelineEntry.sort_order, TimelineEntry.id.desc())
        .all()
    )
    groups = OrderedDict((kind, []) for kind in TimelineEntry.KINDS)
    for entry in entries:
        groups.setdefault(entry.kind, []).append(entry)
    return OrderedDict((k, v) for k, v in groups.items() if v)


def _gallery(limit=None):
    query = GalleryImage.query.filter_by(is_visible=True).order_by(
        GalleryImage.sort_order, GalleryImage.id.desc()
    )
    return query.limit(limit).all() if limit else query.all()


def _require_section(key):
    if not is_section_visible(key):
        abort(404)


# ------------------------------------------------------------------ pages
@bp.route("/")
def home():
    keys = [s["key"] for s in visible_sections()]
    ctx = {"home_sections": keys, "is_home": True}
    if "skills" in keys:
        ctx["skill_categories"] = _skill_categories()
    if "services" in keys:
        ctx["services"] = _services()
    if "projects" in keys:
        ctx["projects"] = _published_projects().limit(6).all()
        ctx["project_total"] = _published_projects().count()
    if "timeline" in keys:
        ctx["timeline_groups"] = _timeline_groups()
    if "gallery" in keys:
        ctx["gallery_images"] = _gallery(limit=8)
        ctx["gallery_total"] = GalleryImage.query.filter_by(is_visible=True).count()
    return render_template("public/home.html", **ctx)


@bp.route("/about")
def about():
    _require_section("about")
    return render_template("public/page.html", section="about", page_title=t("about.title"))


@bp.route("/skills")
def skills():
    _require_section("skills")
    return render_template(
        "public/page.html", section="skills", page_title=t("skills.title"),
        skill_categories=_skill_categories(),
    )


@bp.route("/services")
def services():
    _require_section("services")
    return render_template(
        "public/page.html", section="services", page_title=t("services.title"), services=_services()
    )


@bp.route("/journey")
def timeline():
    _require_section("timeline")
    return render_template(
        "public/page.html", section="timeline", page_title=t("timeline.title"),
        timeline_groups=_timeline_groups(),
    )


@bp.route("/gallery")
def gallery():
    _require_section("gallery")
    return render_template(
        "public/page.html", section="gallery", page_title=t("gallery.title"),
        gallery_images=_gallery(), full_gallery=True,
    )


@bp.route("/projects")
def projects():
    _require_section("projects")
    categories = _project_categories()
    active = request.args.get("category", "")
    query = _published_projects()
    if active:
        category = ProjectCategory.query.filter_by(slug=active).first_or_404()
        query = query.filter(Project.category_id == category.id)
    return render_template(
        "public/projects.html", projects=query.all(), categories=categories,
        active_category=active, page_title=t("projects.title"),
    )


@bp.route("/projects/<slug>")
def project_detail(slug):
    _require_section("projects")
    project = Project.query.filter_by(slug=slug, is_published=True).first_or_404()
    related = (
        _published_projects().filter(Project.id != project.id).limit(3).all()
    )
    return render_template("public/project_detail.html", project=project, related=related)


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    _require_section("contact")
    wants_json = request.headers.get("X-Requested-With") == "fetch"

    if request.method == "GET":
        return render_template("public/page.html", section="contact", page_title=t("contact.title"))

    form = {
        "name": clean(request.form.get("name"), 120),
        "email": clean(request.form.get("email"), 150),
        "subject": clean(request.form.get("subject"), 200),
        "message": clean(request.form.get("message"), 5000),
    }

    # Honeypot: real visitors never fill the hidden "website" field.
    if request.form.get("website"):
        return _contact_response(wants_json, True, t("contact.success"))

    errors = {}
    if len(form["name"]) < 2:
        errors["name"] = t("contact.err.name")
    if not valid_email(form["email"]):
        errors["email"] = t("contact.err.email")
    if len(request.form.get("subject", "")) > 200:
        errors["subject"] = t("contact.err.subject")
    if len(form["message"]) < 10:
        errors["message"] = t("contact.err.message")
    if errors:
        return _contact_response(wants_json, False, t("contact.error"), errors, 400)

    ip = client_ip()
    since = utcnow() - timedelta(hours=1)
    recent = Message.query.filter(Message.ip_address == ip, Message.created_at >= since).count()
    if recent >= current_app.config["CONTACT_MAX_PER_HOUR"]:
        return _contact_response(wants_json, False, t("contact.rate_limited"), status=429)

    message = Message(
        name=form["name"], email=form["email"], subject=form["subject"],
        body=form["message"], ip_address=ip,
    )
    db.session.add(message)
    db.session.commit()
    notify_new_message(message)
    return _contact_response(wants_json, True, t("contact.success"))


def _contact_response(wants_json, ok, text, errors=None, status=200):
    if wants_json:
        return jsonify({"ok": ok, "message": text, "errors": errors or {}}), status
    flash(text, "success" if ok else "error")
    return redirect(url_for("public.contact") + "#contact")


# ------------------------------------------------------------------ utilities
@bp.route("/lang/<code>")
def set_language(code):
    if code not in LANGUAGES:
        abort(404)
    session["lang"] = code
    target = safe_next(request.args.get("next"), url_for("public.home"))
    return redirect(target)


@bp.route("/robots.txt")
def robots():
    admin_prefix = current_app.config["ADMIN_URL_PREFIX"]
    body = (
        "User-agent: *\n"
        f"Disallow: {admin_prefix}/\n"
        f"Sitemap: {url_for('public.sitemap', _external=True)}\n"
    )
    return current_app.response_class(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap():
    pages = [url_for("public.home", _external=True)]
    for section in visible_sections():
        pages.append(url_for(section["endpoint"], _external=True))
    if is_section_visible("projects"):
        for project in _published_projects().all():
            pages.append(url_for("public.project_detail", slug=project.slug, _external=True))
    xml = render_template("public/sitemap.xml", pages=pages)
    response = make_response(xml)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response


@bp.app_errorhandler(400)
def bad_request(error):
    """CSRF failures and malformed requests."""
    from flask_wtf.csrf import CSRFError

    if isinstance(error, CSRFError):
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify({"ok": False, "message": t("contact.error"), "errors": {}}), 400
        flash("انتهت صلاحية الجلسة أو الطلب غير صالح. حاول مرة أخرى.", "error")
        return redirect(safe_next(request.path, url_for("public.home")))
    return render_template("errors/error.html", code=400), 400

