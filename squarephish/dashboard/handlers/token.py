import json
import logging

from flask import Blueprint, request

from ...database import load_token

logger = logging.getLogger(__name__)

token_bp = Blueprint("token", __name__)


@token_bp.route("/token", methods=["GET"])
def token_handler():
    email = request.args.get("email", "")
    if not email:
        return "No email provided", 500

    try:
        token = load_token(email)
        pretty = json.dumps(json.loads(token), indent=2)
        return pretty, 200, {"Content-Type": "application/json"}
    except Exception as e:
        logger.error("Failed to retrieve token: %s", e)
        return "Failed to retrieve token", 500
