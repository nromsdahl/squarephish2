import logging
import os
import re

from flask import Blueprint, render_template, request

from ...database import load_config, save_email_sent
from ...email import send_email, send_qr_email, generate_qr_code, generate_qr_code_ascii

logger = logging.getLogger(__name__)

email_bp = Blueprint("email", __name__)

PRETEXT_MAP = {
    "qrCode": "pretexts/broker_auth/qrcode_email.html",
    "asciiQrCode": "pretexts/broker_auth/qrcode_ascii_email.html",
    "urlLink": "pretexts/broker_auth/url_email.html",
    "deviceCode": "pretexts/broker_auth/devicecode_email.html",
}


@email_bp.route("/pretext/<pretext_type>", methods=["GET"])
def pretext_handler(pretext_type):
    path = PRETEXT_MAP.get(pretext_type)
    if not path or not os.path.isfile(path):
        return "Pretext not found", 404
    with open(path, "r") as f:
        return f.read(), 200, {"Content-Type": "text/plain; charset=utf-8"}


@email_bp.route("/email", methods=["GET"])
def email_handler():
    return render_template("email.html", active_page="email", title="Send Email")


@email_bp.route("/email", methods=["POST"])
def send_email_handler():
    try:
        recipient_string = request.form.get("recipients", "").strip()
        email_body = request.form.get("emailBody", "")
        email_body_type = request.form.get("emailBodyType", "")
        auto = request.form.get("auto", "")

        # Clean up recipients: replace newlines with commas, split
        recipient_string = recipient_string.replace("\n", ",")
        recipients = [r.strip() for r in re.split(r",\s*", recipient_string) if r.strip()]

        config = load_config()
        smtp_config = config.smtp_config
        email_config = config.email_config

        if not all([smtp_config.host, smtp_config.port, smtp_config.username, smtp_config.password]):
            return "Invalid SMTP configuration", 500

        if not all([email_config.sender, email_config.subject, email_config.body]):
            return "Invalid Email configuration", 500

        for recipient in recipients:
            url = f"https://{config.squarephish_config.host}:{config.squarephish_config.port}/CkyAAx7xES?email={recipient}"
            if auto == "true":
                url += "&auto=true"

            body = email_body

            if email_body_type == "asciiQrCode":
                qr_ascii = generate_qr_code_ascii(url)
                body = body.replace("{QR_CODE}", qr_ascii)
                send_email(smtp_config, email_config.sender, [recipient], email_config.subject, body)
            elif email_body_type == "qrCode":
                qr_bytes = generate_qr_code(url, 256)
                send_qr_email(smtp_config, email_config.sender, [recipient], email_config.subject, body, qr_bytes)
            else:
                body = body.replace("{URL}", url)
                send_email(smtp_config, email_config.sender, [recipient], email_config.subject, body)

            # Track in DB (non-critical)
            try:
                save_email_sent(recipient, email_config.subject)
            except Exception:
                pass

        return "Email sent successfully"
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        return f"Failed to send email: {e}", 500
