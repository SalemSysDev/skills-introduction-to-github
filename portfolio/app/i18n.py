"""Interface strings for the public site (Arabic / English).

Content (projects, services, ...) is bilingual in the database; this module
only holds the fixed interface labels.
"""
from flask import current_app, g, request, session

LANGUAGES = {
    "ar": {"name": "العربية", "dir": "rtl"},
    "en": {"name": "English", "dir": "ltr"},
}

STRINGS = {
    # Navigation
    "nav.home": ("الرئيسية", "Home"),
    "nav.about": ("من أنا", "About"),
    "nav.skills": ("المهارات", "Skills"),
    "nav.services": ("الخدمات", "Services"),
    "nav.projects": ("المشاريع", "Projects"),
    "nav.timeline": ("المسيرة", "Journey"),
    "nav.gallery": ("المعرض", "Gallery"),
    "nav.contact": ("تواصل", "Contact"),
    "nav.menu": ("القائمة", "Menu"),
    "nav.skip": ("انتقل إلى المحتوى", "Skip to content"),
    "theme.toggle": ("تبديل الوضع الداكن/الفاتح", "Toggle dark/light mode"),
    "lang.switch": ("English", "العربية"),
    "lang.switch_label": ("Switch to English", "التبديل إلى العربية"),

    # Hero
    "hero.cta_projects": ("استكشف أعمالي", "Explore my work"),
    "hero.cta_contact": ("تواصل معي", "Get in touch"),
    "hero.available": ("متاح لمشاريع جديدة", "Available for new projects"),
    "hero.scroll": ("مرّر للأسفل", "Scroll down"),

    # Section headings
    "about.title": ("من أنا", "About me"),
    "about.subtitle": ("نبذة تعريفية", "A short introduction"),
    "about.specialization": ("التخصص", "Specialization"),
    "about.qualification": ("المؤهل الدراسي", "Qualification"),
    "about.location": ("الموقع", "Location"),
    "about.interests": ("الاهتمامات", "Interests"),
    "about.goals": ("الأهداف المهنية", "Career goals"),
    "about.cv": ("تحميل السيرة الذاتية", "Download CV"),

    "skills.title": ("المهارات التقنية", "Technical skills"),
    "skills.subtitle": ("الأدوات والتقنيات التي أعمل بها", "Tools and technologies I work with"),
    "skills.level.learning": ("قيد التعلّم", "Learning"),
    "skills.level.intermediate": ("متوسط", "Intermediate"),
    "skills.level.advanced": ("متقدم", "Advanced"),

    "services.title": ("الخدمات", "Services"),
    "services.subtitle": ("كيف يمكنني مساعدتك", "How I can help you"),

    "projects.title": ("المشاريع والأعمال", "Projects & work"),
    "projects.subtitle": ("مختارات من أعمالي البرمجية", "Selected software work"),
    "projects.all": ("الكل", "All"),
    "projects.view_all": ("عرض كل المشاريع", "View all projects"),
    "projects.details": ("التفاصيل", "Details"),
    "projects.source": ("الكود المصدري", "Source code"),
    "projects.demo": ("معاينة مباشرة", "Live demo"),
    "projects.tech": ("التقنيات المستخدمة", "Technologies"),
    "projects.category": ("التصنيف", "Category"),
    "projects.date": ("التاريخ", "Date"),
    "projects.empty": ("لا توجد مشاريع منشورة بعد.", "No published projects yet."),
    "projects.back": ("العودة إلى المشاريع", "Back to projects"),
    "projects.gallery": ("صور المشروع", "Project screenshots"),
    "projects.overview": ("نظرة عامة", "Overview"),
    "projects.related": ("مشاريع أخرى", "More projects"),

    "timeline.title": ("التعليم والخبرات", "Education & experience"),
    "timeline.subtitle": ("محطات في مسيرتي", "Milestones along the way"),
    "timeline.present": ("حتى الآن", "Present"),
    "kind.education": ("التعليم", "Education"),
    "kind.experience": ("الخبرات العملية", "Experience"),
    "kind.course": ("الدورات التدريبية", "Courses"),
    "kind.certificate": ("الشهادات", "Certificates"),
    "kind.achievement": ("الإنجازات", "Achievements"),
    "timeline.empty": ("سيتم إضافة المحتوى قريباً.", "Content coming soon."),

    "gallery.title": ("معرض الصور", "Gallery"),
    "gallery.subtitle": ("لقطات من العمل والمشاريع والأنشطة", "Moments from work, projects and events"),
    "gallery.all": ("الكل", "All"),
    "gallery.cat.personal": ("شخصية", "Personal"),
    "gallery.cat.work": ("أثناء العمل", "At work"),
    "gallery.cat.projects": ("المشاريع", "Projects"),
    "gallery.cat.events": ("الأنشطة والمشاركات", "Events"),
    "gallery.empty": ("لا توجد صور بعد.", "No images yet."),
    "gallery.view_all": ("عرض المعرض كاملاً", "Open full gallery"),
    "lightbox.close": ("إغلاق", "Close"),
    "lightbox.prev": ("السابق", "Previous"),
    "lightbox.next": ("التالي", "Next"),

    "contact.title": ("تواصل معي", "Get in touch"),
    "contact.subtitle": ("لديك فكرة أو مشروع؟ لنتحدث", "Have an idea or a project? Let's talk"),
    "contact.intro": (
        "يسعدني استقبال رسائلك حول المشاريع، فرص العمل، أو أي استفسار تقني. سأرد عليك في أقرب وقت.",
        "I'm happy to hear about projects, job opportunities or any technical question. I'll reply as soon as I can.",
    ),
    "contact.name": ("الاسم", "Name"),
    "contact.email": ("البريد الإلكتروني", "Email"),
    "contact.subject": ("الموضوع", "Subject"),
    "contact.message": ("الرسالة", "Message"),
    "contact.send": ("إرسال الرسالة", "Send message"),
    "contact.sending": ("جارٍ الإرسال…", "Sending…"),
    "contact.success": ("تم إرسال رسالتك بنجاح، شكراً لتواصلك!", "Your message was sent successfully. Thank you!"),
    "contact.error": ("تعذّر إرسال الرسالة. يرجى مراجعة الحقول والمحاولة مجدداً.", "Could not send the message. Please check the fields and try again."),
    "contact.rate_limited": ("لقد أرسلت عدة رسائل مؤخراً. حاول لاحقاً.", "You have sent several messages recently. Please try again later."),
    "contact.copy": ("نسخ البريد", "Copy email"),
    "contact.copied": ("تم النسخ!", "Copied!"),
    "contact.whatsapp": ("واتساب", "WhatsApp"),
    "contact.direct": ("قنوات التواصل المباشر", "Direct channels"),
    "contact.err.name": ("يرجى إدخال اسمك (حرفان على الأقل).", "Please enter your name (at least 2 characters)."),
    "contact.err.email": ("يرجى إدخال بريد إلكتروني صحيح.", "Please enter a valid email address."),
    "contact.err.subject": ("الموضوع طويل جداً.", "Subject is too long."),
    "contact.err.message": ("يرجى كتابة رسالة (10 أحرف على الأقل).", "Please write a message (at least 10 characters)."),

    "footer.rights": ("جميع الحقوق محفوظة", "All rights reserved"),
    "footer.built": ("صُمّم وطُوّر بشغف", "Designed & built with care"),
    "footer.top": ("العودة للأعلى", "Back to top"),

    "error.404.title": ("الصفحة غير موجودة", "Page not found"),
    "error.404.text": ("يبدو أن هذا المسار غير موجود في النظام.", "This route doesn't exist in the system."),
    "error.500.title": ("حدث خطأ غير متوقع", "Something went wrong"),
    "error.500.text": ("نعمل على إصلاح المشكلة، حاول مرة أخرى لاحقاً.", "We're on it. Please try again later."),
    "error.413.title": ("الملف كبير جداً", "File too large"),
    "error.413.text": ("حجم الملفات المرفوعة يتجاوز الحد المسموح.", "The uploaded files exceed the allowed size."),
    "error.home": ("العودة للرئيسية", "Back home"),
}


def get_lang() -> str:
    lang = getattr(g, "lang", None)
    if lang:
        return lang
    default = current_app.config.get("DEFAULT_LANG", "ar")
    return session.get("lang", default) if request else default


def t(key: str) -> str:
    pair = STRINGS.get(key)
    if not pair:
        return key
    return pair[0] if get_lang() == "ar" else pair[1]


def tr(obj, field: str, default: str = "") -> str:
    """Return the localized value of `<field>_<lang>` with fallback."""
    if obj is None:
        return default
    lang = get_lang()
    other = "en" if lang == "ar" else "ar"
    value = getattr(obj, f"{field}_{lang}", None)
    if not value:
        value = getattr(obj, f"{field}_{other}", None)
    return value or default
