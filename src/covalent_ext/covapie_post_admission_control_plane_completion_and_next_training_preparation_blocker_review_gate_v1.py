"""Pure post-admission completion and next-blocker selection review V1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


__all__ = (
    "PostAdmissionNextBlockerSelectionDecision",
    "DEPENDENCY_ORDER",
    "review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1",
    "serialize_post_admission_next_blocker_selection_decision",
)

SCHEMA_VERSION = (
    "covapie_post_admission_next_training_preparation_blocker_selection_v1"
)
ATOM_PAIR_BLOCKER = "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED"
PROVIDER_BLOCKER = "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"
SELECTED_NEXT_STEP = (
    "audit_covapie_covalent_bond_atom_pair_current_semantics_"
    "and_downstream_consumers_v1"
)
SELECTION_REASON = (
    "The atom-pair blocker is the semantic upstream dependency for the "
    "training label, feature-semantics audit, tensor/label contract, and "
    "future auxiliary pair task; its current state can be audited from "
    "committed evidence without provider execution. The provider-export "
    "rows remain open and fail-closed quarantined until the later real-data "
    "coverage step."
)
DEPENDENCY_ORDER = (
    "audit current covalent_bond_atom_pair semantics and all consumers",
    "freeze covalent bond atom-pair encoding contract",
    "validate encoding against existing canonical/real evidence",
    "resolve or quarantine real-provider export blocking rows under explicit policy",
    "perform feature-semantics audit",
    "freeze dataloader/tensor/label/loss-mask contracts",
    "begin first checkpoint-compatible auxiliary-module integration",
    "run no-parameter-update forward/loss smoke",
    "only then prepare formal training",
)


@dataclass(frozen=True)
class PostAdmissionNextBlockerSelectionDecision:
    """Closed review decision; selection never means issue resolution."""

    schema_version: str
    outcome: str
    control_plane_complete: bool
    selected_next_blocker: str
    deferred_blocker: str
    selection_reason: str
    selected_blocker_category: str
    deferred_blocker_category: str
    selected_next_step: str
    permission_layer_expansion_required: bool
    provider_execution_required_now: bool
    feature_semantics_audit_required_before_training: bool
    ready_for_download: bool
    ready_for_training: bool


def _invalid_decision(reason: str) -> PostAdmissionNextBlockerSelectionDecision:
    return PostAdmissionNextBlockerSelectionDecision(
        schema_version=SCHEMA_VERSION,
        outcome="invalid",
        control_plane_complete=False,
        selected_next_blocker="",
        deferred_blocker="",
        selection_reason=reason,
        selected_blocker_category="",
        deferred_blocker_category="",
        selected_next_step="",
        permission_layer_expansion_required=False,
        provider_execution_required_now=False,
        feature_semantics_audit_required_before_training=True,
        ready_for_download=False,
        ready_for_training=False,
    )


def review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1(
    *,
    control_plane_complete: bool,
    effective_open_issues: tuple[str, ...],
    atom_pair_evidence_verified: bool,
    provider_export_evidence_verified: bool,
) -> PostAdmissionNextBlockerSelectionDecision:
    """Select only when the independently supplied evidence is exact."""
    if type(control_plane_complete) is not bool:
        raise TypeError("control_plane_complete must be an exact bool")
    if type(effective_open_issues) is not tuple or any(
        type(item) is not str for item in effective_open_issues
    ):
        raise TypeError("effective_open_issues must be a tuple of exact str")
    if type(atom_pair_evidence_verified) is not bool:
        raise TypeError("atom_pair_evidence_verified must be an exact bool")
    if type(provider_export_evidence_verified) is not bool:
        raise TypeError("provider_export_evidence_verified must be an exact bool")
    if not control_plane_complete:
        return _invalid_decision("post-admission control plane is incomplete")
    if effective_open_issues != (ATOM_PAIR_BLOCKER, PROVIDER_BLOCKER):
        return _invalid_decision("effective-open issue set or order is not exact")
    if not atom_pair_evidence_verified:
        return _invalid_decision("atom-pair dependency evidence is incomplete")
    if not provider_export_evidence_verified:
        return _invalid_decision("provider-export continuity evidence is incomplete")
    return PostAdmissionNextBlockerSelectionDecision(
        schema_version=SCHEMA_VERSION,
        outcome="selected",
        control_plane_complete=True,
        selected_next_blocker=ATOM_PAIR_BLOCKER,
        deferred_blocker=PROVIDER_BLOCKER,
        selection_reason=SELECTION_REASON,
        selected_blocker_category="training_label_semantics",
        deferred_blocker_category="provider_export_data_availability",
        selected_next_step=SELECTED_NEXT_STEP,
        permission_layer_expansion_required=False,
        provider_execution_required_now=False,
        feature_semantics_audit_required_before_training=True,
        ready_for_download=False,
        ready_for_training=False,
    )


def serialize_post_admission_next_blocker_selection_decision(
    decision: PostAdmissionNextBlockerSelectionDecision,
) -> bytes:
    """Serialize a decision deterministically for evidence comparison."""
    if type(decision) is not PostAdmissionNextBlockerSelectionDecision:
        raise TypeError("decision has the wrong exact type")
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
