import io
import os
import shutil
import sys
import tempfile

import pytest
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app  # noqa: E402
from app.content import ensure_defaults  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import AdminUser  # noqa: E402
from config import TestConfig  # noqa: E402

ADMIN_USER = "tester"
ADMIN_PASS = "Very-Secure-Pass-123"


@pytest.fixture()
def app():
    upload_dir = tempfile.mkdtemp()

    class Cfg(TestConfig):
        UPLOAD_FOLDER = upload_dir

    application = create_app(Cfg)
    with application.app_context():
        db.drop_all()
        db.create_all()
        ensure_defaults()
        admin = AdminUser(username=ADMIN_USER)
        admin.set_password(ADMIN_PASS)
        db.session.add(admin)
        db.session.commit()
    # No app context is held during the test: each request gets its own
    # context and DB session, exactly like in production.
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
    shutil.rmtree(upload_dir, ignore_errors=True)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_client(client):
    resp = client.post("/admin/login", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    assert resp.status_code == 302
    return client


def make_image(fmt="PNG", size=(800, 500), color=(40, 90, 200)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, fmt)
    buf.seek(0)
    return buf
