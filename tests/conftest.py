from __future__ import annotations

import os
from pathlib import Path

import pytest


_TARGET_FILE = (
    "test_covapie_current11_unit_000001_controlled_editable_"
    "reaction_transformation_review_copy_v1.py"
)
_TARGET_TEST = "test_repository_lifecycle_exact3_in_base_anchored_temp_git"


@pytest.fixture(autouse=True)
def _covapie_controlled_review_exact3_umask_portability(
    request: pytest.FixtureRequest,
):
    path = Path(str(request.node.path))
    if path.name != _TARGET_FILE or request.node.name != _TARGET_TEST:
        yield
        return

    previous_umask = os.umask(0o022)
    try:
        yield
    finally:
        os.umask(previous_umask)
