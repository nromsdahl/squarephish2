import json
import logging

from ..models import Credential, TokenResponse, PRTResult, ConfigData
from .connection import get_db

logger = logging.getLogger(__name__)


def _query_token(email: str) -> str:
    db = get_db()
    row = db.execute(
        "SELECT token FROM credentials WHERE email = ? ORDER BY timestamp DESC LIMIT 1",
        (email,),
    ).fetchone()
    if row is None:
        raise ValueError(f"No token found for {email}")
    return row[0]


def _query_metric(table_name: str) -> int:
    db = get_db()
    row = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    if row is None:
        return 0
    return row[0]


def _query_config_value(key: str, default: str) -> str:
    db = get_db()
    row = db.execute(
        "SELECT value FROM configuration WHERE key = ?", (key,)
    ).fetchone()
    if row is None:
        return default
    return row[0]


def _query_credentials() -> list:
    db = get_db()
    rows = db.execute("SELECT email, token FROM credentials").fetchall()
    credentials = []
    for email_str, token_str in rows:
        token_data = json.loads(token_str)
        token = TokenResponse(
            token_type=token_data.get("token_type", ""),
            scope=token_data.get("scope", ""),
            expires_in=token_data.get("expires_in", 0),
            ext_expires_in=token_data.get("ext_expires_in", 0),
            access_token=token_data.get("access_token", ""),
            refresh_token=token_data.get("refresh_token", ""),
            id_token=token_data.get("id_token", ""),
        )
        credentials.append(Credential(email=email_str, token=token))
    return credentials


def _insert_email_sent(recipient: str, subject: str):
    db = get_db()
    db.execute(
        "INSERT INTO emails_sent(email, subject) VALUES(?, ?)", (recipient, subject)
    )
    db.commit()


def _insert_email_scanned(recipient: str):
    db = get_db()
    db.execute("INSERT INTO emails_scanned(email) VALUES(?)", (recipient,))
    db.commit()


def _insert_credential(email: str, token: str):
    db = get_db()
    db.execute("INSERT INTO credentials(email, token) VALUES(?, ?)", (email, token))
    db.commit()


def _insert_prt(email: str, prt: str, session_key: str):
    db = get_db()
    db.execute(
        "INSERT INTO prt_tokens(email, prt, session_key) VALUES(?, ?, ?)",
        (email, prt, session_key),
    )
    db.commit()


def _query_prts() -> list:
    db = get_db()
    rows = db.execute("SELECT email, prt, session_key FROM prt_tokens").fetchall()
    return [PRTResult(email=r[0], prt=r[1], session_key=r[2]) for r in rows]


def _query_prt(email: str) -> PRTResult:
    db = get_db()
    row = db.execute(
        "SELECT email, prt, session_key FROM prt_tokens WHERE email = ? ORDER BY timestamp DESC LIMIT 1",
        (email,),
    ).fetchone()
    if row is None:
        raise ValueError(f"No PRT found for {email}")
    return PRTResult(email=row[0], prt=row[1], session_key=row[2])


def _clear_stats():
    db = get_db()
    db.execute("DELETE FROM emails_sent")
    db.execute("DELETE FROM emails_scanned")
    db.commit()


def _clear_credentials():
    db = get_db()
    db.execute("DELETE FROM credentials")
    db.commit()


def _clear_prts():
    db = get_db()
    db.execute("DELETE FROM prt_tokens")
    db.commit()


def _insert_config(config: ConfigData):
    db = get_db()

    # Fixed: saves all 13 keys (Go version only saved 9, missing Entra + RequestConfig)
    config_items = {
        "smtpHost": config.smtp_config.host,
        "smtpPort": config.smtp_config.port,
        "smtpUsername": config.smtp_config.username,
        "smtpPassword": config.smtp_config.password,
        "phishHost": config.squarephish_config.host,
        "phishPort": config.squarephish_config.port,
        "emailSender": config.email_config.sender,
        "emailSubject": config.email_config.subject,
        "emailBody": config.email_config.body,
        "entraClientID": config.entra_config.client_id,
        "entraScope": config.entra_config.scope,
        "entraTenant": config.entra_config.tenant,
        "userAgent": config.request_config.user_agent,
        "autoPRT": config.entra_config.auto_prt,
    }

    for key, value in config_items.items():
        db.execute(
            "INSERT INTO configuration (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
    db.commit()
