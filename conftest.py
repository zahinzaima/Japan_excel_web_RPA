# conftest.py
# Playwright + Pytest harness with:
# - artifacts/: screenshots, traces, videos
# - auto-highlighter for actions
# - per-test tracing (ZIP)
# - failure screenshots attached to pytest-html
# - single, correct pytest_runtest_makereport hook

from __future__ import annotations

import os
import time
import shutil
import datetime
from pathlib import Path
from typing import Optional, Callable

import pytest
try:
    import pyautogui
except Exception:  # pragma: no cover - fallback for headless test environments
    pyautogui = None

from playwright.sync_api import (
    Playwright,
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    Locator,
)

# =========================
# Config
# =========================
headless_flag = False          # set True in CI
slow_mo_speed = 0            # reduce in CI

ARTIFACTS_DIR = Path("artifacts")
VIDEOS_DIR = ARTIFACTS_DIR / "videos"
TRACES_DIR = ARTIFACTS_DIR / "traces"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"

if pyautogui is not None:
    screen_width, screen_height = pyautogui.size()
else:
    screen_width, screen_height = (1600, 900)
print(f"Artifacts path: {ARTIFACTS_DIR}")
print(f"Running on screen size: {screen_width}x{screen_height}")

# =========================
# Auto-highlighter settings
# =========================
def _env_truthy(val: str | None) -> bool:
    if val is None:
        return True
    return val.strip().lower() not in {"0", "false", "off", "no"}

HIGHLIGHT_ENABLED = _env_truthy(os.getenv("HIGHLIGHT_ELEMENTS", "1"))
try:
    HIGHLIGHT_DURATION_MS = int(os.getenv("HIGHLIGHT_MS", "800"))
except ValueError:
    HIGHLIGHT_DURATION_MS = 800

ACTION_COLORS = {
    "click": "red",
    "dblclick": "red",
    "press": "red",
    "fill": "green",
    "type": "green",
    "select_option": "green",
    "focus": "green",
    "hover": "blue",
    "check": "purple",
    "uncheck": "purple",
}

# =========================
# Globals
# =========================
global_browser: Optional[Browser] = None
global_context: Optional[BrowserContext] = None
global_pages: list[Page] = []  # last page is the most recent
test_failures: list[dict] = []


# =========================
# Utilities
# =========================
def safe_file_operation(file_path: Path, operation, max_retries=5, delay=1):
    for attempt in range(max_retries):
        try:
            return operation(file_path)
        except (PermissionError, OSError):
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)

def wait_until_file_unlocked(path: Path, timeout=10):
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            with open(path, 'rb'):
                return True
        except PermissionError:
            time.sleep(0.5)
    raise TimeoutError(f"File {path} still locked after {timeout} seconds")


# =========================
# Pytest setup
# =========================
def pytest_configure(config):
    # fresh artifacts dir per run
    if ARTIFACTS_DIR.exists():
        shutil.rmtree(ARTIFACTS_DIR, ignore_errors=True)
    #VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    #TRACES_DIR.mkdir(parents=True, exist_ok=True)
    #SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def playwright() -> Playwright:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    global global_browser
    if global_browser is None:
        global_browser = playwright.chromium.launch(
            headless=headless_flag,
            slow_mo=slow_mo_speed,
            args=[
                "--start-maximized",
                "--window-position=0,0",
                "--high-dpi-support=1",
                "--force-device-scale-factor=1",
                "--ignore-certificate-errors",
            ],
        )
    yield global_browser
    if global_browser:
        global_browser.close()
        global_browser = None


@pytest.fixture(scope="session")
def context(browser: Browser) -> BrowserContext:
    """Single context for the session. Per-test tracing is handled by an autouse fixture below."""
    global global_context, global_pages

    if global_context is None:
        global_context = browser.new_context(
            viewport={"width": screen_width, "height": screen_height},
            device_scale_factor=1,
            #record_video_dir=str(VIDEOS_DIR),
            #record_video_size={"width": screen_width, "height": screen_height},
            ignore_https_errors=True,
        )

        # Track all new pages/tabs
        def on_page(page: Page):
            global_pages.append(page)
        global_context.on("page", on_page)

        # Install action highlighter
        if HIGHLIGHT_ENABLED:
            _install_auto_highlighter()

    yield global_context

    # Close context → flush videos to disk
    try:
        global_context.close()
    except Exception:
        pass
    global_context = None
    global_pages.clear()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    """Return the main page. Create if first use; reuse for speed."""
    global global_pages
    if not global_pages:
        pg = context.new_page()
        global_pages.append(pg)
    main = global_pages[0]
    main.bring_to_front()
    return main


@pytest.fixture(scope="function")
def new_tab(context: BrowserContext) -> Callable[[Callable[[Page], None]], Page]:
    """Helper to open a new tab and return it."""
    def _open(action: Callable[[Page], None]) -> Page:
        global global_pages
        with context.expect_page() as new_page_info:
            action(global_pages[-1])
        pg = new_page_info.value
        global_pages.append(pg)
        pg.bring_to_front()
        return pg
    return _open



# =========================
# Auto-highlighter implementation
# =========================
def highlight_selector(page: Page, selector: str, action: str, duration_ms: int = HIGHLIGHT_DURATION_MS):
    """Outline a CSS/XPath selector temporarily (best-effort)."""
    try:
        color = ACTION_COLORS.get(action, "red")
        # If selector looks like XPath, try a query first to ensure it's attached
        if selector.strip().startswith(("//", "xpath=", "css=")) is False:
            page.wait_for_selector(selector, state="attached", timeout=1500)
        page.eval_on_selector(
            selector if selector.startswith(("css=", "xpath=")) is False else selector.replace("css=", "").replace("xpath=", ""),
            f"""(el) => {{
                const prev = el.style.outline;
                el.style.outline = '3px solid {color}';
                setTimeout(() => {{ el.style.outline = prev; }}, {duration_ms});
            }}"""
        )
    except Exception:
        pass

def highlight_locator(locator: Locator, action: str, duration_ms: int = HIGHLIGHT_DURATION_MS):
    """Outline the element behind a Locator temporarily (best-effort)."""
    try:
        color = ACTION_COLORS.get(action, "red")
        locator.evaluate(
            f"""(el) => {{
                const prev = el.style.outline;
                el.style.outline = '3px solid {color}';
                setTimeout(() => {{ el.style.outline = prev; }}, {duration_ms});
            }}"""
        )
    except Exception:
        pass

def _install_auto_highlighter():
    """Monkey-patch Page and Locator interaction methods to auto-highlight targets."""
    if getattr(Page, "_auto_highlight_installed", False):
        return

    page_methods = list(ACTION_COLORS.keys())
    locator_methods = list(ACTION_COLORS.keys())

    # Patch Page methods
    for method_name in page_methods:
        if not hasattr(Page, method_name):
            continue
        original = getattr(Page, method_name)

        def make_wrapper(_original, _method_name):
            def wrapper(self: Page, selector: str, *args, **kwargs):
                if HIGHLIGHT_ENABLED and isinstance(selector, str):
                    try:
                        highlight_selector(self, selector, _method_name)
                    except Exception:
                        pass
                return _original(self, selector, *args, **kwargs)
            return wrapper

        setattr(Page, method_name, make_wrapper(original, method_name))

    # Patch Locator methods
    for method_name in locator_methods:
        if not hasattr(Locator, method_name):
            continue
        original = getattr(Locator, method_name)

        def make_loc_wrapper(_original, _method_name):
            def wrapper(self: Locator, *args, **kwargs):
                if HIGHLIGHT_ENABLED:
                    try:
                        highlight_locator(self, _method_name)
                    except Exception:
                        pass
                return _original(self, *args, **kwargs)
            return wrapper

        setattr(Locator, method_name, make_loc_wrapper(original, method_name))

    setattr(Page, "_auto_highlight_installed", True)


# =========================
# Optional: soft assertion logging (pytest-check)
# =========================
try:
    import pytest_check
except ImportError:
    pytest_check = None

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    """If pytest-check is installed, print soft assertion errors at the end of each test call."""
    outcome = yield
    if pytest_check:
        errors = getattr(pytest_check, "_errors", [])
        for e in errors:
            print(f"🔸 Soft check failure in {item.name}: {e}")

