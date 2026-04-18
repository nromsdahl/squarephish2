import logging
import smtplib
import ssl
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..models import SMTPConfig

logger = logging.getLogger(__name__)


def _send(smtp_config: SMTPConfig, msg):
    addr = smtp_config.host + ":" + smtp_config.port
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    if smtp_config.port == "465":
        with smtplib.SMTP_SSL(smtp_config.host, int(smtp_config.port), context=ctx) as server:
            server.login(smtp_config.username, smtp_config.password)
            server.send_message(msg)
    elif smtp_config.port == "587":
        with smtplib.SMTP(smtp_config.host, int(smtp_config.port)) as server:
            server.starttls(context=ctx)
            server.login(smtp_config.username, smtp_config.password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_config.host, int(smtp_config.port)) as server:
            server.login(smtp_config.username, smtp_config.password)
            server.send_message(msg)


def send_email(
    smtp_config: SMTPConfig,
    sender: str,
    recipients: list,
    subject: str,
    body: str,
):
    if not recipients:
        raise ValueError("No recipients provided")

    msg = MIMEMultipart("related")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    _send(smtp_config, msg)
    logger.info("Email sent to victim(s): %s", ", ".join(recipients))


def send_qr_email(
    smtp_config: SMTPConfig,
    sender: str,
    recipients: list,
    subject: str,
    body: str,
    qr_bytes: bytes,
):
    if not recipients:
        raise ValueError("No recipients provided")

    msg = MIMEMultipart("related")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    img = MIMEImage(qr_bytes, _subtype="png")
    img.add_header("Content-ID", "<qrcode>")
    img.add_header("Content-Disposition", "inline", filename="qrcode")
    msg.attach(img)

    _send(smtp_config, msg)
    logger.info("Email sent to victim(s): %s", ", ".join(recipients))
