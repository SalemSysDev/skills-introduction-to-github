"""Database models.

Bilingual content uses paired columns: `<field>_ar` and `<field>_en`.
Templates read them through the `tr(obj, "field")` helper, which picks the
current language and falls back to the other one if a value is empty.
"""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)


# --------------------------------------------------------------------------
# Administration
# --------------------------------------------------------------------------
class AdminUser(TimestampMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login_at = db.Column(db.DateTime)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(64), nullable=False, index=True)
    username = db.Column(db.String(64))
    success = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)


# --------------------------------------------------------------------------
# Profile & site settings (single row)
# --------------------------------------------------------------------------
class Profile(TimestampMixin, db.Model):
    __tablename__ = "profile"

    id = db.Column(db.Integer, primary_key=True)

    # Identity
    full_name_ar = db.Column(db.String(150), nullable=False, default="")
    full_name_en = db.Column(db.String(150), nullable=False, default="")
    display_name = db.Column(db.String(100), nullable=False, default="")
    brand_name = db.Column(db.String(100), nullable=False, default="")
    title_ar = db.Column(db.String(150), nullable=False, default="")
    title_en = db.Column(db.String(150), nullable=False, default="")

    # Hero
    tagline_ar = db.Column(db.String(255), nullable=False, default="")
    tagline_en = db.Column(db.String(255), nullable=False, default="")
    short_bio_ar = db.Column(db.Text)
    short_bio_en = db.Column(db.Text)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    availability_ar = db.Column(db.String(120), nullable=False, default="")
    availability_en = db.Column(db.String(120), nullable=False, default="")

    # About
    about_ar = db.Column(db.Text)
    about_en = db.Column(db.Text)
    specialization_ar = db.Column(db.String(150), nullable=False, default="")
    specialization_en = db.Column(db.String(150), nullable=False, default="")
    qualification_ar = db.Column(db.String(200), nullable=False, default="")
    qualification_en = db.Column(db.String(200), nullable=False, default="")
    interests_ar = db.Column(db.Text)
    interests_en = db.Column(db.Text)
    goals_ar = db.Column(db.Text)
    goals_en = db.Column(db.Text)
    location_ar = db.Column(db.String(120), nullable=False, default="")
    location_en = db.Column(db.String(120), nullable=False, default="")

    # Images (paths relative to static/)
    avatar_path = db.Column(db.String(255))
    cover_path = db.Column(db.String(255))
    about_image_path = db.Column(db.String(255))

    # Contact & social
    email = db.Column(db.String(150), nullable=False, default="")
    whatsapp_number = db.Column(db.String(30), nullable=False, default="")
    github_url = db.Column(db.String(255), nullable=False, default="")
    facebook_url = db.Column(db.String(255), nullable=False, default="")
    linkedin_url = db.Column(db.String(255), nullable=False, default="")
    cv_url = db.Column(db.String(255), nullable=False, default="")

    # SEO
    meta_description_ar = db.Column(db.String(300), nullable=False, default="")
    meta_description_en = db.Column(db.String(300), nullable=False, default="")

    @property
    def whatsapp_link(self) -> str:
        digits = "".join(ch for ch in (self.whatsapp_number or "") if ch.isdigit())
        return f"https://wa.me/{digits}" if digits else ""


class Section(db.Model):
    """Controls visibility and order of the home page sections."""

    __tablename__ = "sections"

    KEYS = ("about", "skills", "services", "projects", "timeline", "gallery", "contact")

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(30), unique=True, nullable=False)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# --------------------------------------------------------------------------
# Skills
# --------------------------------------------------------------------------
class SkillCategory(db.Model):
    __tablename__ = "skill_categories"

    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(100), nullable=False, default="")
    name_en = db.Column(db.String(100), nullable=False, default="")
    icon = db.Column(db.String(40), nullable=False, default="code")
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    skills = db.relationship(
        "Skill",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="Skill.sort_order, Skill.id",
    )


class Skill(db.Model):
    __tablename__ = "skills"

    LEVELS = ("", "learning", "intermediate", "advanced")

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("skill_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(80), nullable=False)
    level = db.Column(db.String(20), nullable=False, default="")  # optional, editable — no fake percentages
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    category = db.relationship("SkillCategory", back_populates="skills")


# --------------------------------------------------------------------------
# Services
# --------------------------------------------------------------------------
class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title_ar = db.Column(db.String(120), nullable=False, default="")
    title_en = db.Column(db.String(120), nullable=False, default="")
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    icon = db.Column(db.String(40), nullable=False, default="code")
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------
class ProjectCategory(db.Model):
    __tablename__ = "project_categories"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    name_ar = db.Column(db.String(100), nullable=False, default="")
    name_en = db.Column(db.String(100), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    projects = db.relationship("Project", back_populates="category")


class Project(TimestampMixin, db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("project_categories.id", ondelete="SET NULL"), index=True
    )
    title_ar = db.Column(db.String(150), nullable=False, default="")
    title_en = db.Column(db.String(150), nullable=False, default="")
    summary_ar = db.Column(db.String(300), nullable=False, default="")
    summary_en = db.Column(db.String(300), nullable=False, default="")
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    technologies = db.Column(db.String(500), nullable=False, default="")  # comma separated
    github_url = db.Column(db.String(255), nullable=False, default="")
    demo_url = db.Column(db.String(255), nullable=False, default="")
    project_date = db.Column(db.String(30), nullable=False, default="")  # free text, e.g. "2025"
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    category = db.relationship("ProjectCategory", back_populates="projects")
    images = db.relationship(
        "ProjectImage",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectImage.sort_order, ProjectImage.id",
    )

    @property
    def tech_list(self):
        return [t.strip() for t in (self.technologies or "").split(",") if t.strip()]

    @property
    def cover(self):
        return self.images[0] if self.images else None


class ProjectImage(db.Model):
    __tablename__ = "project_images"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path = db.Column(db.String(255), nullable=False)
    thumb_path = db.Column(db.String(255), nullable=False)
    caption_ar = db.Column(db.String(200), nullable=False, default="")
    caption_en = db.Column(db.String(200), nullable=False, default="")
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    project = db.relationship("Project", back_populates="images")


# --------------------------------------------------------------------------
# Education, experience, courses, certificates, achievements
# --------------------------------------------------------------------------
class TimelineEntry(db.Model):
    __tablename__ = "timeline_entries"

    KINDS = ("education", "experience", "course", "certificate", "achievement")

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False, default="education", index=True)
    title_ar = db.Column(db.String(200), nullable=False, default="")
    title_en = db.Column(db.String(200), nullable=False, default="")
    organization_ar = db.Column(db.String(200), nullable=False, default="")
    organization_en = db.Column(db.String(200), nullable=False, default="")
    description_ar = db.Column(db.Text)
    description_en = db.Column(db.Text)
    start_date = db.Column(db.String(30), nullable=False, default="")
    end_date = db.Column(db.String(30), nullable=False, default="")
    link_url = db.Column(db.String(255), nullable=False, default="")
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# --------------------------------------------------------------------------
# Gallery
# --------------------------------------------------------------------------
class GalleryImage(TimestampMixin, db.Model):
    __tablename__ = "gallery_images"

    CATEGORIES = ("personal", "work", "projects", "events")

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False, default="personal", index=True)
    path = db.Column(db.String(255), nullable=False)
    thumb_path = db.Column(db.String(255), nullable=False)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    caption_ar = db.Column(db.String(200), nullable=False, default="")
    caption_en = db.Column(db.String(200), nullable=False, default="")
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


# --------------------------------------------------------------------------
# Contact messages
# --------------------------------------------------------------------------
class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False, default="")
    body = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(64), index=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
