import logging

from ..models import (
    ConfigData,
    SMTPConfig,
    SquarePhishConfig,
    EmailConfig,
    EntraConfig,
    RequestConfig,
    DashboardData,
    Credential,
    PRTResult,
)
from .connection import connect as _connect, close as _close
from .schema import migrate as _migrate
from .repository import (
    _query_config_value,
    _query_metric,
    _query_credentials,
    _query_token,
    _query_prts,
    _query_prt,
    _insert_config,
    _insert_credential,
    _insert_email_sent,
    _insert_email_scanned,
    _insert_prt,
    _clear_stats,
    _clear_credentials,
    _clear_prts,
)

logger = logging.getLogger(__name__)


def initialize():
    _connect()
    _migrate()


def close():
    _close()


def load_config() -> ConfigData:
    smtp_host = _query_config_value("smtpHost", "")
    smtp_port = _query_config_value("smtpPort", "")
    smtp_username = _query_config_value("smtpUsername", "")
    smtp_password = _query_config_value("smtpPassword", "")

    phish_host = _query_config_value("phishHost", "")
    phish_port = _query_config_value("phishPort", "")

    email_sender = _query_config_value("emailSender", "")
    email_subject = _query_config_value("emailSubject", "")
    email_body = _query_config_value("emailBody", "")

    entra_client_id = _query_config_value(
        "entraClientID", "29d9ed98-a469-4536-ade2-f981bc1d605e"
    )
    entra_scope = _query_config_value(
        "entraScope", ".default offline_access profile openid"
    )
    entra_tenant = _query_config_value("entraTenant", "organizations")
    auto_prt = _query_config_value("autoPRT", "")

    user_agent = _query_config_value(
        "userAgent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.3179.85",
    )

    return ConfigData(
        smtp_config=SMTPConfig(
            host=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
        ),
        squarephish_config=SquarePhishConfig(host=phish_host, port=phish_port),
        email_config=EmailConfig(
            sender=email_sender, subject=email_subject, body=email_body
        ),
        entra_config=EntraConfig(
            client_id=entra_client_id, scope=entra_scope, tenant=entra_tenant,
            auto_prt=auto_prt,
        ),
        request_config=RequestConfig(user_agent=user_agent),
        active_page="config",
        title="Configuration Settings",
    )


def load_dashboard_data() -> DashboardData:
    emails_sent = _query_metric("emails_sent")
    emails_scanned = _query_metric("emails_scanned")

    try:
        credentials = _query_credentials()
    except Exception as e:
        logger.error("Error querying credentials: %s", e)
        credentials = []

    try:
        prt_results = _query_prts()
    except Exception as e:
        logger.error("Error querying PRT tokens: %s", e)
        prt_results = []

    return DashboardData(
        emails_sent=emails_sent,
        emails_scanned=emails_scanned,
        credentials=credentials,
        prt_results=prt_results,
        active_page="dashboard",
        title="Dashboard",
    )


def load_token(email: str) -> str:
    return _query_token(email)


def save_config(config: ConfigData):
    _insert_config(config)


def save_token(email: str, token: str):
    _insert_credential(email, token)


def save_prt(email: str, prt: str, session_key: str):
    _insert_prt(email, prt, session_key)


def load_prt(email: str) -> PRTResult:
    return _query_prt(email)


def clear_stats():
    _clear_stats()


def clear_credentials():
    _clear_credentials()


def clear_prts():
    _clear_prts()


def save_email_sent(recipient: str, subject: str):
    _insert_email_sent(recipient, subject)


def save_email_scanned(recipient: str):
    _insert_email_scanned(recipient)
