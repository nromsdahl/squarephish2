# ------------------------------------------------------------------------
# https://github.com/denniskniep/DeviceCodePhishing
# https://github.com/denniskniep/DeviceCodePhishing/blob/main/LICENSE
#
# Copyright 2025 Dennis Kniep
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------

import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..models import DeviceCodeResponse, RequestConfig

logger = logging.getLogger(__name__)


def enter_device_code_with_headless_browser(
    device_code: DeviceCodeResponse,
    request_config: RequestConfig,
) -> str:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"--user-agent={request_config.user_agent}")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(device_code.verification_uri)

        # Wait for submit button and enter user code
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#idSIButton9")))
        otc_input = driver.find_element(By.CSS_SELECTOR, "#otc")
        otc_input.send_keys(device_code.user_code)
        driver.find_element(By.CSS_SELECTOR, "#idSIButton9").click()

        # Wait for "Can't access your account?" link
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#cantAccessAccount")))
        driver.find_element(By.CSS_SELECTOR, "#cantAccessAccount").click()

        # Wait for either aadTitleHint or cancel button
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "#aadTitleHint, #ContentPlaceholderMainContent_ButtonCancel")
            )
        )

        # Click aadTitleHint if present
        aad_hints = driver.find_elements(By.CSS_SELECTOR, "#aadTitleHint")
        if aad_hints:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#aadTitleHint")))
            driver.find_element(By.CSS_SELECTOR, "#aadTitleHint").click()

        # Click cancel button
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "#ContentPlaceholderMainContent_ButtonCancel")
            )
        )
        driver.find_element(By.CSS_SELECTOR, "#ContentPlaceholderMainContent_ButtonCancel").click()

        # Wait for page to load after cancel
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#cantAccessAccount")))

        return driver.current_url

    finally:
        driver.quit()
