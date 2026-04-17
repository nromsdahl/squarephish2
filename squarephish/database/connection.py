import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_FILE = "./squarephish.db"

_db = None


def connect():
    global _db
    _db = sqlite3.connect(DB_FILE, check_same_thread=False)
    _db.execute("SELECT 1")  # ping
    logger.info("Connected to database: %s", DB_FILE)


def get_db():
    return _db


def close():
    global _db
    if _db is not None:
        _db.close()
        _db = None
        logger.info("Database connection closed")
