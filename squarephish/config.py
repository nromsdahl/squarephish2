import json
import os
from dataclasses import dataclass


@dataclass
class DashboardServer:
    listen_url: str = "127.0.0.1:8080"
    cert_path: str = ""
    key_path: str = ""
    use_tls: bool = False


@dataclass
class PhishServer:
    listen_url: str = "0.0.0.0:8443"
    cert_path: str = ""
    key_path: str = ""
    use_tls: bool = False


@dataclass
class ServerConfig:
    dashboard: DashboardServer
    phish: PhishServer


def load_server_config(path: str) -> ServerConfig:
    path = os.path.normpath(path)
    with open(path, "r") as f:
        data = json.load(f)

    dash = data.get("dashboard_server", {})
    phish = data.get("phish_server", {})

    return ServerConfig(
        dashboard=DashboardServer(
            listen_url=dash.get("listen_url", "127.0.0.1:8080"),
            cert_path=dash.get("cert_path", ""),
            key_path=dash.get("key_path", ""),
            use_tls=dash.get("use_tls", False),
        ),
        phish=PhishServer(
            listen_url=phish.get("listen_url", "0.0.0.0:8443"),
            cert_path=phish.get("cert_path", ""),
            key_path=phish.get("key_path", ""),
            use_tls=phish.get("use_tls", False),
        ),
    )
