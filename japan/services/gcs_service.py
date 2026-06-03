"""Batch-upload run screenshots to Google Cloud Storage.

Screenshots are a side artifact, so anything that goes wrong here (the library
not being installed, missing credentials, a network hiccup) is logged and
swallowed rather than allowed to break a validation run. The upload happens once
at the end of a run, mirroring the ``upload_artifacts`` step used by the other
country RPA pipelines.

Destination layout:
    <GCS_ROOT_PREFIX>/<COUNTRY_NAME>/<year>/<month>/<trace_id>/screenshots/<rel>
where ``<rel>`` is the screenshot's path relative to the run's local
screenshots directory, e.g.
    rpa/Japan/2026/06/<trace_id>/screenshots/<DRUG_ID>/Medicine=[..]_Company=[..].png
"""

from pathlib import Path

from japan import config


def _default_client_factory():
    # Imported lazily so the project (and its tests) do not require
    # google-cloud-storage unless an upload is actually attempted.
    from google.cloud import storage

    return storage.Client()


def build_object_name(relative_path, trace_id, year, month, country=None):
    """Build the GCS object name for a screenshot at ``relative_path``."""
    country = country or config.COUNTRY_NAME
    base = f"{config.GCS_ROOT_PREFIX}/{country}/{year}/{month}/{trace_id}/screenshots"
    return f"{base.strip('/')}/{relative_path}"


def upload_screenshots(
    screenshots_dir,
    trace_id,
    year,
    month,
    country=None,
    logger=None,
    client_factory=None,
):
    """Upload every screenshot under ``screenshots_dir`` to GCS.

    Returns the number of files uploaded (0 if disabled, unavailable, or empty).
    """
    if not config.ENABLE_GCS_UPLOAD:
        if logger:
            logger.info("GCS upload disabled; skipping screenshot upload.")
        return 0

    screenshots_dir = Path(screenshots_dir)
    if not screenshots_dir.exists():
        if logger:
            logger.info("No screenshots directory at %s; nothing to upload.", screenshots_dir)
        return 0

    files = sorted(path for path in screenshots_dir.rglob("*") if path.is_file())
    if not files:
        if logger:
            logger.info("No screenshots found under %s; nothing to upload.", screenshots_dir)
        return 0

    try:
        factory = client_factory or _default_client_factory
        client = factory()
        bucket = client.bucket(config.GCS_BUCKET_NAME)
    except Exception as error:
        if logger:
            logger.warning("GCS client unavailable; skipping screenshot upload: %s", error)
        return 0

    uploaded = 0
    for local_file in files:
        relative = local_file.relative_to(screenshots_dir).as_posix()
        object_name = build_object_name(relative, trace_id, year, month, country=country)
        try:
            bucket.blob(object_name).upload_from_filename(str(local_file))
            uploaded += 1
            if logger:
                logger.info(
                    "Uploaded %s → gs://%s/%s", local_file, config.GCS_BUCKET_NAME, object_name
                )
        except Exception as error:
            if logger:
                logger.warning("Failed to upload %s: %s", local_file, error)

    if logger:
        logger.info(
            "Screenshot upload complete: %d file(s) → gs://%s/%s/%s/%s/%s/%s/screenshots",
            uploaded,
            config.GCS_BUCKET_NAME,
            config.GCS_ROOT_PREFIX,
            country or config.COUNTRY_NAME,
            year,
            month,
            trace_id,
        )
    return uploaded
