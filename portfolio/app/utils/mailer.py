"""Optional e-mail notification when a new contact message arrives.

Configured through MAIL_* variables in `.env`. If not configured, this is a
no-op: messages are always stored in the database and visible in the admin
dashboard regardless.
"""
import smtplib
import ssl
import threading
from email.message import EmailMessage

from flask import current_app


def _send(config: dict, msg: EmailMessage, logger) -> None:
    try:
        context = ssl.create_default_context()
        if config["MAIL_PORT"] == 465:
            server = smtplib.SMTP_SSL(config["MAIL_SERVER"], 465, context=context, timeout=15)
        else:
            server = smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=15)
            if config["MAIL_USE_TLS"]:
                server.starttls(context=context)
        with server:
            if config["MAIL_USERNAME"]:
                server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"] or "")
            server.send_message(msg)
    except Exception:  # noqa: BLE001 - notification must never break the request
        logger.exception("Failed to send contact notification e-mail")


def notify_new_message(message) -> None:
    cfg = current_app.config
    if not (cfg.get("MAIL_SERVER") and cfg.get("MAIL_NOTIFY_TO")):
        return
    msg = EmailMessage()
    msg["Subject"] = f"[Portfolio] {message.subject or 'رسالة جديدة'}"
    msg["From"] = cfg.get("MAIL_SENDER") or cfg.get("MAIL_USERNAME")
    msg["To"] = cfg["MAIL_NOTIFY_TO"]
    msg["Reply-To"] = message.email
    msg.set_content(
        f"From: {message.name} <{message.email}>\n"
        f"Subject: {message.subject}\n\n{message.body}\n"
    )
    config = {k: cfg.get(k) for k in ("MAIL_SERVER", "MAIL_PORT", "MAIL_USE_TLS", "MAIL_USERNAME", "MAIL_PASSWORD")}
    threading.Thread(target=_send, args=(config, msg, current_app.logger), daemon=True).start()
