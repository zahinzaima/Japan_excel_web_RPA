from contextlib import contextmanager

from playwright.sync_api import sync_playwright

from japan import config


@contextmanager
def runtime_page(headless=True, slow_mo=0):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=[
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.set_default_timeout(config.DEFAULT_TIMEOUT)
        page.set_default_navigation_timeout(config.NAVIGATION_TIMEOUT)

        try:
            yield page
        finally:
            context.close()
            browser.close()
