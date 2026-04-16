# japan/config.py

from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = "data/input/Japan5.xlsx"

#timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#OUTPUT_FILE = f"data/output/Japan_validated_{timestamp}.xlsx"

BASE_URL = "https://www.kegg.jp/kegg/medicus/"
SEARCH_URL = "https://www.kegg.jp/medicus-bin/search_drug?search_keyword="

TIMEOUT = 15000