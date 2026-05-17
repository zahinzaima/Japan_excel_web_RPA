# Japan Data Field Availability Report — Full Comparison
**Source:** KEGG Medicus (Japan) — `www.kegg.jp/kegg/medicus/`
**Input File:** `data/input/Japan4.xlsx`
**Output File:** `data/output/Japan_validated_20260402_224357.xlsx`
**Search Key:** YJ Code (薬価基準収載医薬品コード) — Column B
**Validation Fields:** Drug Price (M) + Brand Name (H) + Manufacturer Name (I)
**Ingredient Name (C) — extracted to Column R for reference only, not part of match criteria**
**Generated:** 2026-04-06

---

## 1. Coverage Summary

| Metric | Count |
|--------|------:|
| Total sheets in input file | 6 (2 empty: "As Is", "Clean") |
| Sheets processed by RPA | 4 |
| Total drug rows processed | 12,590 |
| Rows found on KEGG website | 10,328 (82.0%) |
| Rows not found on KEGG website | 2,262 (18.0%) |
| All 3 fields matched (Price + Brand + Manufacturer) | 2,822 (22.4% of total) |
| Rows with at least one mismatch | 7,506 (59.6% of total) |
| Errors during processing | 0 |

---

## 2. Input Excel Schema

| Col | Japanese Header | Description | Validated? |
|-----|-----------------|-------------|:----------:|
| A | 区分 | Drug category / classification | No |
| B | 薬価基準収載医薬品コード | **YJ Code** — primary search key | Key |
| C | 成分名 | Ingredient name (Japanese) | No *(extracted to Col R, not validated)* |
| D | 規格 | Formulation / dosage specification | No |
| E–G | *(unnamed)* | Additional specification sub-columns | No |
| H | 品名 | **Brand name & dosage form** | **Yes** |
| I | メーカー名 | **Manufacturer name** (Japanese) | **Yes** |
| J | 診療報酬において加算等の算定対象となる後発医薬品 | Generic drug reimbursement flag | No |
| K | 先発医薬品 | Originator drug flag | No |
| L | 同一剤形・規格の後発医薬品がある先発医薬品 | Originator with generic equivalent flag | No |
| M | 薬価 | **Drug price** (NHI listed price) | **Yes** |
| N | 経過措置による使用期限 | Grace period expiry date | No |
| O | 備考 | Remarks / notes | No |

---

## 3. Output Schema — Derived & Validation Columns (P–U)

| Col | Column Name | Populated From | Logic |
|-----|-------------|---------------|-------|
| P | `Validation_Remarks` | Comparison result | `"All Match"` (green) if Brand (H) + Manufacturer (I) + Price (M) all match; otherwise lists each mismatched field with the KEGG value |
| Q | `Web_Status` | KEGG search result | `"Found"` (green) / `"Not Found"` (red) |
| R | `Ingredient` | KEGG 欧文一般名 | English ingredient name — informational only, no match logic applied; blank if KEGG has no EN name |
| S | `Brand_Dosage` | KEGG 欧文商標名 | English brand/dosage name — informational only; blank if KEGG has no EN brand |
| T | `Manufacture_name` | Google Translate of Column I | Translated JP→EN only when Column I matches KEGG; blank on manufacturer mismatch |
| U | `ATC_Code` | KEGG ATCコード | Extracted directly; blank if KEGG does not assign an ATC code for the drug |

---

## 4. Per-Sheet Validation Summary

Validation criteria: **Brand (H) + Manufacturer (I) + Price (M)**

| Sheet | Total Rows | Found | Not Found | All Match | Price-Only Mismatch | Brand + Price Mismatch | Manufacturer + Price Mismatch |
|-------|:----------:|:-----:|:---------:|:---------:|:-------------------:|:----------------------:|:-----------------------------:|
| ＨＰ用 | 7,021 | 5,674 | 1,347 | 1,259 (22.2% of found) | 4,412 | 0 | 3 |
| ＨＰ用 (2) | 3,538 | 2,978 | 560 | 1,244 (41.8% of found) | 1,731 | 1 | 2 |
| ＨＰ用 (3) | 2,003 | 1,649 | 354 | 298 (18.1% of found) | 1,341 | 0 | 10 |
| ＨＰ用 (4) | 28 | 27 | 1 | 21 (77.8% of found) | 6 | 0 | 0 |
| **Total** | **12,590** | **10,328** | **2,262** | **2,822 (27.3% of found)** | **7,490** | **1** | **15** |

---

## 5. Validation Results Breakdown

| Result Type | Count | % of Total Rows | % of Found Rows |
|-------------|:-----:|:---------------:|:---------------:|
| All Match — Price + Brand + Manufacturer correct | 2,822 | 22.4% | 27.3% |
| Price (M) mismatch only | 7,490 | 59.5% | 72.5% |
| Manufacturer (I) + Price (M) mismatch | 15 | 0.1% | 0.1% |
| Brand (H) + Price (M) mismatch | 1 | 0.0% | 0.0% |
| Not Found on KEGG | 2,262 | 18.0% | — |
| **Total** | **12,590** | **100%** | |

> **Verified:** 2,822 + 7,490 + 15 + 1 + 2,262 = **12,590** ✓

> **Note:** 275 rows have an Ingredient (Column C) discrepancy recorded in `Validation_Remarks`. Since Ingredient is excluded from the match criteria, these rows are classified by their H/I/M result only — 81 of them count as All Match (only C had an issue) and 194 are reclassified as price-only mismatches (C+M → M only).

### Price Mismatch Direction (7,506 rows with Column M mismatch)

| Direction | Count | % of M-mismatch rows |
|-----------|:-----:|:--------------------:|
| Web price **lower** than Excel (price cut / revision) | 6,369 | 84.9% |
| Web price **higher** than Excel (price increase) | 1,137 | 15.1% |
| Web price = 0.0 (discontinued / not published) | 66 | 0.9% |

> **Key finding:** 84.9% of price mismatches show the web price as *lower* than the Excel value — consistent with the input file containing an older NHI price schedule that has since been revised downward. The 15.1% with higher web prices are drugs that received price increases after the Excel snapshot was taken.

---

## 6. Field-Level Mismatch Detail

### Column H — Brand Name (品名) — 1 mismatch

| YJ Code | Excel Brand | KEGG Brand | Remarks |
|---------|-------------|------------|---------|
| 7290401A1026 | 診断用アレルゲンスクラッチエキス「トリイ」 | アレルゲンスクラッチエキス「トリイ」アサリ | KEGG uses extended product name including allergen type (アサリ); Excel uses the generic product name |

### Column I — Manufacturer Name (メーカー名) — 15 mismatches

All 15 manufacturer mismatches co-occur with a price mismatch, indicating the Excel data is from a prior period when these drugs were held by a different marketing authorisation (MA) holder.

| YJ Code | Excel Manufacturer | KEGG Manufacturer | Pattern |
|---------|--------------------|-------------------|---------|
| 2356001X1124 | 大成薬品工業 | 東海製薬 | Company name change / MA transfer |
| 2615705Q1099 | 大成薬品工業 | 東海製薬 | Company name change / MA transfer |
| 2619702Q3283 | 大成薬品工業 | 東海製薬 | Company name change / MA transfer |
| 7121703X1194 | 大成薬品工業 | 東海製薬 | Company name change / MA transfer |
| 3999021F1023 | 日本イーライリリー | クリニジェン | Licensing / MA transfer |
| 7131001X1453 | ヤクハン製薬 | 日医工 | MA transfer |
| 2619702Q3275 | ヤクハン製薬 | 日医工 | MA transfer |
| 7121704X1415 | ヤクハン製薬 | 日医工 | MA transfer |
| 6122400D1028 | エーザイ | Meiji Seikaファルマ | MA transfer |
| 6122400D2024 | エーザイ | Meiji Seikaファルマ | MA transfer |
| 1319720Q1172 | わかもと製薬 | 千寿製薬 | MA transfer (5 variants) |
| 1319720Q2071 | わかもと製薬 | 千寿製薬 | MA transfer |
| 1319720Q7235 | わかもと製薬 | 千寿製薬 | MA transfer |
| 1319720Q7243 | わかもと製薬 | 千寿製薬 | MA transfer |
| 1319720Q8223 | わかもと製薬 | 千寿製薬 | MA transfer |

---

## 7. Derived Column Population Analysis

### Population rates (10,328 Found rows)

| Column | Populated | Missing | Missing % | Root Cause for Missing |
|--------|:---------:|:-------:|:---------:|------------------------|
| `Web_Status` (Q) | 12,590 | 0 | 0% | Always populated |
| `Validation_Remarks` (P) | 12,590 | 0 | 0% | Always populated |
| `Manufacture_name` (T) | 10,313 | 15 | 0.1% | Empty only when Column I mismatches KEGG — by design |
| `Brand_Dosage` (S / 欧文商標名) | 9,241 | 1,087 | 10.5% | KEGG does not publish 欧文商標名 for raw materials, excipients, and bulk ingredients |
| `Ingredient` (R / 欧文一般名) | 8,832 | 1,496 | 14.5% | KEGG does not publish 欧文一般名 for Kampo/traditional preparations, botanical extracts, complex compound raw materials |
| `ATC_Code` (U) | 7,850 | 2,478 | 24.0% | KEGG does not assign ATC codes to excipients, Kampo/herbal medicines, radiopharmaceuticals, blood products, and peritoneal dialysis solutions |

### Missing ATC Code — Top Drug Categories (2,478 rows total across all 10,328 found rows)

| YJ Code Prefix | Rows Missing ATC | Representative Drug / Category |
|:--------------:|:----------------:|-------------------------------|
| 5200 | 580 | Kampo (traditional Japanese herbal medicines) — e.g. コタロー安中散エキス細粒 |
| 3319 | 163 | Electrolyte / correction solutions — e.g. 乳酸Ｎａ補正液１ｍＥｑ／ｍＬ |
| 3420 | 137 | Peritoneal dialysis solutions — e.g. ダイアニール－Ｎ ＰＤ－２ |
| 2149 | 98 | Neurological / autonomic agents — e.g. デタントール錠０．５ｍｇ |
| 3999 | 98 | Specialty biologics / immunosuppressants — e.g. ブレディニン錠２５ |
| 5100 | 81 | Crude drug / botanical extracts — e.g. ウチダのイレイセンＭ |
| 3259 | 51 | Elemental / amino acid nutritional preparations — e.g. エレンタール配合内用剤 |
| 1319 | 51 | Ophthalmological agents — e.g. アダプチノール錠５ｍｇ |
| 6342 | 49 | Blood products (platelets, plasma) — e.g. 濃厚血小板－ＬＲ「日赤」 |
| 3311 | 46 | Saline / irrigation solutions — e.g. 生食液「小林」 |
| 2649 | 44 | Topical dermatological preparations — e.g. 亜鉛華軟膏「コザカイ・Ｍ」 |
| 3410 | 43 | Kidney dialysis agents — e.g. キンダリー透析剤ＡＦ１号 |
| 1169 | 35 | CNS agents — e.g. ドプス細粒２０％ |
| 7121 | 34 | Pharmaceutical excipients (fats/oils/waxes) — e.g. 白色軟膏（日興製薬） |
| 2190 | 33 | Migraine / vasoactive agents — e.g. ミグシス錠５ｍｇ |

### Missing Field Totals (across all 12,590 rows)

| Field | Total Rows Missing | % of All Rows | Pattern |
|-------|:-----------------:|:-------------:|---------|
| `ATC_Code` | 4,740 | 37.6% | Excipients, Kampo, herbal/botanical, blood products, dialysis solutions |
| `Ingredient` (EN / 欧文一般名) | 3,758 | 29.8% | Kampo, botanical extracts, complex compound preparations |
| `Brand_Dosage` (EN / 欧文商標名) | 3,349 | 26.6% | Raw materials, solvents, excipients — no EN brand on KEGG |
| `Manufacture_name` | 2,277 | 18.1% | 2,262 Not Found rows + 15 manufacturer-mismatch rows |
| `Web_Status` | 0 | 0% | Always populated |
| `Validation_Remarks` | 0 | 0% | Always populated |

> Note: Missing totals above include both Not Found rows (2,262) and found rows where KEGG simply does not publish the field.

---

## 8. Large Price Discrepancies (|Difference| > ¥100,000)

Only 3 rows exceed this threshold. The remaining ~7,500 price mismatches are routine NHI revision adjustments (typically < ¥1,000 difference).

| YJ Code | Brand Name | Excel Price (¥) | KEGG Price (¥) | Difference (¥) |
|---------|------------|:--------------:|:--------------:|:--------------:|
| 1390400D1026 | テッペーザ点滴静注用５００ｍｇ | 979,920 | 1,175,904 | +195,984 |
| 1290401G1021 | アムヴトラ皮下注２５ｍｇシリンジ | 7,810,923 | 8,006,196 | +195,273 |
| 3999434A1026 | イラリス皮下注射液１５０ｍｇ | 1,526,075 | 1,144,556 | −381,519 |

> These are ultra-high-cost specialty drugs (orphan disease / gene therapy class). The large absolute differences reflect percentage-level revisions applied to very high base prices.

---

## 9. Recommendations

| Priority | Action | Affected Rows |
|----------|--------|:-------------:|
| **High** | Refresh the input Excel with the current NHI drug price schedule — 7,506 price mismatches (59.6% of all rows) are driven by an outdated price snapshot | 7,506 |
| **High** | Investigate the 2,262 Not Found entries — confirm whether these YJ codes have been discontinued, reissued under new codes, or were never listed on KEGG Medicus | 2,262 |
| **Medium** | Investigate 15 manufacturer mismatches — all are likely MA (Marketing Authorisation) transfers; update Column I in the input file with the current authorisation holder | 15 |
| **Medium** | Accept missing ATC codes as expected for Kampo (5200x), crude botanicals (5100x), excipients (71xxx), blood products (6342x–6343x), and dialysis solutions (3420x) — document these as "N/A — not assigned by KEGG" | 2,478 |
| **Low** | Accept missing 欧文一般名 / 欧文商標名 as expected for raw material and Kampo categories — KEGG does not publish EN names for these drug types | 1,087–1,496 |
| **Low** | Flag the single brand mismatch (7290401A1026) for manual review — KEGG uses a more specific allergen variant name than Excel | 1 |
| **Low** | Ingredient (Column C) discrepancies (275 rows) are informational — visible in `Validation_Remarks` but do not affect the match result under current criteria | 275 |
| **Low** | Add a drug category column derived from the YJ code prefix (e.g. 5200x = Kampo, 71xxx = excipient) to make missing-field patterns self-documenting and filterable | All rows |
