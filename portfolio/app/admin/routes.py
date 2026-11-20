"""Admin dashboard routes. Every view except login requires an authenticated admin."""
from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, url_for,
)

from ..content import SECTION_LABELS_AR, all_sections, get_profile
from ..extensions import db
from ..models import (
    AdminUser, GalleryImage, Message, Project, ProjectCategory, ProjectImage,
    Service, Skill, SkillCategory, TimelineEntry,
)
from ..utils.security import (
    clean, clean_url, client_ip, current_admin, is_locked_out, login_admin,
    login_required, logout_admin, record_attempt, safe_next, slugify, to_int,
    valid_email,
)
from ..utils.uploads import UploadError, delete_image, save_image, thumb_of

bp = Blueprint("admin", __name__)

KIND_LABELS = {
    "education": "التعليم",
    "experience": "خبرة عملية",
    "course": "دورة تدريبية",
    "certificate": "شهادة",
    "achievement": "إنجاز",
}
GALLERY_LABELS = {"personal": "شخصية", "work": "أثناء العمل", "projects": "المشاريع", "events": "أنشطة ومشاركات"}
LEVEL_LABELS = {"": "— بدون —", "learning": "قيد التعلّم", "intermediate": "متوسط", "advanced": "متقدم"}


@bp.before_request
def load_admin():
    g.admin = current_admin()


@bp.context_processor
def admin_context():
    unread = Message.query.filter_by(is_read=False).count() if g.get("admin") else 0
    return {
        "admin": g.get("admin"),
        "unread_count": unread,
        "kind_labels": KIND_LABELS,
        "gallery_labels": GALLERY_LABELS,
        "level_labels": LEVEL_LABELS,
    }


# ----------------------------------------------------------------- helpers
def _set_bilingual(obj, fields: dict) -> None:
    """fields: {"title": 150, ...} → reads title_ar / title_en from the form."""
    for field, max_len in fields.items():
        for lang in ("ar", "en"):
            setattr(obj, f"{field}_{lang}", clean(request.form.get(f"{field}_{lang}"), max_len))


def _checkbox(name: str) -> bool:
    return request.form.get(name) in ("1", "on", "true")


def _unique_slug(model, base: str, exclude_id=None) -> str:
    base = slugify(base) or "item"
    slug, n = base, 2
    while True:
        query = model.query.filter_by(slug=slug)
        if exclude_id:
            query = query.filter(model.id != exclude_id)
        if not query.first():
            return slug
        slug, n = f"{base}-{n}", n + 1


def _flash_upload_errors(errors):
    for err in errors:
        flash(err, "error")


# ----------------------------------------------------------------- auth
@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.admin:
        return redirect(url_for("admin.dashboard"))
    no_admin = AdminUser.query.count() == 0
    if request.method == "POST":
        ip = client_ip()
        username = clean(request.form.get("username"), 64)
        password = request.form.get("password", "")
        if is_locked_out(ip):
            flash("تم إيقاف تسجيل الدخول مؤقتاً بسبب محاولات فاشلة متكررة. حاول لاحقاً.", "error")
            return render_template("admin/login.html", no_admin=no_admin), 429
        admin = AdminUser.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_admin(admin)
            record_attempt(ip, username, True)
            flash(f"مرحباً {admin.username} 👋", "success")
            return redirect(safe_next(request.args.get("next"), url_for("admin.dashboard")))
        record_attempt(ip, username, False)
        flash("اسم المستخدم أو كلمة المرور غير صحيحة.", "error")
        return render_template("admin/login.html", no_admin=no_admin, username=username), 401
    return render_template("admin/login.html", no_admin=no_admin)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_admin()
    flash("تم تسجيل الخروج.", "success")
    return redirect(url_for("admin.login"))


# ----------------------------------------------------------------- dashboard
@bp.route("/")
@login_required
def dashboard():
    profile = get_profile()
    stats = {
        "projects": Project.query.count(),
        "published": Project.query.filter_by(is_published=True).count(),
        "skills": Skill.query.count(),
        "services": Service.query.count(),
        "timeline": TimelineEntry.query.count(),
        "gallery": GalleryImage.query.count(),
        "messages": Message.query.count(),
    }
    checklist = [
        ("رفع الصورة الشخصية", bool(profile.avatar_path), url_for("admin.profile")),
        ("كتابة النبذة التعريفية", bool(profile.about_ar or profile.about_en), url_for("admin.profile")),
        ("إضافة البريد الإلكتروني", bool(profile.email), url_for("admin.profile") + "#contact"),
        ("إضافة رقم واتساب", bool(profile.whatsapp_number), url_for("admin.profile") + "#contact"),
        ("إضافة رابط GitHub", bool(profile.github_url), url_for("admin.profile") + "#contact"),
        ("إضافة رابط Facebook", bool(profile.facebook_url), url_for("admin.profile") + "#contact"),
        ("نشر مشروع حقيقي واحد على الأقل", Project.query.filter_by(is_published=True).filter(~Project.slug.like("demo-%")).count() > 0, url_for("admin.projects")),
        ("إضافة المؤهل الدراسي", TimelineEntry.query.filter_by(kind="education").filter(~TimelineEntry.title_ar.like("%[تجريبي]%")).count() > 0, url_for("admin.timeline")),
    ]
    recent = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, checklist=checklist, recent=recent)


# ----------------------------------------------------------------- profile
PROFILE_TEXT = {
    "full_name": 150, "title": 150, "tagline": 255, "short_bio": 1000, "availability": 120,
    "about": 6000, "specialization": 150, "qualification": 200, "interests": 2000,
    "goals": 2000, "location": 120, "meta_description": 300,
}
PROFILE_IMAGES = {"avatar": "avatar_path", "cover": "cover_path", "about_image": "about_image_path"}


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    p = get_profile()
    if request.method == "POST":
        _set_bilingual(p, PROFILE_TEXT)
        p.display_name = clean(request.form.get("display_name"), 100)
        p.brand_name = clean(request.form.get("brand_name"), 100)
        p.is_available = _checkbox("is_available")

        email = clean(request.form.get("email"), 150)
        if email and not valid_email(email):
            flash("البريد الإلكتروني غير صالح، لم يتم حفظه.", "error")
        else:
            p.email = email
        p.whatsapp_number = "".join(ch for ch in clean(request.form.get("whatsapp_number"), 30) if ch.isdigit() or ch == "+")
        for field in ("github_url", "facebook_url", "linkedin_url", "cv_url"):
            raw = clean(request.form.get(field))
            value = clean_url(raw)
            if raw and not value:
                flash(f"الرابط في الحقل {field} غير صالح.", "error")
            setattr(p, field, value)

        for input_name, attr in PROFILE_IMAGES.items():
            old = getattr(p, attr)
            if _checkbox(f"remove_{input_name}") and old:
                delete_image(old, thumb_of(old))
                setattr(p, attr, None)
            file = request.files.get(input_name)
            if file and file.filename:
                try:
                    saved = save_image(file, "profile", max_side=1400, thumb_side=480)
                except UploadError as exc:
                    flash(f"{exc}", "error")
                    continue
                if getattr(p, attr):
                    delete_image(getattr(p, attr), thumb_of(getattr(p, attr)))
                setattr(p, attr, saved["path"])
        db.session.commit()
        flash("تم حفظ البيانات الشخصية.", "success")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html", p=p)


# ----------------------------------------------------------------- sections
@bp.route("/sections", methods=["GET", "POST"])
@login_required
def sections():
    items = all_sections()
    if request.method == "POST":
        for s in items:
            s.is_visible = _checkbox(f"visible_{s.key}")
            s.sort_order = to_int(request.form.get(f"order_{s.key}"), s.sort_order)
        db.session.commit()
        flash("تم تحديث ظهور الأقسام وترتيبها.", "success")
        return redirect(url_for("admin.sections"))
    return render_template("admin/sections.html", items=items, labels=SECTION_LABELS_AR)


@bp.route("/sections/<key>/move/<direction>", methods=["POST"])
@login_required
def section_move(key, direction):
    items = all_sections()
    keys = [s.key for s in items]
    if key not in keys or direction not in ("up", "down"):
        abort(404)
    i = keys.index(key)
    j = i - 1 if direction == "up" else i + 1
    if 0 <= j < len(items):
        items[i], items[j] = items[j], items[i]
    for order, s in enumerate(items, start=1):
        s.sort_order = order
    db.session.commit()
    return redirect(url_for("admin.sections"))


# ----------------------------------------------------------------- projects
@bp.route("/projects")
@login_required
def projects():
    items = Project.query.order_by(Project.sort_order, Project.id.desc()).all()
    categories = ProjectCategory.query.order_by(ProjectCategory.sort_order, ProjectCategory.id).all()
    return render_template("admin/projects.html", items=items, categories=categories)


@bp.route("/projects/new", methods=["GET", "POST"])
@bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_form(project_id=None):
    project = db.session.get(Project, project_id) if project_id else Project()
    if project is None:
        abort(404)
    categories = ProjectCategory.query.order_by(ProjectCategory.sort_order, ProjectCategory.id).all()

    if request.method == "POST":
        _set_bilingual(project, {"title": 150, "summary": 300, "description": 10000})
        if not (project.title_ar or project.title_en):
            flash("يجب إدخال اسم المشروع (بالعربية أو الإنجليزية).", "error")
            return render_template("admin/project_form.html", project=project, categories=categories), 400

        techs = [clean(x, 40) for x in (request.form.get("technologies") or "").split(",")]
        project.technologies = ", ".join(x for x in techs if x)[:500]
        for field in ("github_url", "demo_url"):
            raw = clean(request.form.get(field))
            value = clean_url(raw)
            if raw and not value:
                flash("أحد الروابط غير صالح وتم تجاهله.", "warning")
            setattr(project, field, value)
        project.project_date = clean(request.form.get("project_date"), 30)
        category_id = to_int(request.form.get("category_id"))
        project.category_id = category_id if db.session.get(ProjectCategory, category_id) else None
        project.is_featured = _checkbox("is_featured")
        project.is_published = _checkbox("is_published")
        project.sort_order = to_int(request.form.get("sort_order"))
        requested_slug = clean(request.form.get("slug"), 150)
        project.slug = _unique_slug(Project, requested_slug or project.title_en or project.title_ar, project.id)

        if project.id is None:
            db.session.add(project)
        db.session.flush()

        # Update existing image captions / order
        for image in project.images:
            image.caption_ar = clean(request.form.get(f"img_caption_ar_{image.id}"), 200)
            image.caption_en = clean(request.form.get(f"img_caption_en_{image.id}"), 200)
            image.sort_order = to_int(request.form.get(f"img_order_{image.id}"), image.sort_order)

        # New images
        errors, next_order = [], (max([i.sort_order for i in project.images], default=0) + 1)
        for file in request.files.getlist("images"):
            if not file or not file.filename:
                continue
            try:
                saved = save_image(file, "projects")
            except UploadError as exc:
                errors.append(f"{file.filename}: {exc}")
                continue
            project.images.append(ProjectImage(path=saved["path"], thumb_path=saved["thumb_path"], sort_order=next_order))
            next_order += 1
        db.session.commit()
        _flash_upload_errors(errors)
        flash("تم حفظ المشروع.", "success")
        return redirect(url_for("admin.project_form", project_id=project.id))

    return render_template("admin/project_form.html", project=project, categories=categories)


@bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@login_required
def project_delete(project_id):
    project = db.get_or_404(Project, project_id)
    for image in project.images:
        delete_image(image.path, image.thumb_path)
    db.session.delete(project)
    db.session.commit()
    flash("تم حذف المشروع وصوره.", "success")
    return redirect(url_for("admin.projects"))


@bp.route("/projects/images/<int:image_id>/delete", methods=["POST"])
@login_required
def project_image_delete(image_id):
    image = db.get_or_404(ProjectImage, image_id)
    project_id = image.project_id
    delete_image(image.path, image.thumb_path)
    db.session.delete(image)
    db.session.commit()
    flash("تم حذف الصورة.", "success")
    return redirect(url_for("admin.project_form", project_id=project_id) + "#images")


@bp.route("/project-categories", methods=["POST"])
@bp.route("/project-categories/<int:category_id>", methods=["POST"])
@login_required
def project_category_save(category_id=None):
    category = db.get_or_404(ProjectCategory, category_id) if category_id else ProjectCategory()
    _set_bilingual(category, {"name": 100})
    if not (category.name_ar or category.name_en):
        flash("يجب إدخال اسم التصنيف.", "error")
        return redirect(url_for("admin.projects") + "#categories")
    category.sort_order = to_int(request.form.get("sort_order"))
    category.slug = _unique_slug(ProjectCategory, category.name_en or category.name_ar, category.id)
    if category.id is None:
        db.session.add(category)
    db.session.commit()
    flash("تم حفظ التصنيف.", "success")
    return redirect(url_for("admin.projects") + "#categories")


@bp.route("/project-categories/<int:category_id>/delete", methods=["POST"])
@login_required
def project_category_delete(category_id):
    category = db.get_or_404(ProjectCategory, category_id)
    for project in category.projects:
        project.category_id = None
    db.session.delete(category)
    db.session.commit()
    flash("تم حذف التصنيف (المشاريع المرتبطة أصبحت بدون تصنيف).", "success")
    return redirect(url_for("admin.projects") + "#categories")


# ----------------------------------------------------------------- skills
@bp.route("/skills")
@login_required
def skills():
    categories = SkillCategory.query.order_by(SkillCategory.sort_order, SkillCategory.id).all()
    return render_template("admin/skills.html", categories=categories)


@bp.route("/skill-categories", methods=["POST"])
@bp.route("/skill-categories/<int:category_id>", methods=["POST"])
@login_required
def skill_category_save(category_id=None):
    category = db.get_or_404(SkillCategory, category_id) if category_id else SkillCategory()
    _set_bilingual(category, {"name": 100})
    if not (category.name_ar or category.name_en):
        flash("يجب إدخال اسم التصنيف.", "error")
        return redirect(url_for("admin.skills"))
    category.icon = clean(request.form.get("icon"), 40) or "code"
    category.sort_order = to_int(request.form.get("sort_order"))
    if category.id is None:
        db.session.add(category)
    db.session.commit()
    flash("تم حفظ التصنيف.", "success")
    return redirect(url_for("admin.skills") + f"#cat-{category.id}")


@bp.route("/skill-categories/<int:category_id>/delete", methods=["POST"])
@login_required
def skill_category_delete(category_id):
    db.session.delete(db.get_or_404(SkillCategory, category_id))
    db.session.commit()
    flash("تم حذف التصنيف ومهاراته.", "success")
    return redirect(url_for("admin.skills"))


@bp.route("/skills/add/<int:category_id>", methods=["POST"])
@bp.route("/skills/<int:skill_id>", methods=["POST"])
@login_required
def skill_save(category_id=None, skill_id=None):
    if skill_id:
        skill = db.get_or_404(Skill, skill_id)
    else:
        db.get_or_404(SkillCategory, category_id)
        skill = Skill(category_id=category_id)
    skill.name = clean(request.form.get("name"), 80)
    if not skill.name:
        flash("يجب إدخال اسم المهارة.", "error")
        return redirect(url_for("admin.skills"))
    level = request.form.get("level", "")
    skill.level = level if level in Skill.LEVELS else ""
    skill.sort_order = to_int(request.form.get("sort_order"))
    if skill.id is None:
        db.session.add(skill)
    db.session.commit()
    flash("تم حفظ المهارة.", "success")
    return redirect(url_for("admin.skills") + f"#cat-{skill.category_id}")


@bp.route("/skills/<int:skill_id>/delete", methods=["POST"])
@login_required
def skill_delete(skill_id):
    skill = db.get_or_404(Skill, skill_id)
    category_id = skill.category_id
    db.session.delete(skill)
    db.session.commit()
    flash("تم حذف المهارة.", "success")
    return redirect(url_for("admin.skills") + f"#cat-{category_id}")


# ----------------------------------------------------------------- services
@bp.route("/services")
@login_required
def services():
    items = Service.query.order_by(Service.sort_order, Service.id).all()
    return render_template("admin/services.html", items=items)


@bp.route("/services/new", methods=["GET", "POST"])
@bp.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@login_required
def service_form(service_id=None):
    service = db.get_or_404(Service, service_id) if service_id else Service(is_visible=True)
    if request.method == "POST":
        _set_bilingual(service, {"title": 120, "description": 2000})
        if not (service.title_ar or service.title_en):
            flash("يجب إدخال اسم الخدمة.", "error")
            return render_template("admin/service_form.html", item=service), 400
        service.icon = clean(request.form.get("icon"), 40) or "code"
        service.is_visible = _checkbox("is_visible")
        service.sort_order = to_int(request.form.get("sort_order"))
        if service.id is None:
            db.session.add(service)
        db.session.commit()
        flash("تم حفظ الخدمة.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", item=service)


@bp.route("/services/<int:service_id>/delete", methods=["POST"])
@login_required
def service_delete(service_id):
    db.session.delete(db.get_or_404(Service, service_id))
    db.session.commit()
    flash("تم حذف الخدمة.", "success")
    return redirect(url_for("admin.services"))


# ----------------------------------------------------------------- timeline
@bp.route("/timeline")
@login_required
def timeline():
    items = TimelineEntry.query.order_by(TimelineEntry.kind, TimelineEntry.sort_order, TimelineEntry.id.desc()).all()
    return render_template("admin/timeline.html", items=items)


@bp.route("/timeline/new", methods=["GET", "POST"])
@bp.route("/timeline/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def timeline_form(entry_id=None):
    entry = db.get_or_404(TimelineEntry, entry_id) if entry_id else TimelineEntry(is_visible=True, kind=request.args.get("kind", "education"))
    if request.method == "POST":
        _set_bilingual(entry, {"title": 200, "organization": 200, "description": 4000})
        if not (entry.title_ar or entry.title_en):
            flash("يجب إدخال العنوان.", "error")
            return render_template("admin/timeline_form.html", item=entry), 400
        kind = request.form.get("kind")
        entry.kind = kind if kind in TimelineEntry.KINDS else "education"
        entry.start_date = clean(request.form.get("start_date"), 30)
        entry.end_date = clean(request.form.get("end_date"), 30)
        entry.link_url = clean_url(request.form.get("link_url"))
        entry.is_visible = _checkbox("is_visible")
        entry.sort_order = to_int(request.form.get("sort_order"))
        if entry.id is None:
            db.session.add(entry)
        db.session.commit()
        flash("تم الحفظ.", "success")
        return redirect(url_for("admin.timeline"))
    return render_template("admin/timeline_form.html", item=entry)


@bp.route("/timeline/<int:entry_id>/delete", methods=["POST"])
@login_required
def timeline_delete(entry_id):
    db.session.delete(db.get_or_404(TimelineEntry, entry_id))
    db.session.commit()
    flash("تم الحذف.", "success")
    return redirect(url_for("admin.timeline"))


# ----------------------------------------------------------------- gallery
@bp.route("/gallery", methods=["GET", "POST"])
@login_required
def gallery():
    if request.method == "POST":  # upload
        category = request.form.get("category")
        category = category if category in GalleryImage.CATEGORIES else "personal"
        errors, count = [], 0
        for file in request.files.getlist("images"):
            if not file or not file.filename:
                continue
            try:
                saved = save_image(file, "gallery")
            except UploadError as exc:
                errors.append(f"{file.filename}: {exc}")
                continue
            image = GalleryImage(category=category, is_visible=True, **saved)
            _set_bilingual(image, {"caption": 200})
            db.session.add(image)
            count += 1
        db.session.commit()
        _flash_upload_errors(errors)
        if count:
            flash(f"تم رفع {count} صورة.", "success")
        elif not errors:
            flash("لم يتم اختيار أي صورة.", "warning")
        return redirect(url_for("admin.gallery"))
    items = GalleryImage.query.order_by(GalleryImage.sort_order, GalleryImage.id.desc()).all()
    return render_template("admin/gallery.html", items=items)


@bp.route("/gallery/<int:image_id>", methods=["POST"])
@login_required
def gallery_update(image_id):
    image = db.get_or_404(GalleryImage, image_id)
    _set_bilingual(image, {"caption": 200})
    category = request.form.get("category")
    image.category = category if category in GalleryImage.CATEGORIES else image.category
    image.is_visible = _checkbox("is_visible")
    image.sort_order = to_int(request.form.get("sort_order"))
    db.session.commit()
    flash("تم تحديث الصورة.", "success")
    return redirect(url_for("admin.gallery") + f"#img-{image.id}")


@bp.route("/gallery/<int:image_id>/delete", methods=["POST"])
@login_required
def gallery_delete(image_id):
    image = db.get_or_404(GalleryImage, image_id)
    delete_image(image.path, image.thumb_path)
    db.session.delete(image)
    db.session.commit()
    flash("تم حذف الصورة.", "success")
    return redirect(url_for("admin.gallery"))


# ----------------------------------------------------------------- messages
@bp.route("/messages")
@login_required
def messages():
    show = request.args.get("show", "all")
    query = Message.query.order_by(Message.created_at.desc())
    if show == "unread":
        query = query.filter_by(is_read=False)
    page = query.paginate(page=to_int(request.args.get("page"), 1), per_page=20, error_out=False)
    return render_template("admin/messages.html", page=page, show=show)


@bp.route("/messages/<int:message_id>")
@login_required
def message_view(message_id):
    message = db.get_or_404(Message, message_id)
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    return render_template("admin/message_view.html", m=message)


@bp.route("/messages/<int:message_id>/toggle", methods=["POST"])
@login_required
def message_toggle(message_id):
    message = db.get_or_404(Message, message_id)
    message.is_read = not message.is_read
    db.session.commit()
    return redirect(url_for("admin.messages"))


@bp.route("/messages/<int:message_id>/delete", methods=["POST"])
@login_required
def message_delete(message_id):
    db.session.delete(db.get_or_404(Message, message_id))
    db.session.commit()
    flash("تم حذف الرسالة.", "success")
    return redirect(url_for("admin.messages"))


# ----------------------------------------------------------------- account
@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    admin = g.admin
    if request.method == "POST":
        current = request.form.get("current_password", "")
        if not admin.check_password(current):
            flash("كلمة المرور الحالية غير صحيحة.", "error")
            return redirect(url_for("admin.account"))
        username = clean(request.form.get("username"), 64)
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if len(username) < 3:
            flash("اسم المستخدم قصير جداً.", "error")
            return redirect(url_for("admin.account"))
        if AdminUser.query.filter(AdminUser.username == username, AdminUser.id != admin.id).first():
            flash("اسم المستخدم مستخدم مسبقاً.", "error")
            return redirect(url_for("admin.account"))
        admin.username = username
        if new_password:
            if len(new_password) < 10:
                flash("كلمة المرور الجديدة يجب ألا تقل عن 10 أحرف.", "error")
                return redirect(url_for("admin.account"))
            if new_password != confirm:
                flash("تأكيد كلمة المرور غير مطابق.", "error")
                return redirect(url_for("admin.account"))
            admin.set_password(new_password)
        db.session.commit()
        if new_password:
            login_admin(admin)  # refresh session fingerprint
            db.session.commit()
        flash("تم تحديث بيانات الحساب.", "success")
        return redirect(url_for("admin.account"))
    return render_template("admin/account.html")
