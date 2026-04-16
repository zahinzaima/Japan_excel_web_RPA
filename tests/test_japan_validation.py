import pytest
from japan.pages.drug_page import DrugPage
from japan.services.excel_service import read_excel, save_excel, ensure_validation_columns
from japan.services.validation_service import validate_row
from japan.services.normalization_service import normalize_text, brand_match, company_match, flexible_match
from japan.services.translation_service import translate_company
from japan import config
from utils.logger import get_logger
from datetime import datetime
import os
import time

logger = get_logger()


def test_japan_validation(page):

    start_time = time.time()

    page.set_default_timeout(45000)
    page.set_default_navigation_timeout(60000)

    all_sheets = read_excel(limit=None)  # returns dict
    os.makedirs("data/output", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/output/Japan_validated_{timestamp}.xlsx"

    drug_page = DrugPage(page)

    processed_sheets = {}

    total_rows = 0
    all_match_count = 0
    mismatch_count = 0
    not_found_count = 0
    error_count = 0

    try:

        for sheet_name, df in all_sheets.items():
            logger.info(f"\n🚀 Processing Sheet: {sheet_name}")
            df = ensure_validation_columns(df)
            sheet_total_rows = len(df)
            sheet_error = 0  # sheet-level counter

            for index, row in df.iterrows():

                if str(row.get("web_status", "")).strip():
                    continue  # Skip already processed rows (useful for resuming after errors)

                total_rows += 1

                progress = (index + 1) / sheet_total_rows * 100

                drug_id = str(row["薬価基準収載医薬品コード"]).strip()
                #logger.info(f"[{sheet_name}] Row {index+1} | YJ Code: {drug_id}")
                logger.info(
                    f"[{sheet_name}] {index+1}/{sheet_total_rows}"
                    f" ({progress:.1f}%) | YJ Code: {drug_id}"
                )

                max_retry = 3

                for attempt in range(max_retry):
                    try:
                        drug_page.search_drug(drug_id)
                        # No result page
                        if drug_page.is_no_result_page():
                            df.at[index, "web_status"] = "Not Found"
                            df.at[index, "validation_remarks"] = ""
                            not_found_count += 1
                            logger.warning(f"{drug_id} → NOT FOUND")
                            break
                        
                        # If we have result links, open the first one (most likely match)
                        found = drug_page.open_matching_result()

                        if not found:
                            df.at[index, "web_status"] = "Not Found"
                            df.at[index, "validation_remarks"] = ""
                            not_found_count += 1
                            logger.warning(f"{drug_id} → NOT FOUND")
                            break
                        
                        # Extract details from the drug page
                        web_data = drug_page.extract_details(drug_id)
                        #print (f"Extracted Web Data: {web_data} for YJ Code: {drug_id}")

                        status, remarks = validate_row({
                            "B": row["薬価基準収載医薬品コード"],
                            "C": row["成分名"],
                            "H": row["品名"],
                            "I": row["メーカー名"],
                            "M": row["薬価"],
                        }, web_data)

                        df.at[index, "web_status"] = status
                        df.at[index, "validation_remarks"] = remarks

                        # ===============================
                        # Additional columns logic
                        # ===============================
                        if status == "Found" and web_data:
                            '''
                            # R column is Ingredient_English (came from data 欧文一般名) (only if C column matches)
                            if normalize_text(row["成分名"]) == normalize_text(web_data.get("Ingredient")):
                                df.at[index, "Ingredient"] = web_data.get("Ingredient_English", "")
                            else:
                                df.at[index, "Ingredient"] = ""
                            '''                             

                            # Column R → Ingredient (English)
                            # ===============================

                            excel_c = row.get("成分名", "")
                            web_ingredient_jp = web_data.get("ingredient", "")
                            web_ingredient_en = web_data.get("ingredient_english", "")
                            web_formulation = web_data.get("formulation", "")

                            ingredient_value = ""

                            # 1️⃣ Prefer 一般名 if available
                            # ===============================
                            # Column R → Ingredient (English)
                            # Populate if 欧文一般名 exists (independent of match)
                            # ===============================

                            web_ingredient_en = web_data.get("ingredient_english", "")

                            if web_ingredient_en:
                                ingredient_value = "・".join(
                                    [x.strip() for x in web_ingredient_en.split("\n") if x.strip()]
                                )
                            else:
                                ingredient_value = ""

                            df.at[index, "ingredient"] = ingredient_value
                            
                            # ===============================
                            # Column S → Brand_Dosage
                            # Populate if 欧文商標名 exists
                            # ===============================

                            web_brand_en = web_data.get("brand_en", "")

                            if web_brand_en:
                                df.at[index, "brand_dosage"] = web_brand_en.strip()
                            else:
                                df.at[index, "brand_dosage"] = ""

                            # T column → Manufacture name (only if I column matches)
                            if company_match(row["メーカー名"], web_data.get("company")):
                                jp_company = web_data.get("company", "")
                                en_company = translate_company(jp_company)
                                df.at[index, "manufacture_name"] = en_company
                            else:
                                df.at[index, "manufacture_name"] = ""

                            #jp_company = web_data.get("company", "")
                            #en_company = translate_company(jp_company)
                            #df.at[index, "manufacture_name"] = en_company

                            # U column → ATC code 
                            df.at[index, "atc_code"] = web_data.get("atc_code", "")

                        else:
                            df.at[index, "ingredient"] = ""
                            df.at[index, "brand_dosage"] = ""
                            df.at[index, "manufacture_name"] = ""
                            df.at[index, "atc_code"] = ""
                        # ===============================

                        if status == "Found" and remarks == "All Match":
                            all_match_count += 1
                            logger.info(f"{drug_id} → ALL MATCH")

                        elif status == "Found":
                            mismatch_count += 1
                            logger.error(f"{drug_id} → MISMATCH → {remarks}")

                        else:
                            not_found_count += 1
                            logger.warning(f"{drug_id} → NOT FOUND")

                        break
                                            

                    except Exception as row_error:

                        if attempt == max_retry - 1:
                            error_count += 1
                            sheet_error += 1
                            df.at[index, "web_status"] = "Error"
                            df.at[index, "validation_remarks"] = str(row_error)
                            logger.exception(f"{drug_id} → FINAL ERROR")

                        else:
                            logger.warning(f"{drug_id} → RETRYING...")
                            page.reload()   # FIXED (no BASE_URL jump)
                
                                        
                # Autosave every 100 rows
                if total_rows % 100 == 0:
                    processed_sheets[sheet_name] = df
                    save_excel(processed_sheets, output_file, format_file=True)
                    logger.info(f"💾 Auto-saved after {total_rows} rows")

                    

            # Sheet summary
            logger.info(f"\n--- Sheet Summary ({sheet_name}) ---")
            logger.info(f"Errors in this sheet : {sheet_error}")
            logger.info("-----------------------------------")

            processed_sheets[sheet_name] = df


    # Final save with formatting in the end, regardless of any errors
    finally:
        save_excel(processed_sheets, output_file, format_file=True)
        logger.info("Final Excel saved.")

    end_time = time.time()
    total_runtime = end_time - start_time
    runtime_str = time.strftime("%H:%M:%S", time.gmtime(total_runtime))
    logger.info(f"\n⏱️ Total Runtime: {runtime_str}")

    # Final summary
    logger.info("\n========== FINAL SUMMARY ==========")
    logger.info(f"Total Processed : {total_rows}")
    logger.info(f"All Match       : {all_match_count}")
    logger.info(f"Mismatched      : {mismatch_count}")
    logger.info(f"Not Found       : {not_found_count}")
    logger.info(f"Errors          : {error_count}")
    logger.info("===================================")