# Japan Excel Web RPA

Validates Japanese drug data from an Excel workbook against the
[KEGG MEDICUS](https://www.kegg.jp/kegg/medicus/) website by YJ code, writes the
results back to a new workbook, captures a screenshot of each product page, and
(optionally) uploads those screenshots to Google Cloud Storage.

## 🚀 First-time setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the Playwright browser (Chromium)
playwright install chromium
```

Next time, just re-activate the environment:

```bash
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

## ▶️ Run commands

The runner is driven through `main.py`. Exactly **one** mode flag is required.

```bash
# Start a fresh run from the input workbook (data/input/Japan.xlsx)
python main.py --clean-run

# Resume from the most recent checkpoint
python main.py --resume

# Resume from a specific checkpoint (name under data/output/checkpoints/, or an explicit path)
python main.py --resume-from <CHECKPOINT>

# Retry only the rows marked "Error" in the latest checkpoint
python main.py --resolve-errors

# Show all options
python main.py --help
```

Each run:
- reads `data/input/Japan.xlsx`,
- writes a validated workbook to `data/output/Japan_validated_<timestamp>.xlsx`,
- saves resumable checkpoints under `data/output/checkpoints/`,
- captures screenshots locally under `data/output/screenshots/<TraceId>/`,
- prints a summary, e.g.:

  ```
  Completed clean-run: processed=120, all_match=98, mismatched=12, not_found=8,
  errors=2, screenshots_uploaded=112, output=data/output/Japan_validated_20260603_101010.xlsx
  ```

## 🖼️ Screenshots & Google Cloud Storage

At the end of a run, screenshots are batch-uploaded to GCS:

```
gs://<GCS_BUCKET_NAME>/rpa/Japan/<Year>/<Month>/<TraceId>/screenshots/<DrugID>/Medicine=[<brand>]_Company=[<company>].png
```

The output Excel gets a `screenshot_url` column with a clickable link to each
row's screenshot.

Authentication uses Application Default Credentials. Before a run that should
upload, authenticate one of these ways:

```bash
# Use your Google account (must have write access to the bucket)
gcloud auth application-default login

# OR point at a service-account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json   # macOS / Linux
setx GOOGLE_APPLICATION_CREDENTIALS "C:\path\to\key.json" # Windows
```

If no credentials are available the run still completes and keeps the **local**
screenshots; the upload is skipped with a warning.

### Configurable environment variables

| Variable | Default | Purpose |
|---|---|---|
| `ENABLE_GCS_UPLOAD` | `true` | Set to `false`/`0` to skip the GCS upload entirely. |
| `GCS_BUCKET_NAME` | `app_modernization_v2_dev` | Destination bucket. |
| `GCS_ROOT_PREFIX` | `rpa` | Top-level object prefix. |

```bash
# Example: run without uploading to GCS
ENABLE_GCS_UPLOAD=false python main.py --clean-run
```

## ✅ Tests

```bash
# Run the full suite
pytest -v -s

# Skip the live KEGG website test (no network / browser needed)
pytest -v -s --deselect tests/test_japan_validation.py::test_japan_validation_live
```
