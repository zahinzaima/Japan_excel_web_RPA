import os

import pytest

from japan.runner import run_validation


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_JAPAN_VALIDATION") != "1",
    reason="Live KEGG validation is opt-in only",
)
def test_japan_validation_live():
    summary = run_validation(mode="clean-run")
    assert summary["output_file"]
