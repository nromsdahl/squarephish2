import logging

from flask import Blueprint, render_template

from ...database import load_dashboard_data, clear_stats, clear_credentials, clear_prts

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
def dashboard_handler():
    data = load_dashboard_data()
    return render_template(
        "dashboard.html",
        emails_sent=data.emails_sent,
        emails_scanned=data.emails_scanned,
        credentials=data.credentials,
        prt_results=data.prt_results,
        active_page=data.active_page,
        title=data.title,
    )


@dashboard_bp.route("/clear/stats", methods=["POST"])
def clear_stats_handler():
    try:
        clear_stats()
        return "Stats cleared", 200
    except Exception as e:
        logger.error("Failed to clear stats: %s", e)
        return "Failed to clear stats", 500


@dashboard_bp.route("/clear/credentials", methods=["POST"])
def clear_credentials_handler():
    try:
        clear_credentials()
        return "Credentials cleared", 200
    except Exception as e:
        logger.error("Failed to clear credentials: %s", e)
        return "Failed to clear credentials", 500


@dashboard_bp.route("/clear/prts", methods=["POST"])
def clear_prts_handler():
    try:
        clear_prts()
        return "PRT tokens cleared", 200
    except Exception as e:
        logger.error("Failed to clear PRT tokens: %s", e)
        return "Failed to clear PRT tokens", 500
