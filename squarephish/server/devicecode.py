import logging
import urllib3

import requests

from ..models import DeviceCodeResponse, EntraConfig, RequestConfig

logger = logging.getLogger(__name__)

# Suppress InsecureRequestWarning for verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def init_device_code(
    email: str,
    entra_config: EntraConfig,
    request_config: RequestConfig,
) -> DeviceCodeResponse:
    device_code_url = (
        f"https://login.microsoftonline.com/{entra_config.tenant}/oauth2/v2.0/deviceCode"
    )

    data = {
        "client_id": entra_config.client_id,
        "scope": entra_config.scope,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": request_config.user_agent,
    }

    logger.info("[%s] Initializing device code flow...", email)
    logger.info("[%s]     Client ID: %s", email, entra_config.client_id)
    logger.info("[%s]     Scope:     %s", email, entra_config.scope)

    resp = requests.post(
        device_code_url,
        data=data,
        headers=headers,
        verify=False,
        timeout=15,
    )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Received non-success status code {resp.status_code}"
        )

    result = resp.json()
    return DeviceCodeResponse(
        user_code=result.get("user_code", ""),
        device_code=result.get("device_code", ""),
        verification_uri=result.get("verification_uri", ""),
        expires_in=result.get("expires_in", 0),
        interval=result.get("interval", 0),
        message=result.get("message", ""),
    )
