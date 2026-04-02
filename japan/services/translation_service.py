import json
import os
import time
from deep_translator import GoogleTranslator

# ===============================
# CACHE FILES
# ===============================
COMPANY_CACHE_FILE = "company_translation_cache.json"

# ===============================
# LOAD CACHE
# ===============================
def load_cache(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)


company_cache = load_cache(COMPANY_CACHE_FILE)

# Single translator instance (better performance)
translator = GoogleTranslator(source="ja", target="en")


# ===============================
# SAFE TRANSLATE CORE
# ===============================
def _safe_translate(text, cache_dict, cache_file, max_retry=3):

    if not text:
        return ""

    text = text.strip()

    # 1️⃣ Cache check
    if text in cache_dict:
        return cache_dict[text]

    # 2️⃣ Retry mechanism
    for attempt in range(max_retry):
        try:
            translated = translator.translate(text)

            if translated:

                # Optional: Capitalize first letter
                translated = translated.strip()
                translated = translated[0].upper() + translated[1:]

                cache_dict[text] = translated
                save_cache(cache_dict, cache_file)

                time.sleep(0.2)
                return translated

        except Exception:
            time.sleep(1)

    # ❌ If all retries fail → DO NOT store empty
    return ""


# ===============================
# PUBLIC FUNCTIONS
# ===============================
def translate_company(company_name, max_retry=3):
    return _safe_translate(
        company_name,
        company_cache,
        COMPANY_CACHE_FILE,
        max_retry
    )

