import atexit
import json
import time
from pathlib import Path

from deep_translator import GoogleTranslator


COMPANY_CACHE_FILE = Path("company_translation_cache.json")


def load_cache(file_path):
    cache_path = Path(file_path)
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    return {}


def save_cache(cache, file_path):
    cache_path = Path(file_path)
    cache_path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )


company_cache = load_cache(COMPANY_CACHE_FILE)
dirty_cache_entries = 0
translator = GoogleTranslator(source="ja", target="en")


def flush_translation_cache(force=False):
    global dirty_cache_entries

    if dirty_cache_entries == 0 and not force:
        return

    save_cache(company_cache, COMPANY_CACHE_FILE)
    dirty_cache_entries = 0


def _remember_translation(text, translated):
    global dirty_cache_entries

    company_cache[text] = translated
    dirty_cache_entries += 1

    if dirty_cache_entries >= 25:
        flush_translation_cache()


def _safe_translate(text, cache_dict, max_retry=3):
    if not text:
        return ""

    text = text.strip()

    if text in cache_dict:
        return cache_dict[text]

    for _ in range(max_retry):
        try:
            translated = translator.translate(text)

            if translated:
                translated = translated.strip()
                translated = translated[0].upper() + translated[1:]
                _remember_translation(text, translated)
                time.sleep(0.2)
                return translated
        except Exception:
            time.sleep(1)

    return ""


def translate_company(company_name, max_retry=3):
    return _safe_translate(company_name, company_cache, max_retry=max_retry)


atexit.register(flush_translation_cache, force=True)
