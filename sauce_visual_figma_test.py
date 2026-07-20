#!/usr/bin/env python3
"""
Sauce Labs Visual snapshot test with a Figma design as the baseline.

Flow:
  1. Start a Selenium session on Sauce Labs (RemoteWebDriver).
  2. Log in to the target portal.
  3. Take a Sauce Visual snapshot of the Home Page.
  4. Match that snapshot against a Figma-exported baseline using the
     "Baseline Override" feature.

Docs used:
  - Python integration:  https://docs.saucelabs.com/visual-testing/integrations/python/
  - Figma integration:   https://docs.saucelabs.com/visual-testing/integrations/figma/
  - Baseline overrides:  https://docs.saucelabs.com/visual-testing/workflows/cross-browser-os/#3-configure-baseline-overrides

Prereqs:
    pip install saucelabs_visual selenium

Required environment variables (from https://app.saucelabs.com/user-settings):
    SAUCE_USERNAME     - your Sauce Labs username
    SAUCE_ACCESS_KEY   - your Sauce Labs access key
    SAUCE_REGION       - us-west-1 (default) | us-east-4 | eu-central-1
                         Must be the SAME region the Figma design was exported to.

The saucelabs_visual client reads SAUCE_USERNAME / SAUCE_ACCESS_KEY / SAUCE_REGION
automatically. We pass the same region to the Selenium ondemand endpoint below.
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from saucelabs_visual.client import SauceLabsVisual
from saucelabs_visual.typing import BaselineOverride

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# --- Target application ---
APP_URL = "https://sportal-npd.ct-costco.com/"
APP_USERNAME = "genericQAacct_1"
APP_PASSWORD = "water_Saver-vend!06.26"

# Seconds to pause after login so the Home Page images finish loading
# before the visual snapshot is taken.
POST_LOGIN_WAIT_SECONDS = 5

# --- Sauce Labs region -> ondemand endpoint (keep in sync with SAUCE_REGION) ---
SAUCE_REGION = os.environ.get("SAUCE_REGION", "us-west-1")
_ONDEMAND = {
    "us-west-1": "https://ondemand.us-west-1.saucelabs.com/wd/hub",
    "us-east-4": "https://ondemand.us-east-4.saucelabs.com/wd/hub",
    "eu-central-1": "https://ondemand.eu-central-1.saucelabs.com/wd/hub",
}
SAUCE_URL = _ONDEMAND[SAUCE_REGION]
SAUCE_USERNAME = os.environ["SAUCE_USERNAME"]
SAUCE_ACCESS_KEY = os.environ["SAUCE_ACCESS_KEY"]

# --------------------------------------------------------------------------- #
# Figma baseline metadata (from the Figma plugin export)
#
#   {
#     "name": "Home Page",
#     "testName": "SVP-POC",
#     "suiteName": "SVP-homePage",
#     "browser": "FIGMA",
#     "operatingSystem": "UNKNOWN",
#     "operatingSystemVersion": null,
#     "branch": "Demo",
#     "device": null
#   }
#
# NOTE: The saucelabs_visual SDK's Browser / OperatingSystem enums do NOT expose
# FIGMA or UNKNOWN. Those enums subclass `str` and the values are passed straight
# through to the Sauce Visual GraphQL API, which DOES accept these Figma values.
# So we pass the raw strings "FIGMA" / "UNKNOWN" here.
# --------------------------------------------------------------------------- #
SNAPSHOT_NAME = "Home Page"
TEST_NAME = "SVP-POC"
SUITE_NAME = "SVP-homePage"
BUILD_BRANCH = "Demo"  # must match the branch the Figma design was exported under
Project = "Sustainability Vendor Portal"

FIGMA_BASELINE_OVERRIDE = BaselineOverride(
    browser="FIGMA",                 # server enum value (not in SDK enum)
    operatingSystem="UNKNOWN",       # server enum value (not in SDK enum)
    operatingSystemVersion=None,     # Figma export has null -> match null
    device=None,                     # Figma export has null -> match null
)

# --------------------------------------------------------------------------- #
# Selenium capabilities (browser under test on Sauce)
# --------------------------------------------------------------------------- #
def build_driver() -> webdriver.Remote:
    options = webdriver.ChromeOptions()
    options.browser_version = "latest"
    options.platform_name = "Windows 11"
    options.set_capability(
        "sauce:options",
        {
            "username": SAUCE_USERNAME,
            "accessKey": SAUCE_ACCESS_KEY,
            "build": "SVP-POC Figma Baseline",
            "name": f"{SUITE_NAME} - {SNAPSHOT_NAME}",
        },
    )
    return webdriver.Remote(command_executor=SAUCE_URL, options=options)


# --------------------------------------------------------------------------- #
# Login
#
# This is a JavaScript (React) app, so:
#   - we only interact with VISIBLE + ENABLED fields (avoids the
#     "element not interactable" error from matching a hidden duplicate), and
#   - we submit by pressing ENTER in the password field instead of hunting for
#     a submit button (most robust for React forms).
#
# The password field is CSS type='password' which is reliable. The username
# field selector is a best guess; adjust if needed. Set DEBUG_DUMP=1 to print
# every input/button on the page (see dump_form_elements()).
# --------------------------------------------------------------------------- #
# PingFederate SSO login page. The username field is typically name="pf.username";
# the "Sign In" control is <a id="signOnButton" onclick="postOk();"> (an anchor,
# not a real submit button), so we click it by id with a JS fallback.
LOGIN_USERNAME_SELECTOR = (
    By.CSS_SELECTOR,
    "input[name='pf.username'], input[name='username'], input[id*='user' i], input[type='email'], input[type='text']",
)
LOGIN_PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[type='password']")
LOGIN_SUBMIT_SELECTOR = (By.ID, "signOnButton")


def _first_interactable(driver, locator):
    """Return the first displayed + enabled element for a locator, else None."""
    for el in driver.find_elements(*locator):
        try:
            if el.is_displayed() and el.is_enabled():
                return el
        except Exception:
            continue
    return None


def dump_form_elements(driver) -> None:
    """Print all inputs and buttons with their key attributes (for debugging)."""
    js = """
    const out = [];
    for (const el of document.querySelectorAll('input, button, a[role=button]')) {
      const r = el.getBoundingClientRect();
      out.push({
        tag: el.tagName, type: el.type || '', id: el.id || '',
        name: el.getAttribute('name') || '', placeholder: el.placeholder || '',
        text: (el.innerText || el.value || '').trim().slice(0, 40),
        visible: !!(r.width && r.height),
      });
    }
    return JSON.stringify(out, null, 2);
    """
    print("---- FORM ELEMENTS ON PAGE ----")
    print(driver.execute_script(js))
    print("--------------------------------")


def login(driver: webdriver.Remote) -> None:
    wait = WebDriverWait(driver, 30)
    driver.get(APP_URL)

    # Wait for the password field to render (reliable signal the login form is up).
    wait.until(EC.presence_of_element_located(LOGIN_PASSWORD_SELECTOR))

    if os.environ.get("DEBUG_DUMP") == "1":
        dump_form_elements(driver)

    username = _first_interactable(driver, LOGIN_USERNAME_SELECTOR)
    password = _first_interactable(driver, LOGIN_PASSWORD_SELECTOR)
    if username is None or password is None:
        dump_form_elements(driver)
        raise RuntimeError(
            "Could not find a visible username/password field. "
            "See the dump above and update LOGIN_USERNAME_SELECTOR / LOGIN_PASSWORD_SELECTOR."
        )

    username.click()
    username.send_keys(APP_USERNAME)
    password.click()
    password.send_keys(APP_PASSWORD)

    # The "Sign In" control is <a id="signOnButton" onclick="postOk();">.
    # Prefer a real click; fall back to a JS click (works reliably for anchors).
    submit = _first_interactable(driver, LOGIN_SUBMIT_SELECTOR)
    if submit is not None:
        try:
            submit.click()
        except Exception:
            driver.execute_script("arguments[0].click();", submit)
    else:
        # Last resort: call the page's own submit handler, or press ENTER.
        try:
            driver.execute_script("if (typeof postOk === 'function') { postOk(); }")
        except Exception:
            password.send_keys(Keys.RETURN)

    # Wait until the login form is gone (i.e. we've navigated past it).
    wait.until(EC.staleness_of(password))
    # Give the Home Page time to finish loading images before snapshotting.
    time.sleep(POST_LOGIN_WAIT_SECONDS)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    client = SauceLabsVisual()  # reads SAUCE_USERNAME / SAUCE_ACCESS_KEY / SAUCE_REGION

    # Build associated with all snapshots. Branch must match the Figma export.
    client.create_build(name="SVP-POC", project=PROJECT, branch=BUILD_BRANCH)

    driver = build_driver()
    try:
        login(driver)

        client.create_snapshot_from_webdriver(
            name=SNAPSHOT_NAME,
            driver=driver,
            test_name=TEST_NAME,
            suite_name=SUITE_NAME,
            baseline_override=FIGMA_BASELINE_OVERRIDE,
        )
    finally:
        driver.quit()
        client.finish_build()


if __name__ == "__main__":
    main()
