import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_truthy(value, default=True):
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "off", "no", ""}

INPUT_FILE = BASE_DIR / "data" / "input" / "Japan.xlsx"
OUTPUT_DIR = BASE_DIR / "data" / "output"
CHECKPOINTS_DIR = OUTPUT_DIR / "checkpoints"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"
LOGS_DIR = BASE_DIR / "logs"

BASE_URL = "https://www.kegg.jp/kegg/medicus/"
SEARCH_URL = "https://www.kegg.jp/medicus-bin/search_drug?search_keyword="

TIMEOUT = 15000
NAVIGATION_TIMEOUT = 60000
DEFAULT_TIMEOUT = 45000
CHECKPOINT_SAVE_INTERVAL = 100

# Screenshots: capture every product page that is opened, save as a
# 720px-wide PNG organized into year/month folders (screenshots/YYYY/MM/).
ENABLE_SCREENSHOTS = True
SCREENSHOT_WIDTH = 720

# Google Cloud Storage: at the end of a run, every captured screenshot is
# batch-uploaded to GCS. Authentication uses Application Default Credentials
# (GOOGLE_APPLICATION_CREDENTIALS, or `gcloud auth application-default login`).
# Destination layout (mirrors the other country RPA pipelines):
#   gs://<GCS_BUCKET_NAME>/<GCS_ROOT_PREFIX>/<COUNTRY_NAME>/<YYYY>/<MM>/<TraceId>
#       /screenshots/<DRUG_ID>/Medicine=[<brand>]_Company=[<company>].png
COUNTRY_NAME = "Japan"
ENABLE_GCS_UPLOAD = _env_truthy(os.getenv("ENABLE_GCS_UPLOAD"), default=True)
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "app_modernization_v2_dev")
GCS_ROOT_PREFIX = os.getenv("GCS_ROOT_PREFIX", "rpa")
