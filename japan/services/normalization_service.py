import re
import unicodedata


# =========================================
# FLEXIBLE MATCH (General Purpose)
def flexible_match(a, b):

    if not a or not b:
        return False

    a_norm = normalize_text(a)
    b_norm = normalize_text(b)

    # Split into components (newline separator)
    a_parts = [x.strip() for x in a_norm.split("\n") if x.strip()]
    b_parts = [x.strip() for x in b_norm.split("\n") if x.strip()]

    # Every Excel component must exist inside web components
    for a_part in a_parts:
        if not any(a_part in b_part for b_part in b_parts):
            return False

    return True

# =========================================
# TEXT NORMALIZATION (General Purpose)
# =========================================
def normalize_text(value):

    if value is None:
        return ""

    value = unicodedata.normalize("NFKC", str(value))

    # Replace Japanese separator dot with space
    value = value.replace("・", "\n")


    # Remove Japanese quotes
    value = value.replace("「", "")
    value = value.replace("」", "")

    # Normalize dash types
    value = value.replace("－", "-")
    value = value.replace("−", "-")
    value = value.replace("―", "-")
    value = value.replace("-", "") 

    # Normalize bracket styles (full-width and half-width)
    value = value.replace("〈", "")
    value = value.replace("〉", "")
    value = value.replace("＜", "")
    value = value.replace("＞", "")
    value = value.replace("<", "")   
    value = value.replace(">", "")   



    # Remove manufacturer brackets and quotes
    value = re.sub(r"[（(][^）)]*[）)]", "", value)  # remove （山善）
    value = re.sub(r"[「][^」]*[」]", "", value)    # remove 「ヤマゼン」


    # Remove generic label
    value = value.replace("後発品", "")

    # Remove formulation suffixes
    value = value.replace("配合剤", "")
    value = value.replace("製剤", "")
    value = value.replace("水和物", "")
    value = value.replace("エキス", "")

    # Normalize gamma representation (domain-specific rule)
    value = value.replace("ガンマー", "ガンマ")

    # Remove spaces (both half & full width)
    value = value.replace("　", " ")
    value = value.replace(" ", "")

    # Lowercase
    value = value.strip().lower()

    return value


# =========================================
# BRAND MATCH
# =========================================
def brand_match(excel_value, web_value):

    excel_norm = normalize_text(excel_value)
    web_norm = normalize_text(web_value)

    return web_norm.startswith(excel_norm)


# =========================================
# COMPANY NORMALIZATION
# =========================================
def normalize_company(value):

    if value is None:
        return ""

    value = unicodedata.normalize("NFKC", str(value))

    # Convert brackets to hyphen style
    value = re.sub(r"[（(]", "-", value)
    value = re.sub(r"[）)]", "", value)

    # Normalize dash types
    value = value.replace("－", "-")
    value = value.replace("―", "-")
    value = value.replace("−", "-")

    # Remove Japanese quotes
    value = value.replace("「", "")
    value = value.replace("」", "")

    # Remove spaces
    value = value.replace("　", "")
    value = value.replace(" ", "")

    return value.strip().lower()


# =========================================
# COMPANY MATCH (Smarter)
# =========================================
def company_match(excel_value, web_value):

    excel_norm = normalize_company(excel_value)
    web_norm = normalize_company(web_value)

    # Remove bracket content for comparison
    excel_base = re.sub(r"-.*", "", excel_norm)
    web_base = re.sub(r"-.*", "", web_norm)

    return (
        excel_norm == web_norm
        or excel_base == web_base
        or excel_base in web_base
        or web_base in excel_base
    )


# =========================================
# PRICE NORMALIZATION
# =========================================
def normalize_price(value):

    if value is None:
        return 0.0

    value = str(value)
    value = unicodedata.normalize("NFKC", value)

    value = value.replace("円", "")
    value = value.replace("/錠", "")
    value = value.replace("/g", "")
    value = value.replace(",", "")
    value = value.strip()

    match = re.search(r"\d+(\.\d+)?", value)

    if not match:
        return 0.0

    return float(match.group())