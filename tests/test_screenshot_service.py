import logging

from japan.services import screenshot_service


class FakePage:
    def __init__(self, data=b"img"):
        self._data = data

    def screenshot(self, full_page=False):
        return self._data


def make_logger():
    logger = logging.getLogger("screenshot-test")
    logger.handlers.clear()
    logger.propagate = False
    logger.addHandler(logging.NullHandler())
    return logger


def test_build_screenshot_path_groups_by_drug_id_and_names_by_brand_company(tmp_path):
    path = screenshot_service.build_screenshot_path(
        drug_id="1234567",
        brand="Kisqali tablet 200mg",
        company="NOVARTIS PHARMA",
        base_dir=tmp_path,
    )

    assert path.parent.name == "1234567"
    assert path.name == "Medicine=[Kisqali tablet 200mg]_Company=[NOVARTIS PHARMA].png"
    assert path.parent.parent == tmp_path


def test_build_screenshot_path_sanitizes_slashes_and_falls_back(tmp_path):
    path = screenshot_service.build_screenshot_path(
        drug_id="11/22",
        brand="",
        company=None,
        base_dir=tmp_path,
    )

    # Group folder sanitized; brand falls back to the drug id, company to UNKNOWN.
    assert path.parent.name == "11_22"
    assert path.name == "Medicine=[11_22]_Company=[UNKNOWN].png"


def test_capture_writes_png_under_expected_path(tmp_path, monkeypatch):
    monkeypatch.setattr(screenshot_service.config, "ENABLE_SCREENSHOTS", True)
    # Force the Pillow-free branch so the raw bytes are written as-is.
    monkeypatch.setattr(screenshot_service, "Image", None)

    saved = screenshot_service.capture_product_screenshot(
        FakePage(b"PNGDATA"),
        drug_id="9999",
        brand="Brand EN",
        company="ACME",
        base_dir=tmp_path,
        logger=make_logger(),
    )

    assert saved is not None
    assert saved.read_bytes() == b"PNGDATA"
    assert saved == tmp_path / "9999" / "Medicine=[Brand EN]_Company=[ACME].png"


def test_capture_swallows_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(screenshot_service.config, "ENABLE_SCREENSHOTS", True)

    class BrokenPage:
        def screenshot(self, full_page=False):
            raise RuntimeError("page closed")

    saved = screenshot_service.capture_product_screenshot(
        BrokenPage(),
        drug_id="9999",
        brand="Brand",
        company="ACME",
        base_dir=tmp_path,
        logger=make_logger(),
    )

    assert saved is None
