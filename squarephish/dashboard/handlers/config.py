import logging

from flask import Blueprint, render_template, request

from ...database import load_config, save_config
from ...models import (
    ConfigData,
    SMTPConfig,
    SquarePhishConfig,
    EmailConfig,
    EntraConfig,
    RequestConfig,
)

logger = logging.getLogger(__name__)

config_bp = Blueprint("config", __name__)


@config_bp.route("/config", methods=["GET"])
def config_handler():
    data = load_config()
    return render_template(
        "config.html",
        smtp_config=data.smtp_config,
        squarephish_config=data.squarephish_config,
        email_config=data.email_config,
        entra_config=data.entra_config,
        request_config=data.request_config,
        active_page=data.active_page,
        title=data.title,
    )


@config_bp.route("/config", methods=["POST"])
def save_config_handler():
    try:
        config_data = ConfigData(
            smtp_config=SMTPConfig(
                host=request.form.get("smtpHost", ""),
                port=request.form.get("smtpPort", ""),
                username=request.form.get("smtpUsername", ""),
                password=request.form.get("smtpPassword", ""),
            ),
            squarephish_config=SquarePhishConfig(
                host=request.form.get("phishHost", ""),
                port=request.form.get("phishPort", ""),
            ),
            email_config=EmailConfig(
                sender=request.form.get("emailSender", ""),
                subject=request.form.get("emailSubject", ""),
                body=request.form.get("emailBody", ""),
            ),
            entra_config=EntraConfig(
                client_id=request.form.get("entraClientID", ""),
                scope=request.form.get("entraScope", ""),
                tenant=request.form.get("entraTenant", ""),
                auto_prt=request.form.get("autoPRT", ""),
            ),
            request_config=RequestConfig(
                user_agent=request.form.get("userAgent", ""),
            ),
        )
        save_config(config_data)
        return "Configuration saved successfully"
    except Exception as e:
        logger.error("Failed to save configuration: %s", e)
        return "Failed to save configuration", 500
