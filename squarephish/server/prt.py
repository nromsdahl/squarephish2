import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

try:
    from roadtools.roadlib.auth import Authentication  # type: ignore
    from roadtools.roadlib.deviceauth import DeviceAuthentication  # type: ignore

    ROADTOOLS_AVAILABLE = True
except ModuleNotFoundError:
    ROADTOOLS_AVAILABLE = False

# fmt: off
CLIENT_ID    = "29d9ed98-a469-4536-ade2-f981bc1d605e"
RESOURCE_DRS = "urn:ms-drs:enterpriseregistration.windows.net"
USER_AGENT   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
# fmt: on


def generate_prt(refresh_token: str, output_file: str = "prt.txt") -> dict | None:
    """Convert a refresh token into a Primary Refresh Token via ROADtools.

    Returns the full prtdata dict on success, None on failure.
    Saves the PRT file using ROADtools' native saveprt format.
    """
    if not ROADTOOLS_AVAILABLE:
        logger.warning("roadtools not available, skipping PRT generation")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        crt_file = os.path.join(tmpdir, "device.pem")
        key_file = os.path.join(tmpdir, "device.key")

        # Step 1: Swap refresh token to the DRS resource
        logger.info("Swapping refresh token to DRS resource URI")
        auth = Authentication()
        auth.refresh_token = refresh_token
        auth.set_client_id(CLIENT_ID)
        auth.set_resource_uri(RESOURCE_DRS)
        auth.set_user_agent(USER_AGENT)

        res = auth.get_tokens(args=None)
        if not res:
            logger.error("Failed to swap refresh token to DRS resource")
            return None

        auth.access_token = res["accessToken"]
        auth.refresh_token = res["refreshToken"]
        time.sleep(5)

        # Step 2: Join a new device
        logger.info("Joining device for PRT generation")
        deviceauth = DeviceAuthentication(auth)
        deviceauth.register_device(
            access_token=auth.access_token,
            jointype=0,
            certout=crt_file,
            privout=key_file,
            device_type="Windows",
            device_name=None,
            os_version=None,
            deviceticket=None,
        )
        time.sleep(5)

        try:
            # Step 3: Request PRT with the newly joined device
            if not deviceauth.loadcert(crt_file, key_file, None, None, None):
                logger.error("Invalid device certificate and key files")
                return None

            prtdata = deviceauth.get_prt_with_refresh_token(auth.refresh_token)
            if not prtdata:
                logger.error("Failed to retrieve PRT")
                return None

            logger.info("Successfully obtained PRT")
            deviceauth.saveprt(prtdata, output_file)
            return prtdata
        finally:
            # Step 4: Clean up the joined device
            logger.info("Cleaning up device join")
            try:
                deviceauth.delete_device(crt_file, key_file)
            except Exception as e:
                logger.warning("Failed to clean up device: %s", e)
