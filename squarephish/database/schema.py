import logging

from .connection import get_db

logger = logging.getLogger(__name__)

MIGRATIONS = [
    "CREATE TABLE IF NOT EXISTS configuration  (key TEXT PRIMARY KEY, value TEXT);",
    "CREATE TABLE IF NOT EXISTS emails_sent    (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, email TEXT, subject TEXT);",
    "CREATE TABLE IF NOT EXISTS emails_scanned (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, email TEXT);",
    "CREATE TABLE IF NOT EXISTS credentials    (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, email TEXT, token TEXT);",
    "CREATE TABLE IF NOT EXISTS prt_tokens     (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, email TEXT, prt TEXT, session_key TEXT);",
]


def migrate():
    db = get_db()
    for query in MIGRATIONS:
        db.execute(query)
    db.commit()
    logger.info("Database migrations complete")
