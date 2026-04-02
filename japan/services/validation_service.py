from japan.services.normalization_service import (
    normalize_text,
    normalize_price,
    normalize_company,
    brand_match,
    company_match,
    flexible_match
)


def validate_row(excel_row: dict, web_data: dict):

    if not web_data:
        return "Not Found", "No matching YJコード found"

    mismatches = []

    # Column C → Ingredient (Flexible Match)
    web_ingredient = web_data.get("Ingredient")

    if web_ingredient:  # Only validate if Ingredient exists
        if not flexible_match(excel_row.get("C"), web_ingredient):
            mismatches.append(
                f"Column C mismatch → Web: {web_ingredient}"
            )


   # Column H → Brand (Flexible Match)
    excel_brand = excel_row.get("H")
    web_brand = web_data.get("brand")

    if web_brand:
        # Try strict brand match first
        if not brand_match(excel_brand, web_brand):
            # Fallback to flexible match
            if not flexible_match(excel_brand, web_brand):
                mismatches.append(
                    f"Column H mismatch → Web: {web_brand}"
                )


    # Column I → Company (normalize bracket/dash)
    if not company_match(excel_row.get("I"), web_data.get("company")):
        mismatches.append(
            f"Column I mismatch → Web: {web_data.get('company')}"
        )

    # Column M → Price (numeric compare)
    if normalize_price(excel_row.get("M")) != normalize_price(web_data.get("price")):
        mismatches.append(
            f"Column M mismatch → Web: {normalize_price(web_data.get('price'))}"
        )

    if mismatches:
        return "Found", " | ".join(mismatches)

    return "Found", "All Match"