"""Public in-memory adapter for Current11 human-review submissions."""

from __future__ import annotations

import copy
from typing import Any

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_submission_adapter_design_v1
    as design,
)


IMPLEMENTATION_VERSION = (
    "covapie_current11_warhead_boundary_review_submission_adapter_v1"
)
DESIGN_COMMIT = "84375060a0ddd9b281d17719331a316716bffd85"
DESIGN_PRODUCTION_SHA256 = (
    "55080fef4932d13be5fa063d3545c1120cb1e2bcaba20ab3cbe04a50b8838a58"
)
PUBLIC_FUNCTION_NAME = (
    "adapt_current11_warhead_boundary_review_submission_bundle_v1"
)

__all__ = (
    "adapt_current11_warhead_boundary_review_submission_bundle_v1",
)


def adapt_current11_warhead_boundary_review_submission_bundle_v1(
    *,
    source_payload: bytes,
) -> dict[str, Any]:
    """Adapt one exact-bytes submission bundle without authority effects."""

    source_snapshot = (
        copy.copy(source_payload) if type(source_payload) is bytes else None
    )
    response = design._reference_adapt_submission_bundle_v1(
        source_payload=source_payload,
    )
    if source_snapshot is not None and source_payload != source_snapshot:
        raise ValueError("ADAPTER_RESPONSE_INVARIANT_INVALID")
    return response
