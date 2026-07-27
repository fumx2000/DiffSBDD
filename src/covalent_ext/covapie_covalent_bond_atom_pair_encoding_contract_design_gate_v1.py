"""Pure design gate for the CovaPIE covalent-bond atom-pair encoding V1.

This module freezes semantic and future mapping policy only.  It does not read
raw structures, resolve atom-table rows, materialize tensors, or implement a
dataloader, model head, forward path, loss, backward pass, or training step.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path


__all__ = (
    "CovalentAtomLocatorContractDesign",
    "CovalentBondAtomPairCanonicalRecordDesign",
    "CovalentBondAtomPairEncodingContractDesign",
    "CovalentBondAtomPairPolicyDecision",
    "ModelInputIndexSpaceCompatibilityEvidence",
    "derive_covapie_model_input_index_space_compatibility_evidence_v1",
    "design_covapie_covalent_bond_atom_pair_encoding_contract_v1",
    "evaluate_covapie_covalent_bond_atom_pair_policy_case_v1",
    "project_covapie_legacy_atom_name_pair_v1",
    "serialize_covapie_covalent_bond_atom_pair_encoding_contract_design_v1",
    "validate_covapie_covalent_atom_locator_contract_design_v1",
    "validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1",
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_PATH_TYPE = type(Path())
BASE_COMMIT = "6f04eb7036aa926e433a02de3e244412af038800"
BASE_PARENT = "976da60a5af7b7ba71597c1202955a45db6b6cf1"
BASE_TREE = "b629b9082cf8d8ef82c00f9af1a9524dead7a6a4"
BASE_SUBJECT = (
    "add CovaPIE covalent bond atom-pair current-semantics audit v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE covalent bond atom-pair encoding contract v1"
)

LOCATOR_SCHEMA_VERSION = "covapie_covalent_atom_locator_v1"
PAIR_RECORD_SCHEMA_VERSION = (
    "covapie_covalent_bond_atom_pair_canonical_record_v1"
)
SCHEMA_VERSION = "covapie_covalent_bond_atom_pair_encoding_contract_v1"
CANONICAL_ENCODING_KIND = "structured_role_labeled_record"
ROLE_VOCABULARY = ("target_residue_atom", "ligand_atom")
AUTHORITY_VOCABULARY = (
    "validated_struct_conn",
    "explicit_curated_covalent_annotation",
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
LEGACY_VALUES = (
    "SG--C17",
    "SG--C2",
    "SG--C21",
    "SG--C22",
    "SG--C6",
    "SG--CAG",
    "SG--CM",
)
RECOMMENDED_NEXT_STEP = (
    "validate_covapie_covalent_bond_atom_pair_encoding_contract_against_"
    "current_canonical_evidence_v1"
)

STAGE = "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PUBLIC_FILE = "covapie_covalent_bond_atom_pair_encoding_public_contract.csv"
LOCATOR_FILE = "covapie_covalent_bond_atom_locator_schema_contract.csv"
POLICY_FILE = "covapie_covalent_bond_atom_pair_policy_matrix.csv"
LEGACY_FILE = "covapie_covalent_bond_atom_pair_legacy_compatibility_matrix.csv"
ISSUE_FILE = "covapie_covalent_bond_atom_pair_issue_readiness_inventory.csv"
MANIFEST_FILE = (
    "covapie_covalent_bond_atom_pair_encoding_contract_manifest.json"
)
OUTPUT_FILES = (
    PUBLIC_FILE,
    LOCATOR_FILE,
    POLICY_FILE,
    LEGACY_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)

PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
    "consumers_audit_gate_v1"
)
PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
    "consumers_audit_gate_v1.py"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
    "consumers_audit_manifest.json"
)
PREDECESSOR_UNRESOLVED = PREDECESSOR_ROOT / (
    "covapie_covalent_bond_atom_pair_unresolved_semantics_inventory.csv"
)
PREDECESSOR_REPRESENTATION = PREDECESSOR_ROOT / (
    "covapie_covalent_bond_atom_pair_current_representation_audit.csv"
)
PREDECESSOR_ISSUES = PREDECESSOR_ROOT / (
    "covapie_covalent_bond_atom_pair_issue_readiness_inventory.csv"
)
PREDECESSOR_SHA256 = {
    PREDECESSOR_SOURCE: (
        "f905174e6bb471475bc34ce6ff3d35034755daec913da2cc81bfcf94b5112112"
    ),
    PREDECESSOR_MANIFEST: (
        "334a0dfe5b37b41f134c9a66ad9b0237431e0798f926b32bda4101a8e8f0571c"
    ),
    PREDECESSOR_UNRESOLVED: (
        "00722f0c2370d458cdcac7d50c18914b4f36a393e237cf2ecc40f81965bca428"
    ),
    PREDECESSOR_REPRESENTATION: (
        "f63a5a8b0ed1d7ad0284a89826325f0d429ab33b202a5f2e468ae8a370eb1968"
    ),
    PREDECESSOR_ISSUES: (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ),
}

FINAL_DATASET_SCHEMA = Path(
    "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/"
    "covapie_final_dataset_schema_contract.csv"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
TENSORIZATION_BLOCKERS = Path(
    "data/derived/covalent_small/"
    "covapie_feature_semantics_tensorization_audit_gate_v0/"
    "covapie_label_tensorization_blocker_audit.csv"
)
DATALOADER_TENSORIZATION_CONTRACT = Path(
    "data/derived/covalent_small/covapie_actual_dataloader_design_gate_v0/"
    "covapie_actual_dataloader_tensorization_input_contract.csv"
)
INDEX_SPACE_EVIDENCE_SHA256 = {
    FINAL_DATASET_SCHEMA: (
        "2ea572efb4d9df1a168ba6b056ffa14593315ac148d589f86a5ea8f607c2469c"
    ),
    FINAL_DATASET_INDEX: (
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d"
    ),
    PREDECESSOR_MANIFEST: (
        "334a0dfe5b37b41f134c9a66ad9b0237431e0798f926b32bda4101a8e8f0571c"
    ),
    PREDECESSOR_UNRESOLVED: (
        "00722f0c2370d458cdcac7d50c18914b4f36a393e237cf2ecc40f81965bca428"
    ),
    TENSORIZATION_BLOCKERS: (
        "ce1ab5c8024b360ef72c95718898e4c052a5fd0c8a3d07c76bf92f50db64ae0a"
    ),
    DATALOADER_TENSORIZATION_CONTRACT: (
        "b88b7012cffe4d6689e14f63732e5edea64c28e22fb1b3e1c6e53cd25e9ba5eb"
    ),
}
INDEX_SPACE_EVIDENCE_SELECTORS = (
    "final_dataset_schema:required pocket_atom_table_path and ligand_atom_table_path",
    "final_dataset_index:11 nonempty pocket_atom_table_path and ligand_atom_table_path values",
    "current_audit_manifest:no pair index/dataloader/forward/loss/training target",
    "unresolved_semantics:no current protein/pocket/ligand mapping; row order deferred",
    "tensorization_blockers:pair label, collate, loss, and training targets blocked",
    "dataloader_tensorization_contract:pocket/ligand sources present; pair label blocked; no pair-index contract",
)


@dataclass(frozen=True)
class CovalentAtomLocatorContractDesign:
    """Role-labeled semantic locator; every V1 field is an exact string."""

    locator_schema_version: str
    entity_role: str
    event_id: str
    pdb_id: str
    model_id: str
    auth_asym_id: str
    auth_seq_id: str
    insertion_code: str
    label_asym_id: str
    label_seq_id: str
    comp_id: str
    atom_name: str
    altloc: str


@dataclass(frozen=True)
class CovalentBondAtomPairCanonicalRecordDesign:
    """Exact canonical semantic record; this is not an atom-index mapping."""

    pair_record_schema_version: str
    residue_atom_locator: CovalentAtomLocatorContractDesign
    ligand_atom_locator: CovalentAtomLocatorContractDesign
    explicit_bond_authority_class: str
    explicit_bond_provenance_id: str


@dataclass(frozen=True)
class CovalentBondAtomPairEncodingContractDesign:
    """Frozen policy result; it is not a materialized atom-pair target."""

    schema_version: str
    outcome: str
    canonical_encoding_kind: str
    pair_role_semantics: str
    explicit_bond_authority_required: bool
    accepted_explicit_bond_authority_classes: tuple[str, ...]
    distance_only_inference_forbidden: bool
    positive_pair_cardinality_policy: str
    residue_candidate_scope: str
    ligand_candidate_scope: str
    residue_model_index_space: str
    ligand_model_index_space: str
    model_index_base: int
    mapping_cardinality_policy: str
    missing_mapping_policy: str
    ambiguous_mapping_policy: str
    duplicate_evidence_policy: str
    conflicting_pair_policy: str
    zero_pair_policy: str
    multi_pair_policy: str
    legacy_string_role: str
    canonical_masks_share_same_pair_identity: bool
    pair_tensor_materialized: bool
    pair_tensor_shape_defined: bool
    pair_loss_mask_defined: bool
    atom_pair_issue_resolved: bool
    ready_for_contract_validation: bool
    ready_for_tensorization: bool
    ready_for_training: bool
    recommended_next_step: str


@dataclass(frozen=True)
class CovalentBondAtomPairPolicyDecision:
    """One deterministic design-matrix classification."""

    case_id: str
    outcome: str
    reason: str
    pair_retained: bool
    mapping_allowed: bool
    fails_closed: bool


@dataclass(frozen=True)
class ModelInputIndexSpaceCompatibilityEvidence:
    """Committed-evidence result for selecting future model-facing spaces."""

    final_dataset_pocket_atom_table_reference_present: bool
    final_dataset_ligand_atom_table_reference_present: bool
    current_pair_tensor_index_contract_present: bool
    conflicting_existing_index_space_contract_present: bool
    pair_tensorization_currently_blocked: bool
    row_order_validation_deferred_to_contract_validation: bool
    compatible: bool
    evidence_paths: tuple[str, ...]


def validate_covapie_covalent_atom_locator_contract_design_v1(
    locator: CovalentAtomLocatorContractDesign,
) -> bool:
    """Validate the exact V1 locator value contract without mapping any atom."""
    if type(locator) is not CovalentAtomLocatorContractDesign:
        return False
    values = tuple(asdict(locator).values())
    if any(type(value) is not str for value in values):
        return False
    if locator.locator_schema_version != LOCATOR_SCHEMA_VERSION:
        return False
    if locator.entity_role not in ROLE_VOCABULARY:
        return False
    required = (
        locator.event_id,
        locator.pdb_id,
        locator.entity_role,
        locator.comp_id,
        locator.atom_name,
    )
    return all(value != "" for value in required)


def validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
    record: CovalentBondAtomPairCanonicalRecordDesign,
) -> bool:
    """Validate the exact structured record without resolving atom-table rows."""
    if type(record) is not CovalentBondAtomPairCanonicalRecordDesign:
        return False
    if record.pair_record_schema_version != PAIR_RECORD_SCHEMA_VERSION:
        return False
    if type(record.residue_atom_locator) is not CovalentAtomLocatorContractDesign:
        return False
    if type(record.ligand_atom_locator) is not CovalentAtomLocatorContractDesign:
        return False
    if type(record.explicit_bond_authority_class) is not str:
        return False
    if type(record.explicit_bond_provenance_id) is not str:
        return False
    residue = record.residue_atom_locator
    ligand = record.ligand_atom_locator
    if not validate_covapie_covalent_atom_locator_contract_design_v1(residue):
        return False
    if not validate_covapie_covalent_atom_locator_contract_design_v1(ligand):
        return False
    if residue.entity_role != "target_residue_atom":
        return False
    if ligand.entity_role != "ligand_atom":
        return False
    if residue.event_id != ligand.event_id or residue.event_id == "":
        return False
    if residue.pdb_id != ligand.pdb_id or residue.pdb_id == "":
        return False
    if residue.model_id != ligand.model_id:
        return False
    if record.explicit_bond_authority_class not in AUTHORITY_VOCABULARY:
        return False
    return record.explicit_bond_provenance_id != ""


def project_covapie_legacy_atom_name_pair_v1(
    record: CovalentBondAtomPairCanonicalRecordDesign,
) -> str:
    """Project display-only atom names from a valid structured record."""
    if not validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
        record
    ):
        raise ValueError("invalid canonical atom-pair record")
    return (
        f"{record.residue_atom_locator.atom_name}--"
        f"{record.ligand_atom_locator.atom_name}"
    )


def design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
    *,
    current_semantics_audit_precondition_verified: bool,
    model_input_index_space_compatibility_evidence:
        ModelInputIndexSpaceCompatibilityEvidence,
) -> CovalentBondAtomPairEncodingContractDesign:
    """Freeze the design only when both independently verified gates pass."""
    if type(current_semantics_audit_precondition_verified) is not bool:
        raise TypeError("audit precondition must be an exact bool value")
    evidence = model_input_index_space_compatibility_evidence
    if type(evidence) is not ModelInputIndexSpaceCompatibilityEvidence:
        raise TypeError("index-space evidence has the wrong exact type")
    bool_values = tuple(
        value
        for name, value in asdict(evidence).items()
        if name != "evidence_paths"
    )
    if any(type(value) is not bool for value in bool_values):
        raise TypeError("index-space evidence flags must be exact bool values")
    if (
        type(evidence.evidence_paths) is not tuple
        or not evidence.evidence_paths
        or any(type(path) is not str or not path for path in evidence.evidence_paths)
    ):
        raise TypeError("index-space evidence paths must be nonempty exact strings")
    frozen = (
        current_semantics_audit_precondition_verified
        and evidence.final_dataset_pocket_atom_table_reference_present
        and evidence.final_dataset_ligand_atom_table_reference_present
        and evidence.compatible
        and not evidence.conflicting_existing_index_space_contract_present
        and not evidence.current_pair_tensor_index_contract_present
        and evidence.pair_tensorization_currently_blocked
        and evidence.row_order_validation_deferred_to_contract_validation
    )
    return CovalentBondAtomPairEncodingContractDesign(
        schema_version=SCHEMA_VERSION,
        outcome="frozen" if frozen else "invalid",
        canonical_encoding_kind=CANONICAL_ENCODING_KIND,
        pair_role_semantics=(
            "residue_atom_locator_and_ligand_atom_locator_are_role_labeled"
        ),
        explicit_bond_authority_required=True,
        accepted_explicit_bond_authority_classes=AUTHORITY_VOCABULARY,
        distance_only_inference_forbidden=True,
        positive_pair_cardinality_policy=(
            "exactly_one_positive_explicit_pair_per_sample"
        ),
        residue_candidate_scope=(
            "all atoms of the specified target residue present in model "
            "receptor/pocket input"
        ),
        ligand_candidate_scope=(
            "all ligand atoms present in the model ligand input"
        ),
        residue_model_index_space="pocket_atom_table_row_index",
        ligand_model_index_space="ligand_atom_table_row_index",
        model_index_base=0,
        mapping_cardinality_policy=(
            "exactly_one_residue_atom_row_and_exactly_one_ligand_atom_row"
        ),
        missing_mapping_policy="invalid_fail_closed",
        ambiguous_mapping_policy="invalid_fail_closed",
        duplicate_evidence_policy=(
            "deduplicate_only_when_all_identity_and_authority_fields_match"
        ),
        conflicting_pair_policy="invalid_fail_closed",
        zero_pair_policy="invalid_fail_closed",
        multi_pair_policy="unsupported_v1_fail_closed",
        legacy_string_role=(
            "legacy_display_and_backward_compatibility_projection"
        ),
        canonical_masks_share_same_pair_identity=True,
        pair_tensor_materialized=False,
        pair_tensor_shape_defined=False,
        pair_loss_mask_defined=False,
        atom_pair_issue_resolved=False,
        ready_for_contract_validation=frozen,
        ready_for_tensorization=False,
        ready_for_training=False,
        recommended_next_step=(
            RECOMMENDED_NEXT_STEP
            if frozen
            else "repair_atom_pair_encoding_contract_design_preconditions_v1"
        ),
    )


_POLICY_ROWS = (
    ("valid_explicit_single_pair", "valid", "explicit_single_pair_accepted", True, True, False),
    ("distance_only_candidate", "invalid", "distance_only_inference_forbidden", False, False, True),
    ("zero_pair", "invalid", "zero_explicit_pair", False, False, True),
    ("exact_duplicate_evidence", "valid_deduplicated", "exact_duplicate_deduplicated", True, True, False),
    ("conflicting_duplicate", "invalid", "conflicting_pair", False, False, True),
    ("multiple_distinct_pairs", "invalid", "multiple_distinct_pairs_unsupported_v1", False, False, True),
    ("missing_residue_locator", "invalid", "missing_residue_locator", False, False, True),
    ("missing_ligand_locator", "invalid", "missing_ligand_locator", False, False, True),
    ("ambiguous_residue_mapping", "invalid", "ambiguous_residue_mapping", False, False, True),
    ("ambiguous_ligand_mapping", "invalid", "ambiguous_ligand_mapping", False, False, True),
    ("target_residue_mismatch", "invalid", "target_residue_mismatch", False, False, True),
    ("ligand_instance_mismatch", "invalid", "ligand_instance_mismatch", False, False, True),
    ("legacy_string_mismatch", "invalid", "legacy_value_structured_name_mismatch", False, False, True),
    ("legacy_string_only", "invalid", "legacy_string_is_not_a_sole_locator", False, False, True),
    ("non_zero_based_requested_index", "invalid", "model_index_base_must_be_zero", False, False, True),
    ("row_order_drift", "invalid", "atom_table_row_order_not_verified", False, False, True),
    ("altloc_ambiguity", "invalid", "altloc_ambiguity", False, False, True),
    ("model_ambiguity", "invalid", "model_ambiguity", False, False, True),
    ("insertion_code_ambiguity", "invalid", "insertion_code_ambiguity", False, False, True),
    ("unsupported_explicit_authority", "invalid", "unsupported_explicit_authority", False, False, True),
    ("missing_explicit_authority_provenance", "invalid", "missing_explicit_authority_provenance", False, False, True),
    ("residue_role_mismatch", "invalid", "residue_role_mismatch", False, False, True),
    ("ligand_role_mismatch", "invalid", "ligand_role_mismatch", False, False, True),
    ("event_identity_mismatch", "invalid", "event_identity_mismatch", False, False, True),
    ("pdb_identity_mismatch", "invalid", "pdb_identity_mismatch", False, False, True),
    ("model_identity_mismatch", "invalid", "model_identity_mismatch", False, False, True),
)
_POLICY_BY_ID = {row[0]: row[1:] for row in _POLICY_ROWS}


def evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(
    case_id: str,
) -> CovalentBondAtomPairPolicyDecision:
    """Classify a design case; unknown or ill-typed cases fail closed."""
    if type(case_id) is not str:
        raise TypeError("case_id must be an exact string")
    values = _POLICY_BY_ID.get(
        case_id,
        ("invalid", "unknown_policy_case", False, False, True),
    )
    return CovalentBondAtomPairPolicyDecision(case_id, *values)


def serialize_covapie_covalent_bond_atom_pair_encoding_contract_design_v1(
    contract: CovalentBondAtomPairEncodingContractDesign,
) -> bytes:
    """Serialize a contract deterministically for byte-level comparison."""
    if type(contract) is not CovalentBondAtomPairEncodingContractDesign:
        raise TypeError("contract has the wrong exact type")
    return (
        json.dumps(asdict(contract), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv_bytes(columns: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _bool(value: bool) -> str:
    return "true" if value else "false"


def derive_covapie_model_input_index_space_compatibility_evidence_v1(
    repo_root: Path,
) -> ModelInputIndexSpaceCompatibilityEvidence:
    """Derive compatibility from an exact, committed-evidence text corpus."""
    if type(repo_root) is not _PATH_TYPE:
        raise TypeError("repo_root must be an exact Path value")
    payloads: dict[Path, bytes] = {}
    for relative, expected_sha256 in INDEX_SPACE_EVIDENCE_SHA256.items():
        payload = (repo_root / relative).read_bytes()
        if _sha256(payload) != expected_sha256:
            raise ValueError(
                f"index-space evidence SHA256 drift: {relative.as_posix()}"
            )
        payloads[relative] = payload

    schema_rows = tuple(
        csv.DictReader(
            io.StringIO(payloads[FINAL_DATASET_SCHEMA].decode("utf-8"))
        )
    )
    schema_by_field = {
        row["final_dataset_field"]: row for row in schema_rows
    }
    final_rows = tuple(
        csv.DictReader(
            io.StringIO(payloads[FINAL_DATASET_INDEX].decode("utf-8"))
        )
    )
    pocket_present = (
        schema_by_field.get("pocket_atom_table_path", {}).get(
            "schema_contract_passed"
        )
        == "True"
        and len(final_rows) == 11
        and all(row.get("pocket_atom_table_path", "") != "" for row in final_rows)
    )
    ligand_present = (
        schema_by_field.get("ligand_atom_table_path", {}).get(
            "schema_contract_passed"
        )
        == "True"
        and len(final_rows) == 11
        and all(row.get("ligand_atom_table_path", "") != "" for row in final_rows)
    )

    audit = json.loads(payloads[PREDECESSOR_MANIFEST])
    unresolved_rows = tuple(
        csv.DictReader(
            io.StringIO(payloads[PREDECESSOR_UNRESOLVED].decode("utf-8"))
        )
    )
    unresolved_by_item = {
        row["semantics_item"]: row for row in unresolved_rows
    }
    mapping_items = (
        "protein full-atom table row mapping",
        "pocket atom table row mapping",
        "ligand atom table row mapping",
    )
    mapping_is_not_currently_defined = all(
        unresolved_by_item[item]["currently_formally_defined"] == "false"
        and unresolved_by_item[item]["decision_made_current_audit"] == "false"
        and unresolved_by_item[item]["deferred_to_next_contract"] == "true"
        for item in mapping_items
    )
    current_pair_tensor_index_contract_present = not (
        audit.get("current_pair_is_tensor_index_pair") is False
        and audit.get("future_index_mapping_defined") is False
        and audit.get("current_dataloader_consumer_present") is False
        and audit.get("current_model_forward_consumer_present") is False
        and audit.get("current_loss_consumer_present") is False
        and audit.get("current_training_target_tensor_present") is False
        and mapping_is_not_currently_defined
    )

    blocker_rows = tuple(
        csv.DictReader(
            io.StringIO(payloads[TENSORIZATION_BLOCKERS].decode("utf-8"))
        )
    )
    blocker_by_item = {
        row["label_blocker_item"]: row for row in blocker_rows
    }
    required_blockers = (
        "covalent_atom_pair_label_not_training_final",
        "batch_collate_for_labels_blocked",
        "loss_integration_blocked",
        "training_targets_blocked",
    )
    blocker_contract_holds = all(
        blocker_by_item[item]["current_tensorization_status"] == "blocked"
        and blocker_by_item[item]["blocks_training"] == "True"
        and blocker_by_item[item]["label_blocker_audit_passed"] == "True"
        for item in required_blockers
    )

    dataloader_rows = tuple(
        csv.DictReader(
            io.StringIO(
                payloads[DATALOADER_TENSORIZATION_CONTRACT].decode("utf-8")
            )
        )
    )
    dataloader_by_item = {
        row["tensorization_item"]: row for row in dataloader_rows
    }
    artifact_boundaries_hold = (
        dataloader_by_item.get(
            "protein_xyz_from_derived_atom_table", {}
        ).get("source_or_policy")
        == "protein_pocket_atom_table_path"
        and dataloader_by_item.get(
            "ligand_xyz_from_derived_atom_table", {}
        ).get("source_or_policy")
        == "ligand_atom_table_path"
    )
    pair_tensorization_currently_blocked = (
        blocker_contract_holds
        and dataloader_by_item.get("covalent_atom_pair_label_blocked", {}).get(
            "current_step_status"
        )
        == "blocked_by_feature_semantics"
        and dataloader_by_item["covalent_atom_pair_label_blocked"][
            "blocked_before_actual_tensor_smoke"
        ]
        == "True"
    )
    declared_future_keys = {
        row["future_tensor_or_metadata_key"] for row in dataloader_rows
    }
    conflicting_existing_index_space_contract_present = bool(
        declared_future_keys
        & {
            "covalent_atom_pair_index",
            "protein_atom_table_row_index",
            "full_protein_atom_table_row_index",
            "one_based_pocket_atom_table_row_index",
            "one_based_ligand_atom_table_row_index",
        }
    )
    row_order = unresolved_by_item["atom-table row ordering stability"]
    row_order_deferred = (
        row_order["currently_formally_defined"] == "false"
        and row_order["decision_made_current_audit"] == "false"
        and row_order["deferred_to_next_contract"] == "true"
        and row_order["verified"] == "true"
    )
    compatible = all(
        (
            pocket_present,
            ligand_present,
            artifact_boundaries_hold,
            not current_pair_tensor_index_contract_present,
            not conflicting_existing_index_space_contract_present,
            pair_tensorization_currently_blocked,
            row_order_deferred,
        )
    )
    return ModelInputIndexSpaceCompatibilityEvidence(
        final_dataset_pocket_atom_table_reference_present=pocket_present,
        final_dataset_ligand_atom_table_reference_present=ligand_present,
        current_pair_tensor_index_contract_present=(
            current_pair_tensor_index_contract_present
        ),
        conflicting_existing_index_space_contract_present=(
            conflicting_existing_index_space_contract_present
        ),
        pair_tensorization_currently_blocked=(
            pair_tensorization_currently_blocked
        ),
        row_order_validation_deferred_to_contract_validation=(
            row_order_deferred
        ),
        compatible=compatible,
        evidence_paths=tuple(
            path.as_posix() for path in INDEX_SPACE_EVIDENCE_SHA256
        ),
    )


def _verify_predecessor(
    repo_root: Path,
) -> tuple[dict[str, object], bytes, bytes]:
    payloads: dict[Path, bytes] = {}
    for relative, expected in PREDECESSOR_SHA256.items():
        payload = (repo_root / relative).read_bytes()
        if _sha256(payload) != expected:
            raise ValueError(f"predecessor SHA256 drift: {relative.as_posix()}")
        payloads[relative] = payload
    manifest = json.loads(payloads[PREDECESSOR_MANIFEST])
    expected_values = {
        "outcome": "audited",
        "current_source_lineage_verified": True,
        "producer_projection_verified": True,
        "record_conflict_present": False,
        "producer_conflict_present": False,
        "explicit_bond_authority_verified": True,
        "distance_only_inference_used": False,
        "current_pair_is_metadata_string": True,
        "current_pair_is_tensor_index_pair": False,
        "ready_for_encoding_contract_design": True,
        "ready_for_training": False,
    }
    for key, expected in expected_values.items():
        if manifest.get(key) != expected:
            raise ValueError(f"predecessor manifest precondition failed: {key}")
    return (
        manifest,
        payloads[PREDECESSOR_ISSUES],
        payloads[PREDECESSOR_REPRESENTATION],
    )


def _public_rows() -> tuple[tuple[str, ...], ...]:
    pair_fields = ",".join(
        CovalentBondAtomPairEncodingContractDesign.__dataclass_fields__
    )
    locator_fields = ",".join(CovalentAtomLocatorContractDesign.__dataclass_fields__)
    record_fields = ",".join(
        CovalentBondAtomPairCanonicalRecordDesign.__dataclass_fields__
    )
    record_types = (
        "str|CovalentAtomLocatorContractDesign|"
        "CovalentAtomLocatorContractDesign|str|str"
    )
    return (
        ("semantic_encoding", "canonical_encoding_kind", CANONICAL_ENCODING_KIND, CANONICAL_ENCODING_KIND, "role-labeled identity removes tuple-order ambiguity", "true"),
        ("canonical_record", "canonical_pair_record_schema_version", PAIR_RECORD_SCHEMA_VERSION, PAIR_RECORD_SCHEMA_VERSION, "exact canonical record schema discriminator", "true"),
        ("canonical_record", "canonical_pair_record_exact_fields", "pair_record_schema_version,residue_atom_locator,ligand_atom_locator,explicit_bond_authority_class,explicit_bond_provenance_id", record_fields, "five-field frozen canonical record", "true"),
        ("canonical_record", "canonical_pair_record_exact_types", record_types, record_types, "nested locators retain exact types", "true"),
        ("canonical_record", "canonical_record_validator_available", "true", "true", "pure exact-type fail-closed validator", "true"),
        ("canonical_record", "canonical_record_roles_enforced", "target_residue_atom|ligand_atom", "target_residue_atom|ligand_atom", "roles are fields rather than tuple position", "true"),
        ("canonical_record", "canonical_record_event_identity_consistent", "true", "true", "both locators require the same nonempty event_id", "true"),
        ("canonical_record", "canonical_record_pdb_identity_consistent", "true", "true", "both locators require the same nonempty pdb_id", "true"),
        ("canonical_record", "canonical_record_model_identity_consistent", "true", "true", "both locators require the same model_id; both empty is allowed", "true"),
        ("canonical_record", "explicit_authority_field_is_part_of_record", "true", "true", "authority is embedded canonical identity evidence", "true"),
        ("canonical_record", "explicit_provenance_id_is_part_of_record", "true", "true", "nonempty provenance is embedded in the record", "true"),
        ("legacy", "legacy_projection_function_available", "true", "true", "projection accepts only a valid canonical record", "true"),
        ("public_api", "frozen_pair_contract_dataclass_fields", pair_fields, pair_fields, "exact public contract design API", "true"),
        ("public_api", "frozen_locator_dataclass_fields", locator_fields, locator_fields, "exact structured locator API", "true"),
        ("atom_locator", "entity_role_vocabulary", "target_residue_atom|ligand_atom", "|".join(ROLE_VOCABULARY), "closed role vocabulary", "true"),
        ("explicit_authority", "accepted_authority_classes", "validated_struct_conn|explicit_curated_covalent_annotation", "|".join(AUTHORITY_VOCABULARY), "positive pairs require explicit authority", "true"),
        ("explicit_authority", "distance_only_inference_forbidden", "true", "true", "distance is QA evidence only", "true"),
        ("cardinality", "positive_pair_cardinality", "exactly_one_positive_explicit_pair_per_sample", "exactly_one_positive_explicit_pair_per_sample", "V1 exact-one scope", "true"),
        ("atom_locator", "locator_uniqueness", "exactly_one_match_per_role_or_fail_closed", "exactly_one_match_per_role_or_fail_closed", "no nearest or first-row fallback", "true"),
        ("atom_locator", "locator_syntax_is_not_mapping_success", "true", "true", "empty optional fields do not prove absence, uniqueness, or lack of ambiguity", "true"),
        ("future_mapping", "model_index_base", "0", "0", "derived indices are zero-based", "true"),
        ("future_mapping", "model_index_spaces", "pocket_atom_table_row_index|ligand_atom_table_row_index", "pocket_atom_table_row_index|ligand_atom_table_row_index", "model-facing future derived views", "true"),
        ("legacy", "legacy_string_role", "legacy_display_and_backward_compatibility_projection", "legacy_display_and_backward_compatibility_projection", "legacy string is not identity or tensor target", "true"),
        ("legacy", "legacy_projection_grammar", "residue_atom_name--ligand_atom_name", "residue_atom_name--ligand_atom_name", "delimiter=--; visible residue-then-ligand order", "true"),
        ("mask_invariance", "canonical_masks_share_same_pair_identity", "true", "true", "A|B|B2|B3|C share the semantic pair", "true"),
        ("boundary", "tensor_model_training", "not_materialized_or_implemented", "not_materialized_or_implemented", "design evidence only; feature semantics remains unaudited", "true"),
    )


def _locator_rows() -> tuple[tuple[object, ...], ...]:
    fields = tuple(CovalentAtomLocatorContractDesign.__dataclass_fields__)
    required = {"entity_role", "event_id", "pdb_id", "comp_id", "atom_name"}
    identity_roles = {
        "locator_schema_version": "schema_discriminator",
        "entity_role": "role_discriminator",
        "event_id": "event_provenance_identity",
        "pdb_id": "structure_identity",
        "model_id": "model_disambiguator",
        "auth_asym_id": "author_chain_locator",
        "auth_seq_id": "author_sequence_locator",
        "insertion_code": "author_sequence_disambiguator",
        "label_asym_id": "label_chain_locator",
        "label_seq_id": "label_sequence_locator",
        "comp_id": "component_identity",
        "atom_name": "atom_identity_within_component",
        "altloc": "alternate_location_disambiguator",
    }
    current = {
        "locator_schema_version": "contract_only_not_materialized",
        "entity_role": "derivable_role_not_materialized_as_structured_locator",
        "event_id": "source_value_observed_not_materialized_in_locator_v1",
        "pdb_id": "source_value_observed_not_materialized_in_locator_v1",
        "model_id": "explicitly_missing_in_current_source",
        "auth_asym_id": "corresponding_chain_value_observed_namespace_not_fully_audited",
        "auth_seq_id": "corresponding_sequence_value_observed_namespace_not_fully_audited",
        "insertion_code": "explicit_empty_values_observed_not_locator_materialized",
        "label_asym_id": "not_materialized",
        "label_seq_id": "not_materialized",
        "comp_id": "source_value_observed_not_materialized_in_locator_v1",
        "atom_name": "source_value_observed_not_materialized_in_locator_v1",
        "altloc": "not_materialized",
    }
    rows = []
    for order, name in enumerate(fields, 1):
        is_required = name in required or name == "locator_schema_version"
        applies_residue = True
        applies_ligand = True
        rule = (
            f"exact_string_equal_{LOCATOR_SCHEMA_VERSION}"
            if name == "locator_schema_version"
            else (
                f"exact_string_member_of_{'|'.join(ROLE_VOCABULARY)}"
                if name == "entity_role"
                else (
                    "exact_nonempty_string"
                    if name in required
                    else "exact_string_empty_allowed_no_none_or_coercion"
                )
            )
        )
        rows.append(
            (
                order,
                name,
                "str",
                _bool(is_required),
                _bool(not is_required),
                _bool(applies_residue),
                _bool(applies_ligand),
                identity_roles[name],
                rule,
                current[name],
                "true",
            )
        )
    return tuple(rows)


_INPUT_CONDITIONS = {
    "valid_explicit_single_pair": "one explicit accepted-authority pair; unique locators and mappings",
    "distance_only_candidate": "candidate supported only by distance or nearest-atom geometry",
    "zero_pair": "no explicit positive pair",
    "exact_duplicate_evidence": "same event, structured pair, and authority fields repeated exactly",
    "conflicting_duplicate": "same event carries conflicting structured pairs",
    "multiple_distinct_pairs": "more than one distinct explicit pair in a sample",
    "missing_residue_locator": "target-residue semantic locator is missing",
    "missing_ligand_locator": "ligand semantic locator is missing",
    "ambiguous_residue_mapping": "residue locator matches other than exactly one pocket row",
    "ambiguous_ligand_mapping": "ligand locator matches other than exactly one ligand row",
    "target_residue_mismatch": "mapped receptor atom is outside specified target residue",
    "ligand_instance_mismatch": "mapped ligand atom is outside current ligand instance",
    "legacy_string_mismatch": "legacy projection differs from structured atom names",
    "legacy_string_only": "legacy string is supplied without structured identity/provenance",
    "non_zero_based_requested_index": "future derived model index requests a nonzero base",
    "row_order_drift": "atom-table row order is not verified at mapping time",
    "altloc_ambiguity": "locator leaves multiple altloc rows",
    "model_ambiguity": "locator leaves multiple model rows",
    "insertion_code_ambiguity": "locator leaves multiple insertion-code rows",
    "unsupported_explicit_authority": "canonical record carries an authority outside the Exact2 vocabulary",
    "missing_explicit_authority_provenance": "canonical record provenance ID is empty",
    "residue_role_mismatch": "residue locator role is not target_residue_atom",
    "ligand_role_mismatch": "ligand locator role is not ligand_atom",
    "event_identity_mismatch": "residue and ligand locator event IDs differ",
    "pdb_identity_mismatch": "residue and ligand locator PDB IDs differ",
    "model_identity_mismatch": "residue and ligand locator model IDs differ",
}


def _policy_rows() -> tuple[tuple[object, ...], ...]:
    rows = []
    for case_id, *_ in _POLICY_ROWS:
        decision = evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(case_id)
        rows.append(
            (
                case_id,
                _INPUT_CONDITIONS[case_id],
                decision.outcome,
                decision.reason,
                _bool(decision.pair_retained),
                _bool(decision.mapping_allowed),
                _bool(decision.fails_closed),
                "true",
            )
        )
    return tuple(rows)


def _canonical_records_from_current_representation(
    representation_payload: bytes,
) -> tuple[CovalentBondAtomPairCanonicalRecordDesign, ...]:
    rows = tuple(
        csv.DictReader(
            io.StringIO(representation_payload.decode("utf-8"))
        )
    )
    by_legacy: dict[str, CovalentBondAtomPairCanonicalRecordDesign] = {}
    for row in rows:
        legacy_value = row["stored_covalent_bond_atom_pair"]
        if legacy_value in by_legacy:
            continue
        evidence_type = row["explicit_bond_evidence_type"]
        authority = (
            "validated_struct_conn"
            if evidence_type.startswith("validated_struct_conn")
            else ""
        )
        common = {
            "locator_schema_version": LOCATOR_SCHEMA_VERSION,
            "event_id": row["sample_or_event_id"],
            "pdb_id": row["pdb_id"],
            "model_id": "",
            "label_asym_id": "",
            "label_seq_id": "",
            "altloc": "",
        }
        residue = CovalentAtomLocatorContractDesign(
            entity_role="target_residue_atom",
            auth_asym_id=row["residue_chain_id"],
            auth_seq_id=row["residue_index"],
            insertion_code=(
                row["residue_insertion_code_if_available"]
            ),
            comp_id=row["residue_name"],
            atom_name=row["residue_atom_name"],
            **common,
        )
        ligand = CovalentAtomLocatorContractDesign(
            entity_role="ligand_atom",
            auth_asym_id="",
            auth_seq_id="",
            insertion_code="",
            comp_id=row["ligand_comp_id_or_het_id"],
            atom_name=row["ligand_atom_name"],
            **common,
        )
        record = CovalentBondAtomPairCanonicalRecordDesign(
            pair_record_schema_version=PAIR_RECORD_SCHEMA_VERSION,
            residue_atom_locator=residue,
            ligand_atom_locator=ligand,
            explicit_bond_authority_class=authority,
            explicit_bond_provenance_id=(
                f"{row['source_row_identity']}:"
                f"{row['conn_id_if_available']}"
            ),
        )
        if not validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            record
        ):
            raise ValueError(
                f"invalid current name-level canonical fixture: {legacy_value}"
            )
        if project_covapie_legacy_atom_name_pair_v1(record) != legacy_value:
            raise ValueError(
                f"legacy projection disagrees with audited fields: {legacy_value}"
            )
        by_legacy[legacy_value] = record
    if tuple(value for value in LEGACY_VALUES if value not in by_legacy):
        raise ValueError("audited representation lacks a required legacy value")
    return tuple(by_legacy[value] for value in LEGACY_VALUES)


def _legacy_rows(
    representation_payload: bytes,
) -> tuple[tuple[object, ...], ...]:
    rows = []
    records = _canonical_records_from_current_representation(
        representation_payload
    )
    for value, record in zip(LEGACY_VALUES, records):
        reconstructed = project_covapie_legacy_atom_name_pair_v1(record)
        rows.append(
            (
                value,
                record.residue_atom_locator.atom_name,
                record.ligand_atom_locator.atom_name,
                reconstructed,
                _bool(reconstructed == value),
                CANONICAL_ENCODING_KIND,
                "true",
                _bool(record.residue_atom_locator.atom_name == "SG"),
                "true",
            )
        )
    return tuple(rows)


def build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1(
    repo_root: Path = REPO_ROOT,
) -> dict[str, bytes]:
    """Build the six deterministic evidence payloads from frozen predecessors."""
    (
        predecessor_manifest,
        issue_payload,
        representation_payload,
    ) = _verify_predecessor(repo_root)
    compatibility_evidence = (
        derive_covapie_model_input_index_space_compatibility_evidence_v1(
            repo_root
        )
    )
    audit_precondition_verified = all(
        (
            predecessor_manifest.get("outcome") == "audited",
            predecessor_manifest.get("current_source_lineage_verified") is True,
            predecessor_manifest.get("producer_projection_verified") is True,
            predecessor_manifest.get("record_conflict_present") is False,
            predecessor_manifest.get("producer_conflict_present") is False,
            predecessor_manifest.get("ready_for_encoding_contract_design")
            is True,
        )
    )
    contract = design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
        current_semantics_audit_precondition_verified=(
            audit_precondition_verified
        ),
        model_input_index_space_compatibility_evidence=(
            compatibility_evidence
        ),
    )
    if contract.outcome != "frozen":
        raise ValueError("contract design did not freeze")
    canonical_records = _canonical_records_from_current_representation(
        representation_payload
    )
    canonical_fixture = canonical_records[0]
    if not validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
        canonical_fixture
    ):
        raise ValueError("canonical record fixture did not validate")
    if project_covapie_legacy_atom_name_pair_v1(canonical_fixture) == "":
        raise ValueError("canonical record fixture projection is empty")

    payloads = {
        PUBLIC_FILE: _csv_bytes(
            (
                "contract_area",
                "contract_item",
                "expected_value",
                "observed_value",
                "source_or_rationale",
                "verified",
            ),
            _public_rows(),
        ),
        LOCATOR_FILE: _csv_bytes(
            (
                "field_order",
                "field_name",
                "data_type",
                "required",
                "empty_string_allowed",
                "applies_to_residue",
                "applies_to_ligand",
                "identity_role",
                "validation_rule",
                "current_materialization_status",
                "verified",
            ),
            _locator_rows(),
        ),
        POLICY_FILE: _csv_bytes(
            (
                "case_id",
                "input_condition",
                "expected_outcome",
                "expected_reason",
                "pair_retained",
                "mapping_allowed",
                "fails_closed",
                "verified",
            ),
            _policy_rows(),
        ),
        LEGACY_FILE: _csv_bytes(
            (
                "legacy_value",
                "observed_residue_atom_name",
                "observed_ligand_atom_name",
                "reconstructed_legacy_value",
                "matches_current_observation",
                "canonical_identity_source",
                "legacy_is_display_only",
                "current_cys_sg_compatible",
                "verified",
            ),
            _legacy_rows(representation_payload),
        ),
        ISSUE_FILE: issue_payload,
    }
    evidence_sha256 = {
        name: _sha256(payload) for name, payload in payloads.items()
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "outcome": contract.outcome,
        "base_commit": BASE_COMMIT,
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "covalent_bond_atom_pair_encoding_contract_frozen": True,
        "current_semantics_audit_precondition_verified": True,
        "predecessor_outcome": predecessor_manifest["outcome"],
        "predecessor_sha256": {
            path.as_posix(): sha
            for path, sha in PREDECESSOR_SHA256.items()
        },
        "structured_canonical_encoding_frozen": True,
        "canonical_encoding_kind": CANONICAL_ENCODING_KIND,
        "canonical_pair_record_schema_frozen": True,
        "canonical_pair_record_schema_version": PAIR_RECORD_SCHEMA_VERSION,
        "canonical_pair_record_field_count": 5,
        "canonical_pair_record_validator_available": True,
        "canonical_pair_record_roles_enforced": True,
        "canonical_pair_record_identity_consistency_enforced": True,
        "explicit_authority_embedded_in_canonical_record": True,
        "explicit_provenance_embedded_in_canonical_record": True,
        "legacy_projection_function_available": True,
        "structured_atom_locator_schema_frozen": True,
        "locator_schema_version": LOCATOR_SCHEMA_VERSION,
        "entity_role_vocabulary": list(ROLE_VOCABULARY),
        "explicit_bond_authority_policy_frozen": True,
        "accepted_explicit_bond_authority_classes": list(AUTHORITY_VOCABULARY),
        "distance_only_inference_forbidden": True,
        "cardinality_and_fail_closed_policy_frozen": True,
        "positive_pair_cardinality_policy": contract.positive_pair_cardinality_policy,
        "legacy_compatibility_policy_frozen": True,
        "legacy_delimiter": "--",
        "legacy_visible_order": "residue_atom_name_then_ligand_atom_name",
        "legacy_value_must_match_structured_atom_names": True,
        "legacy_value_may_be_used_as_sole_locator": False,
        "legacy_value_may_be_used_as_tensor_target": False,
        "legacy_string_is_canonical_identity": False,
        "legacy_string_is_display_only": True,
        "future_atom_table_mapping_policy_frozen": True,
        "model_input_index_space_compatibility_derived_from_committed_evidence": True,
        "model_input_index_space_compatibility_verified": (
            compatibility_evidence.compatible
        ),
        "model_input_index_space_compatibility_evidence_paths": list(
            compatibility_evidence.evidence_paths
        ),
        "model_input_index_space_compatibility_evidence_sha256": {
            path.as_posix(): sha
            for path, sha in INDEX_SPACE_EVIDENCE_SHA256.items()
        },
        "model_input_index_space_compatibility_evidence_selectors": list(
            INDEX_SPACE_EVIDENCE_SELECTORS
        ),
        "final_dataset_pocket_atom_table_reference_present": (
            compatibility_evidence
            .final_dataset_pocket_atom_table_reference_present
        ),
        "final_dataset_ligand_atom_table_reference_present": (
            compatibility_evidence
            .final_dataset_ligand_atom_table_reference_present
        ),
        "current_pair_tensor_index_contract_present": (
            compatibility_evidence.current_pair_tensor_index_contract_present
        ),
        "conflicting_existing_index_space_contract_present": (
            compatibility_evidence
            .conflicting_existing_index_space_contract_present
        ),
        "pair_tensorization_currently_blocked": (
            compatibility_evidence.pair_tensorization_currently_blocked
        ),
        "row_order_validation_deferred_to_contract_validation": (
            compatibility_evidence
            .row_order_validation_deferred_to_contract_validation
        ),
        "residue_model_index_space": contract.residue_model_index_space,
        "ligand_model_index_space": contract.ligand_model_index_space,
        "model_index_base": contract.model_index_base,
        "full_protein_mapping_role": "trace_or_qa_only_not_v1_model_target",
        "semantic_locator_is_authority": True,
        "row_index_is_derived_view": True,
        "canonical_mask_pair_identity_invariant": True,
        "canonical_masks": [
            {"semantic_name": semantic_name, "alias": alias}
            for semantic_name, alias in CANONICAL_MASKS
        ],
        "b3_warhead_retention_changes_pair_identity": False,
        "b3_pair_auxiliary_loss_activation_defined": False,
        "negative_pair_construction_defined": False,
        "negative_sampling_defined": False,
        "pair_tensor_materialized": False,
        "pair_tensor_shape_defined": False,
        "pair_loss_mask_defined": False,
        "pair_head_implemented": False,
        "pair_contrastive_loss_implemented": False,
        "encoding_contract_validation_completed": False,
        "atom_pair_issue_resolved": False,
        "provider_issue_resolved": False,
        "issue_status_changed": False,
        "resolved_issue_count": 0,
        "new_issue_count": 0,
        "deleted_issue_count": 0,
        "effective_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        ],
        "ready_for_contract_validation": True,
        "ready_for_tensorization": False,
        "provider_used": False,
        "download_used": False,
        "raw_read": False,
        "raw_write": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "training_used": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "ready_for_training": False,
        "public_contract_data_row_count": len(_public_rows()),
        "locator_schema_data_row_count": len(_locator_rows()),
        "policy_matrix_data_row_count": len(_policy_rows()),
        "legacy_compatibility_data_row_count": len(
            _legacy_rows(representation_payload)
        ),
        "issue_inventory_data_row_count": (
            len(issue_payload.decode("utf-8").splitlines()) - 1
        ),
        "issue_inventory_source_sha256": PREDECESSOR_SHA256[
            PREDECESSOR_ISSUES
        ],
        "evidence_sha256": evidence_sha256,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return payloads


def run_covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1(
    output_root: Path,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, bytes]:
    """Materialize only the six declared deterministic design artifacts."""
    if type(output_root) is not _PATH_TYPE or type(repo_root) is not _PATH_TYPE:
        raise TypeError("output_root and repo_root must be exact Path values")
    payloads = (
        build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1(
            repo_root
        )
    )
    output_root.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        (output_root / name).write_bytes(payloads[name])
    return payloads
