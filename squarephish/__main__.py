import argparse
import logging
import os
import ssl
import sys
import threading

logger = logging.getLogger()


def main():
    # Read version
    try:
        with open("VERSION", "r") as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = "unknown"

    parser = argparse.ArgumentParser(description="SquarePhish2")
    parser.add_argument(
        "-c", "--config", default="config.json", help="Path to the config file"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--version", action="version", version=version
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Suppress Flask/Werkzeug default request logging unless verbose
    if not args.verbose:
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    from .config import load_server_config
    from .database import initialize, close
    from .dashboard.app import create_app
    from .server.server import app as phish_app

    server_config = load_server_config(args.config)

    # Initialize database
    initialize()

    # Start phish server in background thread
    phish_conf = server_config.phish
    phish_host, phish_port = phish_conf.listen_url.rsplit(":", 1)
    phish_port = int(phish_port)

    phish_ssl_context = None
    if phish_conf.use_tls:
        phish_ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        phish_ssl_context.load_cert_chain(phish_conf.cert_path, phish_conf.key_path)

    phish_thread = threading.Thread(
        target=lambda: phish_app.run(
            host=phish_host,
            port=phish_port,
            ssl_context=phish_ssl_context,
            use_reloader=False,
        ),
        daemon=True,
    )
    phish_thread.start()
    logger.info("Phish server started on %s", phish_conf.listen_url)

    # Start dashboard on main thread
    dash_conf = server_config.dashboard
    dash_host, dash_port = dash_conf.listen_url.rsplit(":", 1)
    dash_port = int(dash_port)

    dash_ssl_context = None
    if dash_conf.use_tls:
        dash_ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        dash_ssl_context.load_cert_chain(dash_conf.cert_path, dash_conf.key_path)

    dashboard_app = create_app()

    try:
        logger.info("Dashboard server started on %s", dash_conf.listen_url)
        dashboard_app.run(
            host=dash_host,
            port=dash_port,
            ssl_context=dash_ssl_context,
            use_reloader=False,
        )
    finally:
        close()


if __name__ == "__main__":
    main()
