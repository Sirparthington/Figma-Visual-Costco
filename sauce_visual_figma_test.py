#!/usr/bin/env python3
"""
Sauce Labs Visual snapshot test with a Figma design as the baseline.
Flow:
  1. Start a Selenium session on Sauce Labs (RemoteWebDriver).
  2. Log in to the target portal.
  3. Take a Sauce Visual snapshot of the Home Page.
  4. Match that snapshot against a Figma-exported baseline using the
     "Baseline Override" feature.
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from saucelabs_visual.client import SauceLabsVisual
from saucelabs_visual.typing import (
    BaselineOverride,
    DiffingMethod,
    DiffingMethodSensitivity,
    DiffingMethodTolerance,
)

# --- Target application ---
APP_URL = "https://sportal-npd.ct-costco.com/"
APP_USERNAME = "genericQAacct_1"
APP_PASSWORD = "water_Saver-vend!06.26"
POST_LOGIN_WAIT_SECONDS = 5

SAUCE_REGION = os.environ.get("SAUCE_REGION", "us-west-1")
_ONDEMAND = {
    "us-west-1": "https://ondemand.us-west-1.saucelabs.com/wd/hub",
    "us-east-4": "https://ondemand.us-east-4.saucelabs.com/wd/hub",
    "eu-central-1": "https://ondemand.eu-central-1.saucelabs.com/wd/hub",
}
SAUCE_URL = _ONDEMAND[SAUCE_REGION]
SAUCE_USERNAME = os.environ["SAUCE_USERNAME"]
SAUCE_ACCESS_KEY = os.environ["SAUCE_ACCESS_KEY"]

SNAPSHOT_NAME = "Home Page"
TEST_NAME = "SVP-POC"
SUITE_NAME = "SVP-homePage"
BUILD_BRANCH = "Demo"  # must match the branch the Figma design was exported under
PROJECT = "Sustainability Vendor Portal"

FIGMA_BASELINE_OVERRIDE = BaselineOverride(
    browser="FIGMA",
    operatingSystem="UNKNOWN",
    operatingSystemVersion=None,
    device=None,
)

# --- Diffing sensitivity -----------------------------------------------------
# When comparing a live browser render against a Figma-exported baseline,
# anti-aliasing, sub-pixel positioning, and tiny color shifts make almost
# everything look "changed". Lowering the sensitivity tells the Balanced engine
# to ignore that rendering noise.
#
# Preset options (least -> most sensitive): LOW, BALANCED, HIGH.
DIFFING_METHOD = DiffingMethod.BALANCED
DIFFING_SENSITIVITY = DiffingMethodSensitivity.LOW

# Optional: fine-grained tolerances. Uncomment and tune if LOW still over-flags.
# Larger numbers = more tolerant (fewer diffs). minChangeSize is in pixels and
# ignores changed clusters smaller than that.
# DIFFING_TOLERANCE = DiffingMethodTolerance(
#     antiAliasing=1.0,
#     brightness=1.0,
#     color=1.0,
#     minChangeSize=4,
# )
DIFFING_TOLERANCE = None
# -----------------------------------------------------------------------------


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
            # VM screen must be >= the target window. 1440x1024 is NOT a valid
            # Sauce screenResolution, so pick a larger supported one to fit it.
            "screenResolution": "2560x1600",
        },
    )
    driver = webdriver.Remote(command_executor=SAUCE_URL, options=options)
    _set_viewport(driver, 1440, 1600)
    return driver


def _set_viewport(driver, width: int, height: int) -> None:
    """Resize the window so the *viewport* (inner) is exactly width x height."""
    driver.set_window_size(width, height)
    outer_w, outer_h = driver.execute_script(
        "return [window.outerWidth  - window.innerWidth  + arguments[0],"
        "        window.outerHeight - window.innerHeight + arguments[1]];",
        width, height,
    )
    driver.set_window_size(outer_w, outer_h)


LOGIN_USERNAME_SELECTOR = (
    By.CSS_SELECTOR,
    "input[name='pf.username'], input[name='username'], input[id*='user' i], input[type='email'], input[type='text']",
)
LOGIN_PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[type='password']")
LOGIN_SUBMIT_SELECTOR = (By.ID, "signOnButton")


def _first_interactable(driver, locator):
    for el in driver.find_elements(*locator):
        try:
            if el.is_displayed() and el.is_enabled():
                return el
        except Exception:
            continue
    return None


def dump_form_elements(driver) -> None:
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
    submit = _first_interactable(driver, LOGIN_SUBMIT_SELECTOR)
    if submit is not None:
        try:
            submit.click()
        except Exception:
            driver.execute_script("arguments[0].click();", submit)
    else:
        try:
            driver.execute_script("if (typeof postOk === 'function') { postOk(); }")
        except Exception:
            password.send_keys(Keys.RETURN)
    wait.until(EC.staleness_of(password))
    time.sleep(POST_LOGIN_WAIT_SECONDS)


def main() -> None:
    client = SauceLabsVisual()
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
            # Lower the diffing sensitivity so rendering noise isn't flagged.
            diffing_method=DIFFING_METHOD,
            diffing_method_sensitivity=DIFFING_SENSITIVITY,
            diffing_method_tolerance=DIFFING_TOLERANCE,
        )
    finally:
        driver.quit()
        client.finish_build()


if __name__ == "__main__":
    main()
