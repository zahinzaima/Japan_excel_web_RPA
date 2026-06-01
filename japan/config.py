from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

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
