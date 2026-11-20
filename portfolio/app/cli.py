"""Command-line tools:

    flask init-db                 create tables + default rows
    flask create-admin            create (or reset) the admin account
    flask seed [--no-demo]        fill the profile/skills/services with the owner's
                                  information + clearly marked demo content
    flask clear-demo              delete every demo item created by `seed`
    flask export-schema           regenerate database/schema.sql (MySQL DDL)
"""
import os

import click
from PIL import Image, ImageDraw, ImageFont

from .content import ensure_defaults
from .extensions import db
from .models import (
    AdminUser, GalleryImage, Profile, Project, ProjectCategory, ProjectImage,
    Service, Skill, SkillCategory, TimelineEntry,
)
from .utils.uploads import delete_image, store_pil_image

DEMO_TAG_AR = "[تجريبي]"
DEMO_TAG_EN = "[Demo]"


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all tables and default rows."""
        db.create_all()
        ensure_defaults()
        click.secho("✔ Database tables created.", fg="green")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Admin username", default=lambda: os.environ.get("ADMIN_USERNAME", "admin"))
    @click.password_option("--password", prompt="Admin password (min 10 chars)",
                           default=lambda: os.environ.get("ADMIN_PASSWORD"))
    def create_admin(username, password):
        """Create the admin user, or reset its password if it exists."""
        if not password or len(password) < 10:
            raise click.BadParameter("Password must be at least 10 characters.")
        admin = AdminUser.query.filter_by(username=username).first()
        if admin is None:
            admin = AdminUser(username=username)
            db.session.add(admin)
            action = "created"
        else:
            action = "updated"
        admin.set_password(password)
        db.session.commit()
        click.secho(f"✔ Admin '{username}' {action}.", fg="green")

    @app.cli.command("seed")
    @click.option("--demo/--no-demo", default=True, help="Also add clearly-marked demo projects/timeline/gallery.")
    def seed(demo):
        """Fill initial content (safe to run once on an empty database)."""
        db.create_all()
        ensure_defaults()
        seed_profile()
        seed_skills()
        seed_services()
        if demo:
            seed_demo()
        db.session.commit()
        click.secho("✔ Seed complete. Replace demo items from the admin dashboard.", fg="green")

    @app.cli.command("clear-demo")
    def clear_demo():
        """Remove every demo item created by `flask seed`."""
        removed = 0
        for project in Project.query.filter(Project.slug.like("demo-%")).all():
            for image in project.images:
                delete_image(image.path, image.thumb_path)
            db.session.delete(project)
            removed += 1
        for entry in TimelineEntry.query.filter(TimelineEntry.title_ar.like(f"%{DEMO_TAG_AR}%")).all():
            db.session.delete(entry)
            removed += 1
        for image in GalleryImage.query.filter(GalleryImage.caption_ar.like(f"%{DEMO_TAG_AR}%")).all():
            delete_image(image.path, image.thumb_path)
            db.session.delete(image)
            removed += 1
        ProjectCategory.query.filter(ProjectCategory.slug.like("demo-%")).delete(synchronize_session=False)
        profile = Profile.query.first()
        if profile and DEMO_TAG_AR in (profile.goals_ar or ""):
            profile.goals_ar = profile.goals_en = ""
        db.session.commit()
        click.secho(f"✔ Removed {removed} demo items.", fg="green")

    @app.cli.command("export-schema")
    def export_schema():
        """Write database/schema.sql from the SQLAlchemy models (MySQL dialect)."""
        from sqlalchemy.dialects import mysql
        from sqlalchemy.schema import CreateIndex, CreateTable

        dialect = mysql.dialect()
        out = [
            "-- Salem Makki Portfolio — MySQL schema",
            "-- Generated from app/models.py with `flask export-schema`.",
            "-- Usage:  mysql -u root -p < database/schema.sql",
            "",
            "CREATE DATABASE IF NOT EXISTS salem_portfolio",
            "  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            "USE salem_portfolio;",
            "SET NAMES utf8mb4;",
            "",
        ]
        for table in db.metadata.sorted_tables:
            ddl = str(CreateTable(table, if_not_exists=True).compile(dialect=dialect)).strip()
            out.append(ddl + " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n")
            for index in table.indexes:
                out.append(str(CreateIndex(index).compile(dialect=dialect)).strip() + ";")
            out.append("")
        out += [
            "-- Default section rows (visibility & order of the home page).",
            "INSERT IGNORE INTO sections (`key`, is_visible, sort_order) VALUES",
            "  ('about',1,1),('skills',1,2),('services',1,3),('projects',1,4),",
            "  ('timeline',1,5),('gallery',1,6),('contact',1,7);",
            "INSERT INTO profile (full_name_ar, full_name_en, display_name, brand_name, title_ar, title_en,",
            "  tagline_ar, tagline_en, is_available, availability_ar, availability_en, specialization_ar,",
            "  specialization_en, qualification_ar, qualification_en, location_ar, location_en, email,",
            "  whatsapp_number, github_url, facebook_url, linkedin_url, cv_url, meta_description_ar,",
            "  meta_description_en, created_at, updated_at)",
            "SELECT '','','','','','','','',1,'','','','','','','','','','','','','','','','',NOW(),NOW()",
            "WHERE NOT EXISTS (SELECT 1 FROM profile);",
            "",
            "-- The admin account is created with:  flask create-admin",
            "-- (passwords are hashed by the application and never stored in this file).",
        ]
        path = os.path.join(app.root_path, "..", "database", "schema.sql")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n")
        click.secho(f"✔ Wrote {os.path.normpath(path)}", fg="green")


# --------------------------------------------------------------------------
# Seed data — only information supplied by the owner, plus labelled demos.
# --------------------------------------------------------------------------
def seed_profile():
    p = Profile.query.first()
    if p.full_name_ar:
        return  # never overwrite an edited profile
    p.full_name_ar = "سالم عبدالسلام عبدالله"
    p.full_name_en = "Salem Abdulsalam Abdullah"
    p.display_name = "Salem Makki"
    p.brand_name = "Makki Developer"
    p.title_ar = "مبرمج ومحلل نظم"
    p.title_en = "Programmer & Systems Analyst"
    p.tagline_ar = "أحوّل الأفكار إلى حلول رقمية ذكية، وأبني أنظمة برمجية تخدم الواقع."
    p.tagline_en = "I turn ideas into smart digital solutions and build software systems that serve real needs."
    p.short_bio_ar = (
        "مبرمج ومحلل نظم، مهتم بتصميم وتطوير الحلول البرمجية، وبناء تطبيقات الويب والأنظمة الرقمية، "
        "وتحويل الأفكار والمتطلبات إلى حلول تقنية عملية ومنظمة."
    )
    p.short_bio_en = (
        "A programmer and systems analyst focused on designing and developing software solutions, building "
        "web applications and digital systems, and turning ideas and requirements into practical, well-structured technical solutions."
    )
    p.about_ar = (
        p.short_bio_ar
        + "\n\nأؤمن بأن كل نظام ناجح يبدأ بفهم عميق للمشكلة: أحلل المتطلبات، أصمم البنية وقواعد البيانات، "
        "ثم أحوّلها إلى تطبيق يعمل بكفاءة وسهل الاستخدام."
    )
    p.about_en = (
        p.short_bio_en
        + "\n\nI believe every successful system starts with a deep understanding of the problem: I analyse the "
        "requirements, design the architecture and the database, then turn them into an efficient, easy-to-use application."
    )
    p.specialization_ar = "برمجة وتحليل نظم"
    p.specialization_en = "Programming & Systems Analysis"
    p.interests_ar = "تطوير تطبيقات الويب\nتحليل وتصميم الأنظمة\nتصميم قواعد البيانات\nبناء الحلول البرمجية المخصصة"
    p.interests_en = "Web application development\nSystems analysis & design\nDatabase design\nCustom software solutions"
    p.goals_ar = f"{DEMO_TAG_AR} اكتب هنا أهدافك المهنية من لوحة التحكم ← البيانات الشخصية."
    p.goals_en = f"{DEMO_TAG_EN} Write your career goals here from Dashboard → Profile."
    p.availability_ar = "متاح لمشاريع جديدة"
    p.availability_en = "Available for new projects"
    p.meta_description_ar = "Salem Makki — مبرمج ومحلل نظم. تطوير تطبيقات الويب والأنظمة الرقمية وتصميم قواعد البيانات."
    p.meta_description_en = "Salem Makki — Programmer & Systems Analyst. Web applications, digital systems and database design."


SKILLS = [
    ("لغات البرمجة", "Programming Languages", "code", ["JavaScript", "PHP", "Python", "Java", "Kotlin"]),
    ("تطوير الواجهات الأمامية", "Frontend Development", "layout", ["HTML", "CSS", "JavaScript", "Flutter"]),
    ("تطوير الأنظمة الخلفية", "Backend Development", "server", ["PHP", "Python"]),
    ("إدارة قواعد البيانات", "Database Management", "database", ["MySQL"]),
    ("تحليل وتصميم الأنظمة", "Systems Analysis & Design", "workflow", ["Requirements Analysis", "Database Design"]),
    ("الأدوات والتقنيات", "Tools & Technologies", "wrench", ["Git"]),
]


def seed_skills():
    if SkillCategory.query.count():
        return
    for order, (ar, en, icon_name, names) in enumerate(SKILLS, start=1):
        category = SkillCategory(name_ar=ar, name_en=en, icon=icon_name, sort_order=order)
        category.skills = [Skill(name=n, sort_order=i) for i, n in enumerate(names, start=1)]
        db.session.add(category)


SERVICES = [
    ("globe", "تطوير الويب", "Web Development",
     "تطوير مواقع وتطبيقات ويب حديثة، سريعة ومتجاوبة مع جميع الشاشات.",
     "Building modern, fast and responsive websites and web applications."),
    ("server", "تطوير الأنظمة الخلفية", "Backend Development",
     "تطوير الأنظمة والخدمات الخلفية وواجهات API بشكل آمن ومنظم وقابل للتوسع.",
     "Developing secure, well-structured and scalable backend systems, services and APIs."),
    ("database", "تصميم قواعد البيانات", "Database Design",
     "تصميم وإدارة قواعد البيانات وبناء العلاقات بينها بما يضمن سلامة البيانات وأداءها.",
     "Designing and managing databases and their relationships for integrity and performance."),
    ("workflow", "تحليل الأنظمة", "Systems Analysis",
     "تحليل الأنظمة وتحديد المتطلبات وتحويلها إلى مخططات وحلول قابلة للتنفيذ.",
     "Analysing systems and gathering requirements, then turning them into actionable designs."),
    ("layout", "تنفيذ الواجهات", "UI Implementation",
     "تحويل التصاميم إلى واجهات ويب دقيقة وتفاعلية وسهلة الاستخدام.",
     "Turning designs into accurate, interactive and accessible web interfaces."),
    ("puzzle", "حلول برمجية مخصصة", "Software Solutions",
     "تطوير حلول برمجية مخصصة تلبي احتياجات عملك وتؤتمت إجراءاته.",
     "Building custom software solutions tailored to your business needs and workflows."),
]


def seed_services():
    if Service.query.count():
        return
    for order, (icon_name, ar, en, dar, den) in enumerate(SERVICES, start=1):
        db.session.add(Service(icon=icon_name, title_ar=ar, title_en=en, description_ar=dar,
                               description_en=den, sort_order=order, is_visible=True))


# ------------------------------------------------------------------ demo content
def _placeholder(label: str, sub: str, palette: tuple, size=(1600, 1000)) -> Image.Image:
    """Generate a clearly labelled placeholder image (gradient + blueprint grid)."""
    w, h = size
    img = Image.new("RGB", size, palette[0])
    draw = ImageDraw.Draw(img)
    c1, c2 = palette
    for x in range(w):
        r = x / w
        color = tuple(int(c1[i] + (c2[i] - c1[i]) * r) for i in range(3))
        draw.line([(x, 0), (x, h)], fill=color)
    for gx in range(0, w, 64):
        draw.line([(gx, 0), (gx, h)], fill=(255, 255, 255, 30), width=1)
    for gy in range(0, h, 64):
        draw.line([(0, gy), (w, gy)], fill=(255, 255, 255, 30), width=1)
    # window frame
    draw.rounded_rectangle([w * 0.12, h * 0.16, w * 0.88, h * 0.84], radius=28, outline=(255, 255, 255), width=4)
    for i, dot in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx = w * 0.12 + 48 + i * 40
        draw.ellipse([cx - 11, h * 0.16 + 26, cx + 11, h * 0.16 + 48], fill=dot)
    try:
        big, small = ImageFont.load_default(size=86), ImageFont.load_default(size=40)
    except TypeError:  # very old Pillow
        big = small = ImageFont.load_default()
    draw.text((w / 2, h / 2 - 30), label, fill="white", font=big, anchor="mm")
    draw.text((w / 2, h / 2 + 60), sub, fill=(230, 230, 255), font=small, anchor="mm")
    return img


PALETTES = [((37, 99, 235), (124, 58, 237)), ((15, 23, 42), (59, 130, 246)), ((109, 40, 217), (14, 165, 233))]


def seed_demo():
    if not Project.query.filter(Project.slug.like("demo-%")).count():
        web = ProjectCategory(slug="demo-web", name_ar="تطبيقات ويب", name_en="Web Apps", sort_order=1)
        systems = ProjectCategory(slug="demo-systems", name_ar="أنظمة", name_en="Systems", sort_order=2)
        db.session.add_all([web, systems])
        demos = [
            ("demo-project-1", web, "Flask, MySQL, JavaScript"),
            ("demo-project-2", systems, "PHP, MySQL, HTML, CSS"),
            ("demo-project-3", web, "Python, Git"),
        ]
        for i, (slug, cat, tech) in enumerate(demos, start=1):
            project = Project(
                slug=slug, category=cat, technologies=tech, sort_order=i, is_published=True,
                is_featured=(i == 1),
                title_ar=f"{DEMO_TAG_AR} مشروع تجريبي {i}",
                title_en=f"{DEMO_TAG_EN} Sample project {i}",
                summary_ar="هذا مشروع تجريبي لعرض شكل البطاقة. احذفه أو عدّله من لوحة التحكم ← المشاريع.",
                summary_en="A placeholder project to preview the card layout. Edit or delete it from Dashboard → Projects.",
                description_ar=(
                    "هذا وصف تجريبي فقط وليس مشروعاً حقيقياً.\n\n"
                    "اكتب هنا: المشكلة التي يحلها المشروع، دورك فيه، أهم المزايا، والتقنيات المستخدمة."
                ),
                description_en=(
                    "This is placeholder text, not a real project.\n\n"
                    "Describe here: the problem the project solves, your role, the key features and the technologies used."
                ),
            )
            for j in range(2):
                saved = store_pil_image(
                    _placeholder(f"DEMO PROJECT {i}", f"Screenshot {j + 1} - replace me", PALETTES[(i + j) % 3]),
                    "projects",
                )
                project.images.append(ProjectImage(path=saved["path"], thumb_path=saved["thumb_path"], sort_order=j))
            db.session.add(project)

    if not TimelineEntry.query.filter(TimelineEntry.title_ar.like(f"%{DEMO_TAG_AR}%")).count():
        examples = [
            ("education", "المؤهل الدراسي — مثال", "Qualification — example", "اسم الجامعة / المعهد", "University / Institute"),
            ("course", "دورة تدريبية — مثال", "Training course — example", "الجهة المنظِّمة", "Provider"),
            ("certificate", "شهادة — مثال", "Certificate — example", "الجهة المانحة", "Issuer"),
        ]
        for i, (kind, ar, en, org_ar, org_en) in enumerate(examples, start=1):
            db.session.add(TimelineEntry(
                kind=kind, sort_order=i, is_visible=True,
                title_ar=f"{DEMO_TAG_AR} {ar}", title_en=f"{DEMO_TAG_EN} {en}",
                organization_ar=org_ar, organization_en=org_en,
                description_ar="عنصر تجريبي — عدّله أو احذفه من لوحة التحكم ← التعليم والخبرات.",
                description_en="Placeholder entry — edit or delete it from Dashboard → Education & Experience.",
            ))

    if not GalleryImage.query.filter(GalleryImage.caption_ar.like(f"%{DEMO_TAG_AR}%")).count():
        for i, category in enumerate(GalleryImage.CATEGORIES, start=1):
            saved = store_pil_image(
                _placeholder(f"DEMO PHOTO {i}", category.upper(), PALETTES[i % 3], size=(1200, 900)), "gallery"
            )
            db.session.add(GalleryImage(
                category=category, sort_order=i, is_visible=True, **saved,
                caption_ar=f"{DEMO_TAG_AR} صورة تجريبية {i}", caption_en=f"{DEMO_TAG_EN} Placeholder photo {i}",
            ))
