import io
import os

from app.extensions import db
from app.models import (
    GalleryImage, Message, Profile, Project, Section, Service, Skill, SkillCategory, TimelineEntry,
)

from .conftest import ADMIN_PASS, ADMIN_USER, make_image

PUBLIC_PAGES = ["/", "/about", "/skills", "/services", "/projects", "/journey", "/gallery", "/contact",
                "/robots.txt", "/sitemap.xml"]


# ------------------------------------------------------------------ public site
def test_public_pages_render(client):
    for url in PUBLIC_PAGES:
        assert client.get(url).status_code == 200, url


def test_language_switch_and_rtl(client):
    html = client.get("/?lang=en").get_data(as_text=True)
    assert 'lang="en" dir="ltr"' in html
    html = client.get("/").get_data(as_text=True)  # remembered in session
    assert 'dir="ltr"' in html
    client.get("/lang/ar?next=/projects")
    assert 'dir="rtl"' in client.get("/").get_data(as_text=True)


def test_lang_switch_blocks_open_redirect(client):
    resp = client.get("/lang/en?next=https://evil.example.com")
    assert resp.headers["Location"].endswith("/")
    assert "evil" not in resp.headers["Location"]


def test_security_headers(client):
    resp = client.get("/")
    assert "Content-Security-Policy" in resp.headers
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"


def test_404_page(client):
    assert client.get("/does-not-exist").status_code == 404
    assert client.get("/projects/unknown").status_code == 404


def test_hidden_section_is_unavailable(client, app):
    with app.app_context():
        Section.query.filter_by(key="gallery").first().is_visible = False
        db.session.commit()
    assert client.get("/gallery").status_code == 404
    assert 'href="#gallery"' not in client.get("/").get_data(as_text=True)


def test_unpublished_project_hidden(client, app):
    with app.app_context():
        db.session.add(Project(slug="secret", title_en="Secret", is_published=False))
        db.session.commit()
    assert client.get("/projects/secret").status_code == 404


def test_xss_is_escaped(client, app):
    with app.app_context():
        Profile.query.first().about_en = "<script>alert(1)</script>"
        db.session.commit()
    html = client.get("/about?lang=en").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# ------------------------------------------------------------------ contact form
def test_contact_success_json(client, app):
    resp = client.post("/contact", headers={"X-Requested-With": "fetch"}, data={
        "name": "Ali", "email": "ali@example.com", "subject": "Hi", "message": "I have a project for you."})
    assert resp.status_code == 200 and resp.json["ok"] is True
    with app.app_context():
        assert Message.query.count() == 1


def test_contact_validation(client, app):
    resp = client.post("/contact", headers={"X-Requested-With": "fetch"},
                       data={"name": "A", "email": "bad", "message": "short"})
    assert resp.status_code == 400
    assert set(resp.json["errors"]) == {"name", "email", "message"}
    with app.app_context():
        assert Message.query.count() == 0


def test_contact_honeypot_and_rate_limit(client, app):
    client.post("/contact", data={"name": "Bot", "email": "b@b.com", "message": "spam spam spam", "website": "x"})
    with app.app_context():
        assert Message.query.count() == 0
    payload = {"name": "Ali", "email": "ali@example.com", "message": "A sufficiently long message"}
    for _ in range(app.config["CONTACT_MAX_PER_HOUR"]):
        assert client.post("/contact", data=payload).status_code == 302
    resp = client.post("/contact", data=payload, headers={"X-Requested-With": "fetch"})
    assert resp.status_code == 429


# ------------------------------------------------------------------ authentication
def test_admin_requires_login(client):
    for url in ["/admin/", "/admin/profile", "/admin/projects", "/admin/messages", "/admin/gallery"]:
        resp = client.get(url)
        assert resp.status_code == 302 and "/admin/login" in resp.headers["Location"], url
    assert client.post("/admin/projects/1/delete").status_code == 302


def test_login_wrong_password_and_lockout(client, app):
    for _ in range(app.config["LOGIN_MAX_ATTEMPTS"]):
        assert client.post("/admin/login", data={"username": ADMIN_USER, "password": "nope"}).status_code == 401
    # even the right password is refused while locked
    resp = client.post("/admin/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    assert resp.status_code == 429


def test_login_logout(admin_client):
    assert admin_client.get("/admin/").status_code == 200
    admin_client.post("/admin/logout")
    assert admin_client.get("/admin/").status_code == 302


def test_admin_pages_render(admin_client):
    for url in ["/admin/", "/admin/profile", "/admin/sections", "/admin/projects", "/admin/projects/new",
                "/admin/skills", "/admin/services", "/admin/services/new", "/admin/timeline",
                "/admin/timeline/new", "/admin/gallery", "/admin/messages", "/admin/account"]:
        resp = admin_client.get(url)
        assert resp.status_code == 200, url
        assert resp.headers["Cache-Control"] == "no-store"


def test_password_change_invalidates_old_sessions(app, admin_client):
    other = app.test_client()
    other.post("/admin/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    assert other.get("/admin/").status_code == 200
    admin_client.post("/admin/account", data={
        "current_password": ADMIN_PASS, "username": ADMIN_USER,
        "new_password": "Another-Strong-Pass-9", "confirm_password": "Another-Strong-Pass-9"})
    assert admin_client.get("/admin/").status_code == 200   # current session refreshed
    assert other.get("/admin/").status_code == 302           # old session invalidated


# ------------------------------------------------------------------ content management
def test_profile_update_with_avatar(admin_client, app):
    resp = admin_client.post("/admin/profile", content_type="multipart/form-data", data={
        "full_name_ar": "سالم", "full_name_en": "Salem", "display_name": "Salem Makki",
        "email": "me@example.com", "github_url": "github.com/someone", "facebook_url": "javascript:alert(1)",
        "whatsapp_number": "+967 777 000 000",
        "avatar": (make_image(), "me.png")})
    assert resp.status_code == 302
    with app.app_context():
        p = Profile.query.first()
        assert p.github_url == "https://github.com/someone"
        assert p.facebook_url == ""             # dangerous URL rejected
        assert p.whatsapp_link == "https://wa.me/967777000000"
        assert p.avatar_path.endswith(".webp")
        assert os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"], "profile", os.path.basename(p.avatar_path)))
    html = admin_client.get("/").get_data(as_text=True)
    assert "https://wa.me/967777000000" in html and "me@example.com" in html


def test_project_crud_with_images(admin_client, app):
    resp = admin_client.post("/admin/projects/new", content_type="multipart/form-data", data={
        "title_en": "Inventory System", "title_ar": "نظام مخزون", "technologies": "Flask, MySQL",
        "github_url": "https://github.com/x/y", "is_published": "1",
        "images": [(make_image(), "a.png"), (make_image("JPEG"), "b.jpg")]})
    assert resp.status_code == 302
    with app.app_context():
        project = Project.query.filter_by(slug="inventory-system").first()
        assert project and len(project.images) == 2 and project.tech_list == ["Flask", "MySQL"]
        pid, image_id = project.id, project.images[0].id
        paths = [os.path.join(app.config["UPLOAD_FOLDER"], "projects", os.path.basename(i.path)) for i in project.images]
    assert client_page_ok(admin_client, "/projects/inventory-system", "Inventory System")

    assert admin_client.post(f"/admin/projects/images/{image_id}/delete").status_code == 302
    assert not os.path.exists(paths[0])
    assert admin_client.post(f"/admin/projects/{pid}/delete").status_code == 302
    with app.app_context():
        assert db.session.get(Project, pid) is None
    assert not os.path.exists(paths[1])


def client_page_ok(client, url, text):
    resp = client.get(url + "?lang=en")
    return resp.status_code == 200 and text in resp.get_data(as_text=True)


def test_upload_rejects_non_images(admin_client, app):
    fake = io.BytesIO(b"<?php system($_GET['c']); ?>")
    admin_client.post("/admin/gallery", content_type="multipart/form-data",
                      data={"category": "work", "images": [(fake, "shell.png")]})
    exe = io.BytesIO(b"MZ....")
    admin_client.post("/admin/gallery", content_type="multipart/form-data",
                      data={"category": "work", "images": [(exe, "virus.exe")]})
    with app.app_context():
        assert GalleryImage.query.count() == 0
    admin_client.post("/admin/gallery", content_type="multipart/form-data",
                      data={"category": "work", "caption_en": "At work", "images": [(make_image(), "ok.png")]})
    with app.app_context():
        assert GalleryImage.query.count() == 1


def test_skills_services_timeline_crud(admin_client, app):
    admin_client.post("/admin/skill-categories", data={"name_ar": "أدوات", "name_en": "Tools", "icon": "wrench"})
    with app.app_context():
        cat = SkillCategory.query.filter_by(name_en="Tools").first()
        cat_id = cat.id
    admin_client.post(f"/admin/skills/add/{cat_id}", data={"name": "Docker", "level": "bogus"})
    with app.app_context():
        skill = Skill.query.filter_by(name="Docker").first()
        assert skill.level == ""                 # invalid level ignored
    admin_client.post("/admin/services/new", data={"title_en": "Consulting", "icon": "lightbulb", "is_visible": "1"})
    admin_client.post("/admin/timeline/new", data={"kind": "certificate", "title_en": "Cert X", "is_visible": "1"})
    with app.app_context():
        assert Service.query.filter_by(title_en="Consulting").count() == 1
        assert TimelineEntry.query.filter_by(kind="certificate").count() == 1
    html = admin_client.get("/?lang=en").get_data(as_text=True)
    assert "Docker" in html and "Consulting" in html and "Cert X" in html


def test_sections_reorder(admin_client, app):
    admin_client.post("/admin/sections/contact/move/up")
    with app.app_context():
        order = [s.key for s in Section.query.order_by(Section.sort_order).all()]
    assert order.index("contact") < order.index("gallery")


def test_messages_management(admin_client, app):
    with app.app_context():
        db.session.add(Message(name="N", email="n@x.com", subject="S", body="Hello there!"))
        db.session.commit()
        mid = Message.query.first().id
    assert admin_client.get(f"/admin/messages/{mid}").status_code == 200
    with app.app_context():
        assert db.session.get(Message, mid).is_read is True
    admin_client.post(f"/admin/messages/{mid}/delete")
    with app.app_context():
        assert Message.query.count() == 0


def test_csrf_enforced_when_enabled(app):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    resp = client.post("/contact", data={"name": "Ali", "email": "a@b.com", "message": "long enough msg"})
    assert resp.status_code == 302  # rejected & redirected with a flash message
    with app.app_context():
        assert Message.query.count() == 0
