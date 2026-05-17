import json
from datetime import datetime
from pathlib import Path

from japan import config
from japan.services.excel_service import (
    ensure_validation_columns,
    read_checkpoint_csv,
    read_workbook,
    save_checkpoint_csv,
)


METADATA_FILE = "checkpoint_meta.json"


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def checkpoint_root(base_dir=None):
    root = Path(base_dir or config.CHECKPOINTS_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_checkpoint_workspace(sheet_names, base_dir=None, checkpoint_name=None, input_file=None):
    name = checkpoint_name or _timestamp()
    root = checkpoint_root(base_dir)
    workspace = root / name
    workspace.mkdir(parents=True, exist_ok=True)

    metadata = {
        "checkpoint_name": name,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "input_file": str(input_file) if input_file else "",
        "sheets": [],
    }

    for index, sheet_name in enumerate(sheet_names, start=1):
        metadata["sheets"].append(
            {
                "sheet_name": sheet_name,
                "file_name": f"sheet_{index:03d}.csv",
            }
        )

    write_metadata(workspace, metadata)
    return workspace, metadata


def write_metadata(checkpoint_dir, metadata):
    metadata_path = Path(checkpoint_dir) / METADATA_FILE
    metadata["updated_at"] = datetime.now().isoformat()
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_metadata(checkpoint_dir):
    metadata_path = Path(checkpoint_dir) / METADATA_FILE
    if not metadata_path.exists():
        raise FileNotFoundError(f"Checkpoint metadata not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def save_sheet_checkpoint(checkpoint_dir, metadata, sheet_name, df):
    entry = next(
        (item for item in metadata["sheets"] if item["sheet_name"] == sheet_name),
        None,
    )
    if entry is None:
        raise KeyError(f"Unknown sheet in checkpoint metadata: {sheet_name}")

    csv_path = Path(checkpoint_dir) / entry["file_name"]
    save_checkpoint_csv(df, csv_path)
    write_metadata(checkpoint_dir, metadata)
    return csv_path


def save_all_checkpoints(checkpoint_dir, metadata, sheets):
    for sheet_name, df in sheets.items():
        save_sheet_checkpoint(checkpoint_dir, metadata, sheet_name, df)


def resolve_checkpoint(checkpoint_ref=None, base_dir=None):
    root = checkpoint_root(base_dir)

    if checkpoint_ref:
        candidate = Path(checkpoint_ref)
        if candidate.exists():
            return candidate

        named = root / checkpoint_ref
        if named.exists():
            return named

        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_ref}")

    checkpoints = [path for path in root.iterdir() if path.is_dir()]
    if not checkpoints:
        raise FileNotFoundError(f"No checkpoints found in {root}")

    return max(checkpoints, key=lambda path: path.stat().st_mtime)


def load_checkpoint(checkpoint_ref=None, base_dir=None):
    checkpoint_dir = resolve_checkpoint(checkpoint_ref, base_dir=base_dir)
    metadata = read_metadata(checkpoint_dir)
    sheets = {}

    for entry in metadata["sheets"]:
        csv_path = checkpoint_dir / entry["file_name"]
        sheets[entry["sheet_name"]] = read_checkpoint_csv(csv_path)

    return checkpoint_dir, metadata, sheets


def initialize_clean_checkpoint(input_file=None, base_dir=None, checkpoint_name=None, limit=None):
    sheets = read_workbook(file_path=input_file, limit=limit)
    sheets = {
        sheet_name: ensure_validation_columns(df.copy())
        for sheet_name, df in sheets.items()
    }
    checkpoint_dir, metadata = create_checkpoint_workspace(
        list(sheets.keys()),
        base_dir=base_dir,
        checkpoint_name=checkpoint_name,
        input_file=input_file or config.INPUT_FILE,
    )
    save_all_checkpoints(checkpoint_dir, metadata, sheets)
    return checkpoint_dir, metadata, sheets


def build_output_file(checkpoint_name, output_dir=None):
    output_root = Path(output_dir or config.OUTPUT_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root / f"Japan_validated_{checkpoint_name}.xlsx"
