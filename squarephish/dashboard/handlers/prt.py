import json
import logging
import os

from flask import Blueprint, request, send_file

from ...database import load_prt

logger = logging.getLogger(__name__)

prt_bp = Blueprint("prt", __name__)


@prt_bp.route("/prt", methods=["GET"])
def prt_handler():
    email = request.args.get("email", "")
    if not email:
        return "No email provided", 500

    try:
        result = load_prt(email)
        data = {
            "email": result.email,
            "prt": result.prt,
            "session_key": result.session_key,
        }
        return json.dumps(data, indent=2), 200, {"Content-Type": "application/json"}
    except Exception as e:
        logger.error("Failed to retrieve PRT: %s", e)
        return "Failed to retrieve PRT", 500


@prt_bp.route("/prt/download", methods=["GET"])
def prt_download_handler():
    email = request.args.get("email", "")
    if not email:
        return "No email provided", 400

    safe_email = email.replace("@", "_at_").replace(".", "_")
    filename = f"prt_{safe_email}.txt"

    if not os.path.isfile(filename):
        return "PRT file not found", 404

    return send_file(
        os.path.abspath(filename),
        as_attachment=True,
        download_name=filename,
    )
