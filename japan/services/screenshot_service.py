import io
import re
from datetime import datetime
from pathlib import Path

from japan import config

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is optional at import time
    Image = None


_UNSAFE_FILENAME = re.compile(r"[^0-9A-Za-z._-]+")


def _safe_name(drug_id):
    name = _UNSAFE_FILENAME.sub("_", str(drug_id).strip())
    return name or "unknown"


def _target_path(drug_id, when=None, base_dir=None):
    when = when or datetime.now()
    base_dir = Path(base_dir) if base_dir else config.SCREENSHOTS_DIR
    month_dir = base_dir / when.strftime("%Y") / when.strftime("%m")
    return month_dir / f"{_safe_name(drug_id)}.png"


def capture_product_screenshot(page, drug_id, logger=None, base_dir=None):
    """Save a 720px-wide screenshot of the current page under screenshots/YYYY/MM/.

    Screenshots are a side artifact, so any failure here is logged and swallowed
    rather than allowed to break the validation run. Returns the saved Path or None.
    """
    if not config.ENABLE_SCREENSHOTS:
        return None

    try:
        path = _target_path(drug_id, base_dir=base_dir)
        path.parent.mkdir(parents=True, exist_ok=True)

        image_bytes = page.screenshot(full_page=True)

        if Image is None:
            # Pillow unavailable: save the full-size capture as-is.
            path.write_bytes(image_bytes)
            if logger:
                logger.warning(
                    "Pillow not installed; saved full-size screenshot for %s", drug_id
                )
            return path

        _resize_to_width(image_bytes, config.SCREENSHOT_WIDTH).save(path, format="PNG")
        if logger:
            logger.info("Screenshot saved: %s", path)
        return path

    except Exception as error:
        if logger:
            logger.warning("Screenshot failed for %s: %s", drug_id, error)
        return None


def _resize_to_width(image_bytes, width):
    image = Image.open(io.BytesIO(image_bytes))
    if image.width <= width:
        return image
    height = round(image.height * width / image.width)
    return image.resize((width, height), Image.LANCZOS)
