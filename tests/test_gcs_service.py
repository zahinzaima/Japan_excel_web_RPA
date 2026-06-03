import logging

from japan import config
from japan.services import gcs_service


class FakeBlob:
    def __init__(self, name, store):
        self.name = name
        self._store = store

    def upload_from_filename(self, filename):
        self._store[self.name] = filename


class FakeBucket:
    def __init__(self, name, store):
        self.name = name
        self._store = store

    def blob(self, object_name):
        return FakeBlob(object_name, self._store)


class FakeClient:
    def __init__(self, store):
        self._store = store
        self.requested_buckets = []

    def bucket(self, bucket_name):
        self.requested_buckets.append(bucket_name)
        return FakeBucket(bucket_name, self._store)


def make_logger():
    logger = logging.getLogger("gcs-test")
    logger.handlers.clear()
    logger.propagate = False
    logger.addHandler(logging.NullHandler())
    return logger


def create_screenshots(root):
    files = {
        "1111/Medicine=[Brand One EN]_Company=[Company One].png": b"one",
        "2222/Medicine=[Brand Two EN]_Company=[Company Two].png": b"two",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return files


def test_uploads_all_files_with_expected_object_names(tmp_path, monkeypatch):
    screenshots_dir = tmp_path / "abc123"
    create_screenshots(screenshots_dir)

    store = {}
    client = FakeClient(store)

    monkeypatch.setattr(config, "ENABLE_GCS_UPLOAD", True)
    monkeypatch.setattr(config, "GCS_BUCKET_NAME", "app_modernization_v2_dev")
    monkeypatch.setattr(config, "GCS_ROOT_PREFIX", "rpa")
    monkeypatch.setattr(config, "COUNTRY_NAME", "Japan")

    uploaded = gcs_service.upload_screenshots(
        screenshots_dir=screenshots_dir,
        trace_id="abc123",
        year="2026",
        month="06",
        logger=make_logger(),
        client_factory=lambda: client,
    )

    assert uploaded == 2
    assert client.requested_buckets == ["app_modernization_v2_dev"]
    assert set(store) == {
        "rpa/Japan/2026/06/abc123/screenshots/1111/Medicine=[Brand One EN]_Company=[Company One].png",
        "rpa/Japan/2026/06/abc123/screenshots/2222/Medicine=[Brand Two EN]_Company=[Company Two].png",
    }


def test_build_object_name_matches_requested_pattern(monkeypatch):
    monkeypatch.setattr(config, "GCS_ROOT_PREFIX", "rpa")
    monkeypatch.setattr(config, "COUNTRY_NAME", "Japan")

    name = gcs_service.build_object_name(
        "KISQALI/Medicine=[Kisqali tablet 200mg]_Company=[NOVARTIS].png",
        trace_id="trace-xyz",
        year="2026",
        month="06",
    )

    assert name == (
        "rpa/Japan/2026/06/trace-xyz/screenshots/"
        "KISQALI/Medicine=[Kisqali tablet 200mg]_Company=[NOVARTIS].png"
    )


def test_build_console_url_and_gs_uri(monkeypatch):
    monkeypatch.setattr(config, "GCS_ROOT_PREFIX", "rpa")
    monkeypatch.setattr(config, "COUNTRY_NAME", "Japan")
    monkeypatch.setattr(config, "GCS_BUCKET_NAME", "app_modernization_v2_dev")

    rel = "1234567/Medicine=[Brand]_Company=[ACME].png"
    assert gcs_service.build_console_url(rel, "tid", "2026", "06") == (
        "https://storage.cloud.google.com/app_modernization_v2_dev/"
        "rpa/Japan/2026/06/tid/screenshots/1234567/Medicine=[Brand]_Company=[ACME].png"
    )
    assert gcs_service.build_gs_uri(rel, "tid", "2026", "06") == (
        "gs://app_modernization_v2_dev/"
        "rpa/Japan/2026/06/tid/screenshots/1234567/Medicine=[Brand]_Company=[ACME].png"
    )


def test_disabled_upload_is_a_noop(tmp_path, monkeypatch):
    screenshots_dir = tmp_path / "run"
    create_screenshots(screenshots_dir)

    monkeypatch.setattr(config, "ENABLE_GCS_UPLOAD", False)

    def boom():
        raise AssertionError("client factory must not be called when disabled")

    uploaded = gcs_service.upload_screenshots(
        screenshots_dir=screenshots_dir,
        trace_id="t",
        year="2026",
        month="06",
        logger=make_logger(),
        client_factory=boom,
    )

    assert uploaded == 0


def test_missing_directory_returns_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ENABLE_GCS_UPLOAD", True)

    uploaded = gcs_service.upload_screenshots(
        screenshots_dir=tmp_path / "does-not-exist",
        trace_id="t",
        year="2026",
        month="06",
        logger=make_logger(),
        client_factory=lambda: FakeClient({}),
    )

    assert uploaded == 0


def test_client_construction_failure_is_swallowed(tmp_path, monkeypatch):
    screenshots_dir = tmp_path / "run"
    create_screenshots(screenshots_dir)

    monkeypatch.setattr(config, "ENABLE_GCS_UPLOAD", True)

    def failing_factory():
        raise RuntimeError("no credentials")

    uploaded = gcs_service.upload_screenshots(
        screenshots_dir=screenshots_dir,
        trace_id="t",
        year="2026",
        month="06",
        logger=make_logger(),
        client_factory=failing_factory,
    )

    assert uploaded == 0


def test_per_file_failure_does_not_abort_remaining_uploads(tmp_path, monkeypatch):
    screenshots_dir = tmp_path / "run"
    create_screenshots(screenshots_dir)

    monkeypatch.setattr(config, "ENABLE_GCS_UPLOAD", True)
    monkeypatch.setattr(config, "GCS_ROOT_PREFIX", "rpa")

    store = {}

    class FlakyBucket(FakeBucket):
        def blob(self, object_name):
            if "2222" in object_name:
                class FailingBlob:
                    def upload_from_filename(self, filename):
                        raise RuntimeError("transient network error")

                return FailingBlob()
            return FakeBlob(object_name, store)

    class FlakyClient(FakeClient):
        def bucket(self, bucket_name):
            self.requested_buckets.append(bucket_name)
            return FlakyBucket(bucket_name, store)

    uploaded = gcs_service.upload_screenshots(
        screenshots_dir=screenshots_dir,
        trace_id="t",
        year="2026",
        month="06",
        logger=make_logger(),
        client_factory=lambda: FlakyClient(store),
    )

    assert uploaded == 1
    assert len(store) == 1
