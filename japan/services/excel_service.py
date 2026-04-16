from wsgiref import headers

import pandas as pd
from japan import config
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from pathlib import Path


# 🔹 Column Mapping (JP + EN support)
COLUMN_MAPPING = {
    "薬価基準収載医薬品コード": [
        "薬価基準収載医薬品コード",
        "薬価基準収載医薬品コード (YJ Code)",
        "YJ Code",
        "Drug price standard listed drug code"
    ],
    "成分名": [
        "成分名",
        "Ingredient name"
    ],
    "品名": [
        "品名",
        "Product name"
    ],
    "メーカー名": [
        "メーカー名",
        "Manufacture name"
    ],
    "薬価": [
        "薬価",
        "Drug price"
    ]
}



def normalize_columns(df):

    new_columns = {}

    for standard_col, variations in COLUMN_MAPPING.items():
        for col in df.columns:
            col_clean = col.strip().lower()

            for variation in variations:
                if col_clean == variation.strip().lower():
                    new_columns[col] = standard_col
                    break

    df = df.rename(columns=new_columns)

    return df


# 🔹 Read ALL sheets
def read_excel(limit=None):

    file_path = Path(config.INPUT_FILE)

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    excel_file = pd.ExcelFile(file_path)

    print(f"📂 Found sheets: {excel_file.sheet_names}")

    all_sheets = {}

    for sheet in excel_file.sheet_names:

        print(f"🔎 Reading sheet: {sheet}")

        df = pd.read_excel(file_path, sheet_name=sheet)
        df = normalize_columns(df)

        if df.empty:
            print(f"⚠ Sheet '{sheet}' is empty. Skipping.")
            continue

        print(f"📊 Total rows found: {len(df)}")

        if limit:
            df = df.head(limit)
            print(f"🚀 Processing first {len(df)} rows")

        all_sheets[sheet] = df

    if not all_sheets:
        raise ValueError("❌ All sheets are empty in the Excel file.")

    return all_sheets


# 🔹 Save multiple sheets
def save_excel(all_sheets_dict, output_file, format_file=False):

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sheet_name, df in all_sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    if not format_file:
        print(f"💾 Auto-saved: {output_file}")
        return

    # Apply formatting sheet by sheet
    wb = load_workbook(output_file)

    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")


    for ws in wb.worksheets:

        headers = [cell.value for cell in ws[1]]

        if "Validation_Remarks" not in headers or "Web_Status" not in headers:
            continue

        remarks_col = headers.index("Validation_Remarks") + 1
        status_col = headers.index("Web_Status") + 1

        for row in range(2, ws.max_row + 1):
            remarks_cell = ws.cell(row=row, column=remarks_col)
            status_cell = ws.cell(row=row, column=status_col)

            if remarks_cell.value == "All Match":
                remarks_cell.fill = green_fill
            elif remarks_cell.value:
                remarks_cell.fill = red_fill

            if status_cell.value == "Found":
                status_cell.fill = green_fill
            elif status_cell.value == "Not Found":
                status_cell.fill = red_fill

            
    wb.save(output_file)
    print(f"\n✅ Final Excel saved with formatting: {output_file}")


# 🔹 Ensure validation columns
def ensure_validation_columns(df):

    new_cols = [
        "Validation_Remarks",
        "Web_Status",
        "Ingredient",
        "Brand_Dosage",
        "Manufacture_name",
        "ATC_Code"
    ]

    for col in new_cols:
        if col not in df.columns:
            df[col] = ""

    return df