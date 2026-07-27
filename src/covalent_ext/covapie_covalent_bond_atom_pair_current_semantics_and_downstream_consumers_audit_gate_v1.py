"""Pure current-semantics audit decision for the CovaPIE atom-pair label."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


__all__ = (
    "CovalentBondAtomPairCurrentSemanticsAuditDecision",
    "audit_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_v1",
    "serialize_covalent_bond_atom_pair_current_semantics_audit_decision",
)

SCHEMA_VERSION = "covapie_covalent_bond_atom_pair_current_semantics_audit_v1"
RECOMMENDED_NEXT_STEP = (
    "design_covapie_covalent_bond_atom_pair_encoding_contract_v1"
)


@dataclass(frozen=True)
class CovalentBondAtomPairCurrentSemanticsAuditDecision:
    """Audit result; an audited current state does not resolve the open issue."""

    schema_version: str
    outcome: str
    current_source_lineage_verified: bool
    current_representation_inventory_complete: bool
    current_consumer_inventory_complete: bool
    current_semantics_internally_consistent: bool
    explicit_bond_authority_verified: bool
    distance_only_inference_used: bool
    current_pair_is_metadata_string: bool
    current_pair_is_tensor_index_pair: bool
    current_dataloader_consumer_present: bool
    current_model_forward_consumer_present: bool
    current_loss_consumer_present: bool
    current_training_target_tensor_present: bool
    unresolved_semantics_inventory_complete: bool
    atom_pair_issue_resolved: bool
    ready_for_encoding_contract_design: bool
    feature_semantics_audit_completed: bool
    ready_for_training: bool
    recommended_next_step: str


def _decision(
    *,
    outcome: str,
    source_lineage: bool,
    representation: bool,
    consumers: bool,
    consistent: bool,
    explicit_authority: bool,
    distance_inference: bool,
    metadata_string: bool,
    tensor_index_pair: bool,
    dataloader: bool,
    forward: bool,
    loss: bool,
    training_target: bool,
    unresolved: bool,
    next_step: str,
) -> CovalentBondAtomPairCurrentSemanticsAuditDecision:
    audited = outcome == "audited"
    return CovalentBondAtomPairCurrentSemanticsAuditDecision(
        schema_version=SCHEMA_VERSION,
        outcome=outcome,
        current_source_lineage_verified=source_lineage,
        current_representation_inventory_complete=representation,
        current_consumer_inventory_complete=consumers,
        current_semantics_internally_consistent=consistent,
        explicit_bond_authority_verified=explicit_authority,
        distance_only_inference_used=distance_inference,
        current_pair_is_metadata_string=metadata_string,
        current_pair_is_tensor_index_pair=tensor_index_pair,
        current_dataloader_consumer_present=dataloader,
        current_model_forward_consumer_present=forward,
        current_loss_consumer_present=loss,
        current_training_target_tensor_present=training_target,
        unresolved_semantics_inventory_complete=unresolved,
        atom_pair_issue_resolved=False,
        ready_for_encoding_contract_design=audited,
        feature_semantics_audit_completed=False,
        ready_for_training=False,
        recommended_next_step=next_step,
    )


def audit_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_v1(
    *,
    current_source_lineage_verified: bool,
    current_representation_inventory_complete: bool,
    current_consumer_inventory_complete: bool,
    current_semantics_internally_consistent: bool,
    explicit_bond_authority_verified: bool,
    distance_only_inference_used: bool,
    current_pair_is_metadata_string: bool,
    current_pair_is_tensor_index_pair: bool,
    current_dataloader_consumer_present: bool,
    current_model_forward_consumer_present: bool,
    current_loss_consumer_present: bool,
    current_training_target_tensor_present: bool,
    unresolved_semantics_inventory_complete: bool,
) -> CovalentBondAtomPairCurrentSemanticsAuditDecision:
    """Return ``audited`` only for the exact, internally consistent BASE state."""
    values = (
        current_source_lineage_verified,
        current_representation_inventory_complete,
        current_consumer_inventory_complete,
        current_semantics_internally_consistent,
        explicit_bond_authority_verified,
        distance_only_inference_used,
        current_pair_is_metadata_string,
        current_pair_is_tensor_index_pair,
        current_dataloader_consumer_present,
        current_model_forward_consumer_present,
        current_loss_consumer_present,
        current_training_target_tensor_present,
        unresolved_semantics_inventory_complete,
    )
    if any(type(value) is not bool for value in values):
        raise TypeError("all audit evidence inputs must be exact bool values")
    expected = (
        True,
        True,
        True,
        True,
        True,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        True,
    )
    if values != expected:
        return _decision(
            outcome="invalid",
            source_lineage=current_source_lineage_verified,
            representation=current_representation_inventory_complete,
            consumers=current_consumer_inventory_complete,
            consistent=current_semantics_internally_consistent,
            explicit_authority=explicit_bond_authority_verified,
            distance_inference=distance_only_inference_used,
            metadata_string=current_pair_is_metadata_string,
            tensor_index_pair=current_pair_is_tensor_index_pair,
            dataloader=current_dataloader_consumer_present,
            forward=current_model_forward_consumer_present,
            loss=current_loss_consumer_present,
            training_target=current_training_target_tensor_present,
            unresolved=unresolved_semantics_inventory_complete,
            next_step=(
                "resolve_covalent_bond_atom_pair_current_semantics_audit_"
                "contradictions_v1"
            ),
        )
    return _decision(
        outcome="audited",
        source_lineage=True,
        representation=True,
        consumers=True,
        consistent=True,
        explicit_authority=True,
        distance_inference=False,
        metadata_string=True,
        tensor_index_pair=False,
        dataloader=False,
        forward=False,
        loss=False,
        training_target=False,
        unresolved=True,
        next_step=RECOMMENDED_NEXT_STEP,
    )


def serialize_covalent_bond_atom_pair_current_semantics_audit_decision(
    decision: CovalentBondAtomPairCurrentSemanticsAuditDecision,
) -> bytes:
    """Serialize a decision deterministically for byte-level comparison."""
    if type(decision) is not CovalentBondAtomPairCurrentSemanticsAuditDecision:
        raise TypeError("decision has the wrong exact type")
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
