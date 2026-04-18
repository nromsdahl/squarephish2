import logging
import os

from flask import Flask, request

from .handlers.dashboard import dashboard_bp
from .handlers.config import config_bp
from .handlers.email import email_bp
from .handlers.token import token_bp
from .handlers.prt import prt_bp

logger = logging.getLogger(__name__)

# Resolve template and static dirs relative to project root (cwd)
TEMPLATE_DIR = os.path.join(os.getcwd(), "templates")
STATIC_DIR = os.path.join(os.getcwd(), "static")


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=TEMPLATE_DIR,
        static_folder=STATIC_DIR,
        static_url_path="/static",
    )

    @app.before_request
    def log_request():
        logger.debug("Dashboard request: %s %s", request.method, request.path)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(token_bp)
    app.register_blueprint(prt_bp)

    return app
