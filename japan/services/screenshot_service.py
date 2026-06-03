import io
import re
from pathlib import Path

from japan import config

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is optional at import time
    Image = None


# Characters that are unsafe in a path segment. Kept deliberately permissive so
# the descriptive "Medicine=[...]_Company=[...]" filename stays human-readable,
# matching the naming used by the other country RPA pipelines.
_INVALID_FS_CHARS = re.compile(r'[/\\:*?"<>|\r\n\t]+')


def _safe_segment(value, fallback="UNKNOWN", max_len=120):
    text = _INVALID_FS_CHARS.sub("_", str(value or "").strip())
    text = re.sub(r"\s+", " ", text).strip()
    text = text[:max_len].strip()
    return text or fallback


def build_screenshot_path(drug_id, brand, company, base_dir):
    """Return the local path for a product screenshot.

    Layout (relative to ``base_dir``):
        <DRUG_ID>/Medicine=[<brand>]_Company=[<company>].png

    ``DRUG_ID`` groups every screenshot captured for a single YJ code, and the
    filename records the brand and company found on the website.
    """
    group = _safe_segment(drug_id)
    medicine = _safe_segment(brand, fallback=group)
    company_name = _safe_segment(company, fallback="UNKNOWN")
    filename = _safe_segment(f"Medicine=[{medicine}]_Company=[{company_name}]") + ".png"
    return Path(base_dir) / group / filename


def capture_product_screenshot(page, drug_id, brand, company, base_dir, logger=None):
    """Save a 720px-wide screenshot of the current product page.

    Screenshots are a side artifact, so any failure here is logged and swallowed
    rather than allowed to break the validation run. Returns the saved Path or None.
    """
    if not config.ENABLE_SCREENSHOTS:
        return None

    try:
        path = build_screenshot_path(drug_id, brand, company, base_dir)
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
