import time

from japan import config
from japan.pages.drug_page import DrugPage
from japan.runtime import runtime_page
from japan.services.checkpoint_service import (
    build_output_file,
    initialize_clean_checkpoint,
    load_checkpoint,
    save_all_checkpoints,
    save_sheet_checkpoint,
)
from japan.services.excel_service import export_to_excel
from japan.services.normalization_service import company_match
from japan.services.translation_service import flush_translation_cache, translate_company
from japan.services.validation_service import validate_row
from utils.logger import get_logger


RUN_MODES = {
    "clean-run",
    "resume",
    "resume-from",
    "resolve-errors",
}

DERIVED_COLUMNS = [
    "validation_remarks",
    "web_status",
    "ingredient",
    "brand_dosage",
    "manufacture_name",
    "atc_code",
]


def run_validation(
    mode,
    checkpoint_ref=None,
    input_file=None,
    checkpoint_root=None,
    output_dir=None,
    autosave_every=None,
    browser_factory=None,
    drug_page_cls=DrugPage,
    logger=None,
    limit=None,
):
    if mode not in RUN_MODES:
        raise ValueError(f"Unsupported run mode: {mode}")

    if mode == "resume-from" and not checkpoint_ref:
        raise ValueError("checkpoint_ref is required for resume-from mode")

    logger = logger or get_logger()
    autosave_every = autosave_every or config.CHECKPOINT_SAVE_INTERVAL

    checkpoint_dir, metadata, sheets = _load_run_state(
        mode=mode,
        checkpoint_ref=checkpoint_ref,
        input_file=input_file,
        checkpoint_root=checkpoint_root,
        limit=limit,
    )
    checkpoint_name = metadata["checkpoint_name"]
    output_file = build_output_file(checkpoint_name, output_dir=output_dir)

    summary = {
        "mode": mode,
        "checkpoint_name": checkpoint_name,
        "checkpoint_dir": str(checkpoint_dir),
        "output_file": str(output_file),
        "processed": 0,
        "all_match": 0,
        "mismatched": 0,
        "not_found": 0,
        "errors": 0,
        "runtime_seconds": 0.0,
    }

    browser_context = browser_factory() if browser_factory else runtime_page()
    start_time = time.time()

    try:
        with browser_context as page:
            drug_page = drug_page_cls(page)

            for sheet_name, df in sheets.items():
                logger.info(f"Processing sheet: {sheet_name}")
                sheet_error_count = 0
                sheet_processed = 0
                sheet_total_rows = len(df.index)

                for position, index in enumerate(df.index, start=1):
                    if not _should_process_row(df.at[index, "web_status"], mode):
                        continue

                    row = df.loc[index]
                    drug_id = str(row.get("薬価基準収載医薬品コード", "")).strip()
                    if not drug_id:
                        continue

                    if mode == "resolve-errors":
                        _clear_row_outputs(df, index)

                    sheet_processed += 1
                    summary["processed"] += 1
                    progress = position / sheet_total_rows * 100 if sheet_total_rows else 0
                    logger.info(
                        "[%s] %s/%s (%.1f%%) | YJ Code: %s",
                        sheet_name,
                        position,
                        sheet_total_rows,
                        progress,
                        drug_id,
                    )

                    try:
                        result = _process_row(df, index, row, drug_page, logger)
                    except Exception as row_error:
                        summary["errors"] += 1
                        sheet_error_count += 1
                        df.at[index, "web_status"] = "Error"
                        df.at[index, "validation_remarks"] = str(row_error)
                        logger.exception("%s → FINAL ERROR", drug_id)
                        result = "Error"

                    if result == "All Match":
                        summary["all_match"] += 1
                    elif result == "Mismatch":
                        summary["mismatched"] += 1
                    elif result == "Not Found":
                        summary["not_found"] += 1

                    if sheet_processed and sheet_processed % autosave_every == 0:
                        save_sheet_checkpoint(checkpoint_dir, metadata, sheet_name, df)
                        flush_translation_cache()
                        logger.info("Checkpoint saved after %s processed rows in %s", sheet_processed, sheet_name)

                save_sheet_checkpoint(checkpoint_dir, metadata, sheet_name, df)
                logger.info("Finished sheet: %s | errors: %s", sheet_name, sheet_error_count)

    finally:
        flush_translation_cache(force=True)
        save_all_checkpoints(checkpoint_dir, metadata, sheets)
        export_to_excel(sheets, output_file, format_file=True)

    summary["runtime_seconds"] = time.time() - start_time

    logger.info("Final Excel saved: %s", output_file)
    logger.info("Checkpoint directory: %s", checkpoint_dir)
    logger.info(
        "Processed=%s AllMatch=%s Mismatched=%s NotFound=%s Errors=%s Runtime=%.2fs",
        summary["processed"],
        summary["all_match"],
        summary["mismatched"],
        summary["not_found"],
        summary["errors"],
        summary["runtime_seconds"],
    )

    return summary


def _load_run_state(mode, checkpoint_ref=None, input_file=None, checkpoint_root=None, limit=None):
    if mode == "clean-run":
        return initialize_clean_checkpoint(
            input_file=input_file or config.INPUT_FILE,
            base_dir=checkpoint_root,
            limit=limit,
        )

    if mode == "resume-from":
        return load_checkpoint(checkpoint_ref=checkpoint_ref, base_dir=checkpoint_root)

    return load_checkpoint(checkpoint_ref=None, base_dir=checkpoint_root)


def _should_process_row(web_status, mode):
    status = str(web_status or "").strip()
    if mode == "resolve-errors":
        return status == "Error"
    return not status


def _clear_row_outputs(df, index):
    for column in DERIVED_COLUMNS:
        df.at[index, column] = ""


def _process_row(df, index, row, drug_page, logger):
    drug_id = str(row.get("薬価基準収載医薬品コード", "")).strip()
    max_retry = 3

    for attempt in range(max_retry):
        try:
            drug_page.search_drug(drug_id)

            if drug_page.is_no_result_page():
                _set_not_found(df, index)
                logger.warning("%s → NOT FOUND", drug_id)
                return "Not Found"

            found = drug_page.open_matching_result()
            if not found:
                _set_not_found(df, index)
                logger.warning("%s → NOT FOUND", drug_id)
                return "Not Found"

            web_data = drug_page.extract_details(drug_id)
            status, remarks = validate_row(
                {
                    "B": row.get("薬価基準収載医薬品コード"),
                    "C": row.get("成分名"),
                    "H": row.get("品名"),
                    "I": row.get("メーカー名"),
                    "M": row.get("薬価"),
                },
                web_data,
            )

            df.at[index, "web_status"] = status
            df.at[index, "validation_remarks"] = remarks

            if status == "Found" and web_data:
                _populate_derived_columns(df, index, row, web_data)
            else:
                _clear_row_outputs(df, index)
                df.at[index, "web_status"] = status
                df.at[index, "validation_remarks"] = remarks

            if status == "Found" and remarks == "All Match":
                logger.info("%s → ALL MATCH", drug_id)
                return "All Match"

            if status == "Found":
                logger.error("%s → MISMATCH → %s", drug_id, remarks)
                return "Mismatch"

            logger.warning("%s → NOT FOUND", drug_id)
            return "Not Found"

        except Exception:
            if attempt == max_retry - 1:
                raise

            logger.warning("%s → RETRYING...", drug_id)
            page = getattr(drug_page, "page", None)
            if page and hasattr(page, "reload"):
                try:
                    page.reload()
                except Exception:
                    pass

    return "Error"


def _set_not_found(df, index):
    _clear_row_outputs(df, index)
    df.at[index, "web_status"] = "Not Found"
    df.at[index, "validation_remarks"] = ""


def _populate_derived_columns(df, index, row, web_data):
    ingredient_english = web_data.get("ingredient_english", "")
    if ingredient_english:
        df.at[index, "ingredient"] = "・".join(
            [item.strip() for item in ingredient_english.split("\n") if item.strip()]
        )
    else:
        df.at[index, "ingredient"] = ""

    df.at[index, "brand_dosage"] = web_data.get("brand_en", "").strip()

    if company_match(row.get("メーカー名"), web_data.get("company")):
        df.at[index, "manufacture_name"] = translate_company(web_data.get("company", ""))
    else:
        df.at[index, "manufacture_name"] = ""

    df.at[index, "atc_code"] = web_data.get("atc_code", "")
