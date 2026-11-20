"""Shared content accessors used by both public views and templates."""
from flask import g

from .extensions import db
from .models import Profile, Section

# key -> (nav label key, public endpoint, default order)
SECTION_META = {
    "about": ("nav.about", "public.about", 1),
    "skills": ("nav.skills", "public.skills", 2),
    "services": ("nav.services", "public.services", 3),
    "projects": ("nav.projects", "public.projects", 4),
    "timeline": ("nav.timeline", "public.timeline", 5),
    "gallery": ("nav.gallery", "public.gallery", 6),
    "contact": ("nav.contact", "public.contact", 7),
}

SECTION_LABELS_AR = {
    "about": "من أنا",
    "skills": "المهارات التقنية",
    "services": "الخدمات",
    "projects": "المشاريع",
    "timeline": "التعليم والخبرات",
    "gallery": "معرض الصور",
    "contact": "التواصل",
}


def ensure_defaults() -> None:
    """Create the singleton profile row and section rows if missing."""
    if Profile.query.first() is None:
        db.session.add(Profile())
    existing = {s.key for s in Section.query.all()}
    for key, (_, _, order) in SECTION_META.items():
        if key not in existing:
            db.session.add(Section(key=key, sort_order=order, is_visible=True))
    db.session.commit()


def get_profile() -> Profile:
    if "profile" not in g:
        profile = Profile.query.first()
        if profile is None:
            ensure_defaults()
            profile = Profile.query.first()
        g.profile = profile
    return g.profile


def all_sections():
    sections = Section.query.order_by(Section.sort_order, Section.id).all()
    if len(sections) < len(SECTION_META):
        ensure_defaults()
        sections = Section.query.order_by(Section.sort_order, Section.id).all()
    return [s for s in sections if s.key in SECTION_META]


def visible_sections():
    """List of dicts for visible sections, in configured order."""
    if "visible_sections" not in g:
        g.visible_sections = [
            {"key": s.key, "label": SECTION_META[s.key][0], "endpoint": SECTION_META[s.key][1]}
            for s in all_sections()
            if s.is_visible
        ]
    return g.visible_sections


def is_section_visible(key: str) -> bool:
    return any(s["key"] == key for s in visible_sections())
