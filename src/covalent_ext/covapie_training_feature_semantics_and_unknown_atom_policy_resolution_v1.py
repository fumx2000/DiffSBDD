"""Resolve CovaPIE training atom semantics without tensor or model execution.

The resolution is metadata-only.  Every historical input is read from the
explicit BASE commit.  Explicit hydrogen is removed before a model-bound node
set exists, while unsupported non-hydrogen and missing or invalid type symbols
reject the complete sample.  No runtime dataloader, tensor, model, checkpoint,
forward, loss, or training path is used or modified here.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import subprocess
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Sequence

__all__ = (
    "HeavyAtomProjection",
    "TrainingFeatureSemanticsAndUnknownAtomPolicyResolutionDecision",
    "TrainingFeatureSemanticsResolutionObservation",
    "TrainingFeatureSemanticsResolutionScenario",
    "build_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_artifacts_v1",
    "build_failure_matrix_rows_v1",
    "classify_type_symbol_v1",
    "derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1",
    "project_type_symbols_to_checkpoint_heavy_v1",
    "serialize_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_decision_v1",
    "validate_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_scenario_v1",
)

BASE_COMMIT = "5b2013281b03d7bd3e0c59b9985e52494263c69f"
BASE_PARENT = "66d488ba829dad29d17e8a0ec07fa9798bae90b2"
BASE_TREE = "e5254b14e5c31768806443b8fbf0f7b5179c9975"
BASE_SUBJECT = "add CovaPIE final training feature-semantics audit v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE training unknown-atom policy resolution v1"
SCHEMA_VERSION = (
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1"
)
STAGE = SCHEMA_VERSION
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
SOURCE_INVENTORY_FILE = "covapie_unknown_atom_resolution_source_inventory.csv"
DISPOSITION_FILE = (
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
SAMPLE_PROJECTION_FILE = (
    "covapie_sample_heavy_atom_projection_validation_matrix.csv"
)
FAILURE_MATRIX_FILE = "covapie_unknown_atom_policy_resolution_failure_matrix.csv"
ISSUE_INVENTORY_FILE = (
    "covapie_unknown_atom_policy_resolution_issue_readiness_inventory.csv"
)
MANIFEST_FILE = (
    "covapie_training_feature_semantics_and_unknown_atom_policy_"
    "resolution_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    DISPOSITION_FILE,
    SAMPLE_PROJECTION_FILE,
    FAILURE_MATRIX_FILE,
    ISSUE_INVENTORY_FILE,
    MANIFEST_FILE,
)

PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1.py"
)
PREDECESSOR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1"
)
PREDECESSOR_MANIFEST = PREDECESSOR_ROOT / (
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_"
    "audit_manifest.json"
)
PREDECESSOR_ISSUES = (
    PREDECESSOR_ROOT / "covapie_feature_semantics_issue_readiness_inventory.csv"
)
PREDECESSOR_REGISTRY = (
    PREDECESSOR_ROOT / "covapie_training_feature_semantics_registry.csv"
)
PREDECESSOR_UNKNOWN_MATRIX = (
    PREDECESSOR_ROOT / "covapie_unknown_atom_policy_audit_matrix.csv"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
ATOM_PAIR_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1"
)
ATOM_PAIR_MATRIX = (
    ATOM_PAIR_ROOT / "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
ATOM_PAIR_MANIFEST = ATOM_PAIR_ROOT / (
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_manifest.json"
)
CHECKPOINT_CONFIG = Path("configs/crossdock_fullatom_cond.yml")
CONSTANTS_SOURCE = Path("constants.py")
PREPROCESSOR_SOURCE = Path("process_crossdock.py")
DATASET_SOURCE = Path("dataset.py")
PREVIEW_ADAPTER_SOURCE = Path("src/covalent_ext/diffsbdd_input_adapter.py")
CHECKPOINT_SMOKE_SOURCE = Path(
    "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py"
)

FROZEN_SHA256 = {
    PREDECESSOR_SOURCE: (
        "30dcd94500fa5acc40a566072b80df9f1383b326778eb1ce7e5709819a7c57ad"
    ),
    PREDECESSOR_MANIFEST: (
        "8e9aa9e853556715f1f6920b6bb80c1aa0ab22344b4118ba63f988d0ae659dbe"
    ),
    PREDECESSOR_ISSUES: (
        "38469f4d1fff515b47d47463bd085844e64109aed3875723710776e4f36c7128"
    ),
    PREDECESSOR_REGISTRY: (
        "820e0abaa8dad761d66950ee85b3ba0f0078448ca33180c29c9238572a91995f"
    ),
    PREDECESSOR_UNKNOWN_MATRIX: (
        "f6aeeb1528563429652a4ab8441d785547b0a44385c628448c04e18a99b4c5bd"
    ),
    FINAL_DATASET_INDEX: (
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d"
    ),
    ATOM_PAIR_MATRIX: (
        "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45"
    ),
    ATOM_PAIR_MANIFEST: (
        "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152"
    ),
}

CHECKPOINT_VOCABULARY = (
    ("C", 6, 0),
    ("N", 7, 1),
    ("O", 8, 2),
    ("S", 16, 3),
    ("B", 5, 4),
    ("Br", 35, 5),
    ("Cl", 17, 6),
    ("P", 15, 7),
    ("I", 53, 8),
    ("F", 9, 9),
)
CHECKPOINT_TOKEN_TO_INDEX = {
    token: index for token, _atomic_number, index in CHECKPOINT_VOCABULARY
}
CHECKPOINT_ATOMIC_NUMBER_TO_INDEX = {
    atomic_number: index
    for _token, atomic_number, index in CHECKPOINT_VOCABULARY
}
CHECKPOINT_CHANNEL_ORDER = "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
PREVIEW_CHANNEL_ORDER = (
    "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9|others:10"
)
UNKNOWN_ATOM_POLICY = (
    "fail_closed_rejection_required_for_checkpoint_compatibility"
)
EXPLICIT_HYDROGEN_POLICY = "exclude_before_checkpoint_model_projection"
SUPPORTED_NONHYDROGEN_POLICY = "retain_and_map_to_checkpoint_10d"
UNSUPPORTED_NONHYDROGEN_POLICY = "reject_sample_fail_closed"
MISSING_OR_EMPTY_POLICY = "reject_sample_fail_closed"
INVALID_TYPE_SYMBOL_POLICY = "reject_sample_fail_closed"
RECOMMENDED_NEXT_STEP = "design_covapie_tensor_label_and_loss_mask_contract_v1"

CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
PLANNED_COVALENT_MODEL_MODULES = (
    "target residue/atom condition adapter",
    "role/mask/anchor-distance encoding",
    "ligand atom ↔ residue atom pair prediction head",
    "covalent geometry prediction head",
    "pair contrastive loss",
)
PROJECTION_ORDER = (
    "read_explicit_type_symbol",
    "validate_present_nonempty_and_legal_type",
    "classify_supported_heavy_explicit_hydrogen_or_unsupported_nonhydrogen",
    "exclude_explicit_hydrogen",
    "reject_sample_if_unsupported_nonhydrogen_exists",
    "build_source_row_to_retained_heavy_row_index_map",
    "project_all_future_per_atom_arrays_and_masks",
    "remap_covalent_atom_pair_indices",
    "compute_retained_ligand_plus_pocket_heavy_atom_joint_centroid",
    "generate_checkpoint_10d_categorical_feature",
    "enter_future_tensor_contract",
)
SHARED_PROJECTION_CONSUMERS = (
    "all_future_per_atom_tensors",
    "role_labels",
    "canonical_task_masks",
    "target_masks",
    "context_masks",
    "generation_masks",
    "fixed_masks",
    "auxiliary_labels",
    "covalent_atom_pair_indices",
)
SYMBOL_CLASSES = {
    "supported_checkpoint_heavy_atom",
    "explicit_hydrogen",
    "unsupported_nonhydrogen",
    "missing_or_invalid",
}
PROJECTION_DISPOSITIONS = {
    "retain_checkpoint_10d",
    "exclude_explicit_hydrogen",
    "reject_sample_unsupported_nonhydrogen",
    "reject_sample_missing_or_invalid_symbol",
}
_LEGAL_ELEMENT_TOKEN = re.compile(r"^[A-Z][a-z]?$")

EXPECTED_COUNTS = {
    "source_atom_row_count": 2870,
    "protein_source_row_count": 2531,
    "ligand_source_row_count": 339,
    "excluded_explicit_hydrogen_row_count": 345,
    "protein_excluded_hydrogen_row_count": 329,
    "ligand_excluded_hydrogen_row_count": 16,
    "retained_heavy_atom_row_count": 2525,
    "protein_retained_heavy_row_count": 2202,
    "ligand_retained_heavy_row_count": 323,
    "unsupported_nonhydrogen_row_count": 0,
    "missing_or_invalid_symbol_row_count": 0,
}

SOURCE_COLUMNS = (
    "source_role",
    "source_path",
    "source_sha256",
    "committed_in_base",
    "source_kind",
    "selector_or_symbol",
    "referenced_atom_row_count",
    "referenced_sample_count",
    "verified",
)
DISPOSITION_COLUMNS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_identity",
    "domain",
    "source_table_path",
    "source_table_sha256",
    "source_atom_row_index_0based",
    "source_atom_site_or_row_identity",
    "type_symbol",
    "symbol_class",
    "projection_disposition",
    "projection_reason",
    "retained_for_checkpoint_model",
    "projected_heavy_atom_row_index_0based",
    "checkpoint_channel_index",
    "excluded_before_centering",
    "excluded_before_node_count",
    "excluded_before_batch_membership",
    "excluded_before_mask_projection",
    "excluded_before_pair_index_projection",
    "sample_rejected",
    "verified",
)
SAMPLE_COLUMNS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_identity",
    "source_pocket_atom_count",
    "excluded_pocket_h_count",
    "retained_pocket_heavy_count",
    "unsupported_pocket_nonh_count",
    "source_ligand_atom_count",
    "excluded_ligand_h_count",
    "retained_ligand_heavy_count",
    "unsupported_ligand_nonh_count",
    "retained_joint_atom_count",
    "retained_pocket_nonempty",
    "retained_ligand_nonempty",
    "source_residue_pair_row_index_0based",
    "projected_residue_pair_row_index_0based",
    "source_ligand_pair_row_index_0based",
    "projected_ligand_pair_row_index_0based",
    "residue_pair_atom_type_symbol",
    "ligand_pair_atom_type_symbol",
    "residue_pair_atom_retained",
    "ligand_pair_atom_retained",
    "pair_projection_exact_one",
    "projected_pocket_indices_contiguous",
    "projected_ligand_indices_contiguous",
    "source_order_preserved",
    "centering_node_set",
    "hydrogen_filter_before_centering",
    "checkpoint_width_after_projection",
    "sample_policy_outcome",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "expected_outcome",
    "observed_outcome",
    "unknown_atom_policy_contract_resolved",
    "feature_semantics_known",
    "ready_for_tensor_label_loss_mask_contract_design",
    "ready_for_tensorization",
    "ready_for_model_integration",
    "ready_for_training",
    "unknown_issue_effective_status",
    "fails_closed",
    "verified",
)
FAILURE_CASES = (
    "predecessor SHA drift",
    "predecessor audit not completed",
    "predecessor open issue set not exact",
    "atom table count not 22",
    "atom disposition count not 2870",
    "duplicate source atom identity",
    "missing type_symbol accepted",
    "atom-name inference attempted",
    "supported heavy atom excluded",
    "explicit H retained",
    "explicit H mapped to zero vector",
    "explicit H mapped to others",
    "unsupported non-H retained",
    "unsupported non-H mapped to zero vector",
    "unsupported non-H mapped to others",
    "checkpoint width changed to 11",
    "checkpoint channel order drift",
    "filtering applied after centering",
    "projected index not contiguous",
    "projected source order changed",
    "duplicate projected index",
    "excluded row assigned projected index",
    "retained row missing projected index",
    "residue pair atom excluded",
    "ligand pair atom excluded",
    "residue pair remap mismatch",
    "ligand pair remap mismatch",
    "sample empty after projection",
    "B3 mask omitted",
    "unknown issue resolved before complete projection",
    "ready-for-tensorization prematurely true",
    "model/dataloader/forward/loss/checkpoint/training boundary crossed",
)


@dataclass(frozen=True)
class TrainingFeatureSemanticsAndUnknownAtomPolicyResolutionDecision:
    schema_version: str
    outcome: str
    predecessor_verified: bool
    source_atom_row_count: int
    retained_heavy_atom_row_count: int
    excluded_explicit_hydrogen_row_count: int
    unsupported_nonhydrogen_row_count: int
    missing_or_invalid_symbol_row_count: int
    protein_unknown_atom_policy: str
    ligand_unknown_atom_policy: str
    explicit_hydrogen_policy: str
    unsupported_nonhydrogen_policy: str
    checkpoint_categorical_width: int
    checkpoint_channel_order_preserved: bool
    preview_11d_checkpoint_authority: bool
    silent_zero_vector_fallback_allowed: bool
    all_atom_rows_classified: bool
    all_sample_projections_valid: bool
    all_pair_indices_remapped: bool
    hydrogen_filter_precedes_centering: bool
    unknown_atom_policy_contract_resolved: bool
    unknown_atom_runtime_enforcement_integrated: bool
    feature_semantics_known: bool
    checkpoint_compatibility_preserved: bool
    ready_for_tensor_label_loss_mask_contract_design: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool
    model_changed: bool
    dataloader_changed: bool
    tensorization_used: bool
    checkpoint_access: bool
    training_used: bool
    recommended_next_step: str


@dataclass(frozen=True)
class HeavyAtomProjection:
    outcome: str
    symbol_classes: tuple[str, ...]
    keep_mask: tuple[bool, ...]
    source_to_projected_index: tuple[int | None, ...]
    checkpoint_channel_indices: tuple[int | None, ...]
    sample_rejected: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class TrainingFeatureSemanticsResolutionScenario:
    predecessor_sha_valid: bool = True
    predecessor_audit_completed: bool = True
    predecessor_open_issue_set_exact: bool = True
    atom_table_count: int = 22
    atom_disposition_count: int = 2870
    source_atom_identities_unique: bool = True
    missing_or_invalid_symbols_rejected: bool = True
    atom_name_inference_attempted: bool = False
    supported_heavy_retained: bool = True
    explicit_hydrogen_excluded: bool = True
    explicit_hydrogen_zero_vector: bool = False
    explicit_hydrogen_others: bool = False
    unsupported_nonhydrogen_rejected: bool = True
    unsupported_nonhydrogen_zero_vector: bool = False
    unsupported_nonhydrogen_others: bool = False
    checkpoint_width: int = 10
    checkpoint_channel_order: str = CHECKPOINT_CHANNEL_ORDER
    filter_before_centering: bool = True
    projected_indices_contiguous: bool = True
    source_order_preserved: bool = True
    projected_indices_unique: bool = True
    excluded_rows_without_projected_index: bool = True
    retained_rows_have_projected_index: bool = True
    residue_pair_retained: bool = True
    ligand_pair_retained: bool = True
    residue_pair_remap_exact: bool = True
    ligand_pair_remap_exact: bool = True
    samples_nonempty_after_projection: bool = True
    canonical_masks: tuple[tuple[str, str], ...] = CANONICAL_MASKS
    complete_projection_evidence: bool = True
    ready_contract_design: bool = True
    ready_tensorization: bool = False
    boundary_crossed: bool = False


@dataclass(frozen=True)
class TrainingFeatureSemanticsResolutionObservation:
    outcome: str
    reasons: tuple[str, ...]
    unknown_atom_policy_contract_resolved: bool
    feature_semantics_known: bool
    ready_for_tensor_label_loss_mask_contract_design: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool
    unknown_issue_effective_status: str


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def _git(repo_root: Path, *args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise ValueError(
            f"BASE-bound git read failed: {args!r}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def _base_bytes(repo_root: Path, path: Path) -> bytes:
    name = path.as_posix()
    forbidden_suffixes = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz", ".tar", ".zip",
        ".tgz", ".tmp", ".part",
    }
    if name.startswith("data/raw/"):
        raise ValueError(f"raw source access forbidden: {name}")
    if path.suffix.lower() in forbidden_suffixes:
        raise ValueError(f"artifact source access forbidden: {name}")
    _git(repo_root, "cat-file", "-e", f"{BASE_COMMIT}:{name}")
    return _git(repo_root, "show", f"{BASE_COMMIT}:{name}")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _json(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _csv_scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, dict, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _csv_bytes(
    columns: tuple[str, ...],
    rows: Sequence[dict[str, Any]],
) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=columns,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_scalar(value) for key, value in row.items()})
    return buffer.getvalue().encode("utf-8")


def classify_type_symbol_v1(type_symbol: object) -> str:
    """Classify only an explicit ``type_symbol`` value.

    The helper intentionally accepts no atom-name or residue-name input.
    """

    if type(type_symbol) is not str:
        return "missing_or_invalid"
    if not type_symbol or type_symbol.strip() != type_symbol:
        return "missing_or_invalid"
    if type_symbol == "H":
        return "explicit_hydrogen"
    if type_symbol in CHECKPOINT_TOKEN_TO_INDEX:
        return "supported_checkpoint_heavy_atom"
    if _LEGAL_ELEMENT_TOKEN.fullmatch(type_symbol) is None:
        return "missing_or_invalid"
    return "unsupported_nonhydrogen"


def project_type_symbols_to_checkpoint_heavy_v1(
    type_symbols: Sequence[object],
) -> HeavyAtomProjection:
    """Project a sample/domain sequence, rejecting the full sequence on a gap."""

    classes = tuple(classify_type_symbol_v1(value) for value in type_symbols)
    bad = tuple(
        f"{index}:{symbol_class}"
        for index, symbol_class in enumerate(classes)
        if symbol_class in {"unsupported_nonhydrogen", "missing_or_invalid"}
    )
    if bad:
        empty = tuple(None for _value in type_symbols)
        return HeavyAtomProjection(
            outcome="invalid",
            symbol_classes=classes,
            keep_mask=tuple(False for _value in type_symbols),
            source_to_projected_index=empty,
            checkpoint_channel_indices=empty,
            sample_rejected=True,
            reasons=bad,
        )
    keep_mask = tuple(
        symbol_class == "supported_checkpoint_heavy_atom"
        for symbol_class in classes
    )
    next_index = 0
    source_to_projected: list[int | None] = []
    channels: list[int | None] = []
    for value, keep in zip(type_symbols, keep_mask):
        if keep:
            source_to_projected.append(next_index)
            channels.append(CHECKPOINT_TOKEN_TO_INDEX[str(value)])
            next_index += 1
        else:
            source_to_projected.append(None)
            channels.append(None)
    return HeavyAtomProjection(
        outcome="passed",
        symbol_classes=classes,
        keep_mask=keep_mask,
        source_to_projected_index=tuple(source_to_projected),
        checkpoint_channel_indices=tuple(channels),
        sample_rejected=False,
        reasons=(),
    )


def _literal_assignment(source: bytes, name: str) -> Any:
    tree = ast.parse(source.decode("utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"literal assignment missing: {name}")


def _dataset_params_assignment(source: bytes, key: str) -> dict[str, Any]:
    tree = ast.parse(source.decode("utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == "dataset_params"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == key
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise ValueError(f"dataset_params assignment missing: {key}")


def _validate_categorical_lineage(
    payloads: dict[Path, bytes],
) -> dict[str, Any]:
    config_text = payloads[CHECKPOINT_CONFIG].decode("utf-8")
    config_valid = all(
        fragment in config_text
        for fragment in (
            "dataset: 'crossdock'",
            "processed_crossdock_noH_full",
            "pocket_representation: 'full-atom'",
            "normalize_factors: [1, 4]",
        )
    )
    constants = payloads[CONSTANTS_SOURCE]
    checkpoint_dataset = _dataset_params_assignment(constants, "crossdock")
    preview_dataset = _dataset_params_assignment(constants, "crossdock_full")
    checkpoint_encoder = checkpoint_dataset.get("atom_encoder")
    preview_encoder = preview_dataset.get("atom_encoder")
    expected_10d = {
        token: index for token, _number, index in CHECKPOINT_VOCABULARY
    }
    expected_11d = {**expected_10d, "others": 10}
    preview_source_encoder = _literal_assignment(
        payloads[PREVIEW_ADAPTER_SOURCE], "ATOM_ENCODER_CROSSDOCK_FULL"
    )
    smoke_mapping = _literal_assignment(
        payloads[CHECKPOINT_SMOKE_SOURCE],
        "CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX",
    )
    smoke_text = payloads[CHECKPOINT_SMOKE_SOURCE].decode("utf-8")
    smoke_zero_vector = all(
        fragment in smoke_text
        for fragment in (
            "torch.zeros((len(flat_numbers), len(CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX))",
            "feature_idx = CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX.get(int(value))",
            "if feature_idx is None:",
            "one_hot[row_idx, feature_idx] = 1.0",
            'input_contract.get("target_ligand_feature_dim", 0)',
            'input_contract.get("target_pocket_feature_dim", 0)',
            "target_ligand_dim != 10 or target_pocket_dim != 10",
        )
    )
    if not all(
        (
            config_valid,
            checkpoint_encoder == expected_10d,
            preview_encoder == expected_11d,
            preview_source_encoder == expected_11d,
            smoke_mapping == CHECKPOINT_ATOMIC_NUMBER_TO_INDEX,
            smoke_zero_vector,
        )
    ):
        raise ValueError("categorical lineage failed closed")
    return {
        "checkpoint_config_noh_full": True,
        "checkpoint_channel_order_preserved": True,
        "preview_channel_order_preserved": True,
        "preview_or_intermediate_only": True,
        "preview_11d_checkpoint_authority": False,
        "observed_smoke_zero_vector_behavior": True,
        "observed_smoke_behavior_allowed_final_training_policy": False,
    }


def _verify_predecessor(
    repo_root: Path,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    if any(
        _sha(payloads[path]) != expected
        for path, expected in FROZEN_SHA256.items()
    ):
        raise ValueError("frozen predecessor SHA drift")
    manifest = _json(payloads[PREDECESSOR_MANIFEST])
    expected = {
        "feature_semantics_audit_completed": True,
        "audit_outcome": "audited_with_blockers",
        "all_current_model_input_semantics_frozen": True,
        "protein_unknown_atom_policy": "unknown_atom_policy_unresolved",
        "ligand_unknown_atom_policy": "unknown_atom_policy_unresolved",
        "unknown_atom_feature_policy_resolved": False,
        "feature_semantics_known": False,
        "effective_open_issue_count": 1,
        "effective_open_issues": ["UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"],
        "checkpoint_compatibility_preserved": True,
        "ready_for_tensor_label_loss_mask_contract_design": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("predecessor manifest contract drift")
    issues = _csv_rows(payloads[PREDECESSOR_ISSUES])
    open_issues = [
        row["issue_id"]
        for row in issues
        if row.get("successor_effective_status") == "open"
    ]
    if (
        len(issues) != 32
        or open_issues != ["UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"]
        or issues[30].get("issue_id")
        != "FINAL_TRAINING_FEATURE_SEMANTICS_UNRESOLVED"
        or issues[30].get("successor_effective_status") != "resolved"
    ):
        raise ValueError("predecessor issue inventory drift")
    return payloads, manifest


def _source_specs() -> tuple[tuple[Path, str, str, str], ...]:
    return (
        (PREDECESSOR_SOURCE, "feature_audit_source", "python", "frozen SHA"),
        (PREDECESSOR_MANIFEST, "feature_audit_manifest", "json", "readiness contract"),
        (PREDECESSOR_REGISTRY, "feature_semantics_registry", "csv", "current feature lineage"),
        (PREDECESSOR_UNKNOWN_MATRIX, "unknown_policy_audit_matrix", "csv", "observed policy gaps"),
        (PREDECESSOR_ISSUES, "feature_audit_issue_inventory", "csv", "Exact32 rows"),
        (FINAL_DATASET_INDEX, "final_dataset_index", "csv", "11 canonical samples"),
        (ATOM_PAIR_MATRIX, "atom_pair_mapping_validation_matrix", "csv", "22 exact-one mappings"),
        (ATOM_PAIR_MANIFEST, "atom_pair_and_canonical_mask_authority", "json", "Exact5 masks and pair boundary"),
        (CHECKPOINT_CONFIG, "checkpoint_training_config", "yaml", "crossdock/processed_crossdock_noH_full/full-atom/[1,4]"),
        (CONSTANTS_SOURCE, "categorical_vocabulary_authority", "python", "dataset_params crossdock and crossdock_full"),
        (PREPROCESSOR_SOURCE, "historical_noh_preprocessor_lineage", "python", "process_ligand_and_pocket"),
        (DATASET_SOURCE, "historical_dataset_lineage", "python", "ProcessedLigandPocketDataset"),
        (PREVIEW_ADAPTER_SOURCE, "preview_11d_adapter", "python", "ATOM_ENCODER_CROSSDOCK_FULL/_one_hot_from_atomic_numbers"),
        (CHECKPOINT_SMOKE_SOURCE, "checkpoint_10d_smoke_lineage", "python", "CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX/_checkpoint_compatible_one_hot_from_atomic_numbers"),
        (Path("src/covalent_ext/npz_dataset.py"), "batch_input_adapter_reference", "python", "covalent_npz_collate_fn"),
        (Path("src/covalent_ext/batch_adapter.py"), "batch_input_adapter_reference", "python", "_coordinate_center/adapt_covalent_batch_for_model_v0"),
        (Path("src/covalent_ext/model_input_adapter.py"), "model_input_adapter_reference", "python", "build_covalent_model_input_v0"),
        (Path("lightning_modules.py"), "model_input_consumer_reference", "python", "LigandPocketDDPM.forward"),
        (Path("equivariant_diffusion/dynamics.py"), "model_feature_consumer_reference", "python", "EGNNDynamics.forward"),
        (Path("equivariant_diffusion/en_diffusion.py"), "diffusion_input_consumer_reference", "python", "normalize/forward/inpaint"),
    )


def _load_sources(
    repo_root: Path,
    fixed_payloads: dict[Path, bytes],
) -> tuple[
    list[dict[str, str]],
    dict[Path, bytes],
    dict[Path, list[dict[str, str]]],
]:
    final_rows = _csv_rows(fixed_payloads[FINAL_DATASET_INDEX])
    if len(final_rows) != 11:
        raise ValueError(f"canonical sample count drift: {len(final_rows)}")
    table_payloads: dict[Path, bytes] = {}
    table_rows: dict[Path, list[dict[str, str]]] = {}
    for sample in final_rows:
        for column in ("pocket_atom_table_path", "ligand_atom_table_path"):
            path = Path(sample[column])
            if path in table_payloads:
                raise ValueError(f"duplicate canonical atom table path: {path}")
            payload = _base_bytes(repo_root, path)
            rows = _csv_rows(payload)
            if not rows or "type_symbol" not in rows[0]:
                raise ValueError(f"atom table schema invalid: {path}")
            table_payloads[path] = payload
            table_rows[path] = rows
    if len(table_payloads) != 22:
        raise ValueError(f"atom table count drift: {len(table_payloads)}")
    return final_rows, table_payloads, table_rows


def _disposition_rows(
    final_rows: list[dict[str, str]],
    table_payloads: dict[Path, bytes],
    table_rows: dict[Path, list[dict[str, str]]],
) -> tuple[
    list[dict[str, Any]],
    dict[tuple[str, str], HeavyAtomProjection],
]:
    output: list[dict[str, Any]] = []
    projections: dict[tuple[str, str], HeavyAtomProjection] = {}
    identities: set[tuple[str, str, int]] = set()
    for sample in final_rows:
        for domain, column in (
            ("protein_or_pocket_atom", "pocket_atom_table_path"),
            ("ligand_atom", "ligand_atom_table_path"),
        ):
            path = Path(sample[column])
            rows = table_rows[path]
            symbols = tuple(row.get("type_symbol") for row in rows)
            projection = project_type_symbols_to_checkpoint_heavy_v1(symbols)
            projections[(sample["sample_index_row_id"], domain)] = projection
            for source_index, (row, symbol_class) in enumerate(
                zip(rows, projection.symbol_classes)
            ):
                identity = (sample["sample_index_row_id"], domain, source_index)
                if identity in identities:
                    raise ValueError("duplicate source atom identity")
                identities.add(identity)
                retained = symbol_class == "supported_checkpoint_heavy_atom"
                if symbol_class == "supported_checkpoint_heavy_atom":
                    disposition = "retain_checkpoint_10d"
                    reason = "supported_nonhydrogen_retained_in_checkpoint_10d"
                elif symbol_class == "explicit_hydrogen":
                    disposition = "exclude_explicit_hydrogen"
                    reason = "explicit_hydrogen_excluded_before_model_bound_projection"
                elif symbol_class == "unsupported_nonhydrogen":
                    disposition = "reject_sample_unsupported_nonhydrogen"
                    reason = "unsupported_nonhydrogen_requires_sample_fail_closed"
                else:
                    disposition = "reject_sample_missing_or_invalid_symbol"
                    reason = "missing_or_invalid_type_symbol_requires_sample_fail_closed"
                atom_site = row.get("atom_site_id", "")
                output.append({
                    "sample_index_row_id": sample["sample_index_row_id"],
                    "sample_preparation_input_id": sample["sample_preparation_input_id"],
                    "pdb_id": sample["pdb_id"],
                    "ligand_identity": sample["expected_het_id"],
                    "domain": domain,
                    "source_table_path": path.as_posix(),
                    "source_table_sha256": _sha(table_payloads[path]),
                    "source_atom_row_index_0based": source_index,
                    "source_atom_site_or_row_identity": (
                        f"atom_site_id={atom_site}"
                        if atom_site
                        else f"source_row_index_0based={source_index}"
                    ),
                    "type_symbol": row.get("type_symbol", ""),
                    "symbol_class": symbol_class,
                    "projection_disposition": disposition,
                    "projection_reason": reason,
                    "retained_for_checkpoint_model": retained,
                    "projected_heavy_atom_row_index_0based": (
                        projection.source_to_projected_index[source_index]
                        if not projection.sample_rejected else None
                    ),
                    "checkpoint_channel_index": (
                        projection.checkpoint_channel_indices[source_index]
                        if not projection.sample_rejected else None
                    ),
                    "excluded_before_centering": not retained,
                    "excluded_before_node_count": not retained,
                    "excluded_before_batch_membership": not retained,
                    "excluded_before_mask_projection": not retained,
                    "excluded_before_pair_index_projection": not retained,
                    "sample_rejected": projection.sample_rejected,
                    "verified": (
                        symbol_class in SYMBOL_CLASSES
                        and disposition in PROJECTION_DISPOSITIONS
                    ),
                })
    return output, projections


def _count_dispositions(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    protein = [
        row for row in rows if row["domain"] == "protein_or_pocket_atom"
    ]
    ligand = [row for row in rows if row["domain"] == "ligand_atom"]

    def count(group: Sequence[dict[str, Any]], symbol_class: str) -> int:
        return sum(row["symbol_class"] == symbol_class for row in group)

    return {
        "source_atom_row_count": len(rows),
        "protein_source_row_count": len(protein),
        "ligand_source_row_count": len(ligand),
        "excluded_explicit_hydrogen_row_count": count(
            rows, "explicit_hydrogen"
        ),
        "protein_excluded_hydrogen_row_count": count(
            protein, "explicit_hydrogen"
        ),
        "ligand_excluded_hydrogen_row_count": count(
            ligand, "explicit_hydrogen"
        ),
        "retained_heavy_atom_row_count": count(
            rows, "supported_checkpoint_heavy_atom"
        ),
        "protein_retained_heavy_row_count": count(
            protein, "supported_checkpoint_heavy_atom"
        ),
        "ligand_retained_heavy_row_count": count(
            ligand, "supported_checkpoint_heavy_atom"
        ),
        "unsupported_nonhydrogen_row_count": count(
            rows, "unsupported_nonhydrogen"
        ),
        "missing_or_invalid_symbol_row_count": count(
            rows, "missing_or_invalid"
        ),
    }


def _projection_indices_valid(projection: HeavyAtomProjection) -> bool:
    projected = [
        value
        for value in projection.source_to_projected_index
        if value is not None
    ]
    source_retained = [
        index for index, keep in enumerate(projection.keep_mask) if keep
    ]
    return (
        not projection.sample_rejected
        and projected == list(range(len(projected)))
        and source_retained == sorted(source_retained)
        and len(projected) == len(set(projected))
        and all(
            (mapped is not None) == keep
            for mapped, keep in zip(
                projection.source_to_projected_index, projection.keep_mask
            )
        )
    )


def _sample_projection_rows(
    final_rows: list[dict[str, str]],
    pair_rows: list[dict[str, str]],
    table_rows: dict[Path, list[dict[str, str]]],
    projections: dict[tuple[str, str], HeavyAtomProjection],
) -> list[dict[str, Any]]:
    if len(pair_rows) != 22:
        raise ValueError(f"atom-pair mapping row count drift: {len(pair_rows)}")
    pairs_by_sample: dict[str, dict[str, dict[str, str]]] = {}
    for row in pair_rows:
        sample_pairs = pairs_by_sample.setdefault(row["sample_index_row_id"], {})
        role = row["entity_role"]
        if role in sample_pairs:
            raise ValueError("duplicate atom-pair mapping role")
        sample_pairs[role] = row
    output: list[dict[str, Any]] = []
    for sample in final_rows:
        sample_id = sample["sample_index_row_id"]
        roles = pairs_by_sample.get(sample_id, {})
        if set(roles) != {"target_residue_atom", "ligand_atom"}:
            raise ValueError(f"atom-pair roles invalid: {sample_id}")
        pocket_path = Path(sample["pocket_atom_table_path"])
        ligand_path = Path(sample["ligand_atom_table_path"])
        pocket_rows = table_rows[pocket_path]
        ligand_rows = table_rows[ligand_path]
        pocket_projection = projections[(sample_id, "protein_or_pocket_atom")]
        ligand_projection = projections[(sample_id, "ligand_atom")]
        residue_source = int(
            roles["target_residue_atom"]["matched_row_index_0based"]
        )
        ligand_source = int(roles["ligand_atom"]["matched_row_index_0based"])
        if roles["target_residue_atom"]["target_table_path"] != pocket_path.as_posix():
            raise ValueError("residue pair target table drift")
        if roles["ligand_atom"]["target_table_path"] != ligand_path.as_posix():
            raise ValueError("ligand pair target table drift")
        residue_projected = pocket_projection.source_to_projected_index[
            residue_source
        ]
        ligand_projected = ligand_projection.source_to_projected_index[
            ligand_source
        ]
        residue_retained = (
            residue_projected is not None
            and pocket_projection.keep_mask[residue_source]
        )
        ligand_retained = (
            ligand_projected is not None
            and ligand_projection.keep_mask[ligand_source]
        )
        pair_exact = (
            residue_retained
            and ligand_retained
            and _truth(roles["target_residue_atom"]["verified"])
            and _truth(roles["ligand_atom"]["verified"])
            and roles["target_residue_atom"]["candidate_match_count"] == "1"
            and roles["ligand_atom"]["candidate_match_count"] == "1"
        )
        pocket_indices_valid = _projection_indices_valid(pocket_projection)
        ligand_indices_valid = _projection_indices_valid(ligand_projection)
        pocket_retained = sum(pocket_projection.keep_mask)
        ligand_retained_count = sum(ligand_projection.keep_mask)
        sample_passed = all(
            (
                not pocket_projection.sample_rejected,
                not ligand_projection.sample_rejected,
                pocket_retained > 0,
                ligand_retained_count > 0,
                pair_exact,
                pocket_indices_valid,
                ligand_indices_valid,
            )
        )
        output.append({
            "sample_index_row_id": sample_id,
            "sample_preparation_input_id": sample["sample_preparation_input_id"],
            "pdb_id": sample["pdb_id"],
            "ligand_identity": sample["expected_het_id"],
            "source_pocket_atom_count": len(pocket_rows),
            "excluded_pocket_h_count": sum(
                value == "explicit_hydrogen"
                for value in pocket_projection.symbol_classes
            ),
            "retained_pocket_heavy_count": pocket_retained,
            "unsupported_pocket_nonh_count": sum(
                value == "unsupported_nonhydrogen"
                for value in pocket_projection.symbol_classes
            ),
            "source_ligand_atom_count": len(ligand_rows),
            "excluded_ligand_h_count": sum(
                value == "explicit_hydrogen"
                for value in ligand_projection.symbol_classes
            ),
            "retained_ligand_heavy_count": ligand_retained_count,
            "unsupported_ligand_nonh_count": sum(
                value == "unsupported_nonhydrogen"
                for value in ligand_projection.symbol_classes
            ),
            "retained_joint_atom_count": pocket_retained + ligand_retained_count,
            "retained_pocket_nonempty": pocket_retained > 0,
            "retained_ligand_nonempty": ligand_retained_count > 0,
            "source_residue_pair_row_index_0based": residue_source,
            "projected_residue_pair_row_index_0based": residue_projected,
            "source_ligand_pair_row_index_0based": ligand_source,
            "projected_ligand_pair_row_index_0based": ligand_projected,
            "residue_pair_atom_type_symbol": pocket_rows[residue_source][
                "type_symbol"
            ],
            "ligand_pair_atom_type_symbol": ligand_rows[ligand_source][
                "type_symbol"
            ],
            "residue_pair_atom_retained": residue_retained,
            "ligand_pair_atom_retained": ligand_retained,
            "pair_projection_exact_one": pair_exact,
            "projected_pocket_indices_contiguous": pocket_indices_valid,
            "projected_ligand_indices_contiguous": ligand_indices_valid,
            "source_order_preserved": (
                pocket_indices_valid and ligand_indices_valid
            ),
            "centering_node_set": (
                "retained_ligand_plus_pocket_heavy_atoms"
            ),
            "hydrogen_filter_before_centering": True,
            "checkpoint_width_after_projection": 10,
            "sample_policy_outcome": "passed" if sample_passed else "invalid",
            "verified": sample_passed,
        })
    return output


def validate_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_scenario_v1(
    scenario: TrainingFeatureSemanticsResolutionScenario,
) -> TrainingFeatureSemanticsResolutionObservation:
    checks = (
        (scenario.predecessor_sha_valid, "predecessor_sha"),
        (scenario.predecessor_audit_completed, "predecessor_audit"),
        (scenario.predecessor_open_issue_set_exact, "predecessor_open_issues"),
        (scenario.atom_table_count == 22, "atom_table_count"),
        (scenario.atom_disposition_count == 2870, "atom_disposition_count"),
        (scenario.source_atom_identities_unique, "source_atom_identity"),
        (scenario.missing_or_invalid_symbols_rejected, "missing_or_invalid"),
        (not scenario.atom_name_inference_attempted, "atom_name_inference"),
        (scenario.supported_heavy_retained, "supported_heavy"),
        (scenario.explicit_hydrogen_excluded, "explicit_hydrogen"),
        (not scenario.explicit_hydrogen_zero_vector, "hydrogen_zero_vector"),
        (not scenario.explicit_hydrogen_others, "hydrogen_others"),
        (scenario.unsupported_nonhydrogen_rejected, "unsupported_nonhydrogen"),
        (
            not scenario.unsupported_nonhydrogen_zero_vector,
            "unsupported_zero_vector",
        ),
        (not scenario.unsupported_nonhydrogen_others, "unsupported_others"),
        (scenario.checkpoint_width == 10, "checkpoint_width"),
        (
            scenario.checkpoint_channel_order == CHECKPOINT_CHANNEL_ORDER,
            "checkpoint_channel_order",
        ),
        (scenario.filter_before_centering, "filter_before_centering"),
        (scenario.projected_indices_contiguous, "projected_contiguous"),
        (scenario.source_order_preserved, "source_order"),
        (scenario.projected_indices_unique, "projected_unique"),
        (
            scenario.excluded_rows_without_projected_index,
            "excluded_projected_index",
        ),
        (
            scenario.retained_rows_have_projected_index,
            "retained_projected_index",
        ),
        (scenario.residue_pair_retained, "residue_pair_retained"),
        (scenario.ligand_pair_retained, "ligand_pair_retained"),
        (scenario.residue_pair_remap_exact, "residue_pair_remap"),
        (scenario.ligand_pair_remap_exact, "ligand_pair_remap"),
        (
            scenario.samples_nonempty_after_projection,
            "sample_empty_after_projection",
        ),
        (scenario.canonical_masks == CANONICAL_MASKS, "canonical_masks"),
        (scenario.complete_projection_evidence, "complete_projection_evidence"),
        (scenario.ready_contract_design, "contract_design_readiness"),
        (not scenario.ready_tensorization, "premature_tensorization"),
        (not scenario.boundary_crossed, "authorized_boundary"),
    )
    reasons = tuple(reason for condition, reason in checks if not condition)
    resolved = not reasons
    return TrainingFeatureSemanticsResolutionObservation(
        outcome="resolved_policy_contract" if resolved else "invalid",
        reasons=reasons,
        unknown_atom_policy_contract_resolved=resolved,
        feature_semantics_known=resolved,
        ready_for_tensor_label_loss_mask_contract_design=resolved,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        unknown_issue_effective_status="resolved" if resolved else "open",
    )


def build_failure_matrix_rows_v1() -> list[dict[str, Any]]:
    mutations: dict[str, dict[str, Any]] = {
        "predecessor SHA drift": {"predecessor_sha_valid": False},
        "predecessor audit not completed": {"predecessor_audit_completed": False},
        "predecessor open issue set not exact": {"predecessor_open_issue_set_exact": False},
        "atom table count not 22": {"atom_table_count": 21},
        "atom disposition count not 2870": {"atom_disposition_count": 2869},
        "duplicate source atom identity": {"source_atom_identities_unique": False},
        "missing type_symbol accepted": {"missing_or_invalid_symbols_rejected": False},
        "atom-name inference attempted": {"atom_name_inference_attempted": True},
        "supported heavy atom excluded": {"supported_heavy_retained": False},
        "explicit H retained": {"explicit_hydrogen_excluded": False},
        "explicit H mapped to zero vector": {"explicit_hydrogen_zero_vector": True},
        "explicit H mapped to others": {"explicit_hydrogen_others": True},
        "unsupported non-H retained": {"unsupported_nonhydrogen_rejected": False},
        "unsupported non-H mapped to zero vector": {"unsupported_nonhydrogen_zero_vector": True},
        "unsupported non-H mapped to others": {"unsupported_nonhydrogen_others": True},
        "checkpoint width changed to 11": {"checkpoint_width": 11},
        "checkpoint channel order drift": {"checkpoint_channel_order": "drift"},
        "filtering applied after centering": {"filter_before_centering": False},
        "projected index not contiguous": {"projected_indices_contiguous": False},
        "projected source order changed": {"source_order_preserved": False},
        "duplicate projected index": {"projected_indices_unique": False},
        "excluded row assigned projected index": {"excluded_rows_without_projected_index": False},
        "retained row missing projected index": {"retained_rows_have_projected_index": False},
        "residue pair atom excluded": {"residue_pair_retained": False},
        "ligand pair atom excluded": {"ligand_pair_retained": False},
        "residue pair remap mismatch": {"residue_pair_remap_exact": False},
        "ligand pair remap mismatch": {"ligand_pair_remap_exact": False},
        "sample empty after projection": {"samples_nonempty_after_projection": False},
        "B3 mask omitted": {"canonical_masks": CANONICAL_MASKS[:3] + CANONICAL_MASKS[4:]},
        "unknown issue resolved before complete projection": {"complete_projection_evidence": False},
        "ready-for-tensorization prematurely true": {"ready_tensorization": True},
        "model/dataloader/forward/loss/checkpoint/training boundary crossed": {"boundary_crossed": True},
    }
    rows: list[dict[str, Any]] = []
    for failure_case in FAILURE_CASES:
        observation = (
            validate_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_scenario_v1(
                replace(
                    TrainingFeatureSemanticsResolutionScenario(),
                    **mutations[failure_case],
                )
            )
        )
        fails_closed = (
            observation.outcome == "invalid"
            and not observation.unknown_atom_policy_contract_resolved
            and not observation.feature_semantics_known
            and not observation.ready_for_tensor_label_loss_mask_contract_design
            and not observation.ready_for_tensorization
            and not observation.ready_for_model_integration
            and not observation.ready_for_training
            and observation.unknown_issue_effective_status == "open"
        )
        rows.append({
            "failure_case": failure_case,
            "expected_outcome": "invalid",
            "observed_outcome": observation.outcome,
            "unknown_atom_policy_contract_resolved": observation.unknown_atom_policy_contract_resolved,
            "feature_semantics_known": observation.feature_semantics_known,
            "ready_for_tensor_label_loss_mask_contract_design": observation.ready_for_tensor_label_loss_mask_contract_design,
            "ready_for_tensorization": observation.ready_for_tensorization,
            "ready_for_model_integration": observation.ready_for_model_integration,
            "ready_for_training": observation.ready_for_training,
            "unknown_issue_effective_status": observation.unknown_issue_effective_status,
            "fails_closed": fails_closed,
            "verified": fails_closed,
        })
    return rows


_ISSUE_TRANSITION_EVIDENCE = (
    "2870/2870 rows classified;"
    "345 explicit H rows excluded before model-bound projection;"
    "2525 supported heavy rows retained in source order;"
    "0 unsupported non-H and 0 missing symbols;"
    "11/11 covalent atom pairs retained and reindexed;"
    "checkpoint width remains 10;"
    "11D others preview forbidden as checkpoint authority;"
    "silent zero-vector fallback forbidden;"
    "runtime integration deferred to tensor contract"
)


def _issue_artifact(
    predecessor_payload: bytes,
    projections_valid: bool,
) -> tuple[bytes, list[dict[str, str]]]:
    rows = _csv_rows(predecessor_payload)
    if len(rows) != 32:
        raise ValueError("predecessor issue row count drift")
    columns = tuple(rows[0])
    unknown_rows = [
        row
        for row in rows
        if row["issue_id"] == "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"
    ]
    if len(unknown_rows) != 1:
        raise ValueError("unknown issue identity drift")
    if projections_valid:
        unknown = unknown_rows[0]
        unknown["successor_effective_status"] = "resolved"
        unknown["successor_transition_stage"] = STAGE
        unknown["successor_transition_action"] = (
            "resolved_by_explicit_hydrogen_exclusion_and_fail_closed_"
            "nonhydrogen_policy_v1"
        )
        unknown["successor_transition_evidence"] = _ISSUE_TRANSITION_EVIDENCE
    return _csv_bytes(columns, rows), rows


def _source_inventory(
    repo_root: Path,
    fixed_payloads: dict[Path, bytes],
    table_payloads: dict[Path, bytes],
    table_rows: dict[Path, list[dict[str, str]]],
) -> list[dict[str, Any]]:
    payloads = dict(fixed_payloads)
    specs = list(_source_specs())
    for path, _role, _kind, _selector in specs:
        if path not in payloads:
            payloads[path] = _base_bytes(repo_root, path)
    for path, payload in table_payloads.items():
        payloads[path] = payload
        role = (
            "pocket_atom_table"
            if path.name == "pocket_atom_table.csv"
            else "ligand_atom_table"
        )
        specs.append((path, role, "csv", "explicit type_symbol and source row order"))
    rows: list[dict[str, Any]] = []
    for path, role, kind, selector in sorted(
        specs, key=lambda item: (item[0].as_posix(), item[1])
    ):
        payload = payloads[path]
        referenced_atom_rows = len(table_rows[path]) if path in table_rows else 0
        if path == ATOM_PAIR_MATRIX:
            referenced_atom_rows = len(_csv_rows(payload))
        sample_count = 0
        if path == FINAL_DATASET_INDEX:
            sample_count = len(_csv_rows(payload))
        elif path in table_rows:
            sample_count = 1
        elif path in {ATOM_PAIR_MATRIX, ATOM_PAIR_MANIFEST}:
            sample_count = 11
        rows.append({
            "source_role": role,
            "source_path": path.as_posix(),
            "source_sha256": _sha(payload),
            "committed_in_base": True,
            "source_kind": kind,
            "selector_or_symbol": selector,
            "referenced_atom_row_count": referenced_atom_rows,
            "referenced_sample_count": sample_count,
            "verified": True,
        })
    return rows


def serialize_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_decision_v1(
    decision: TrainingFeatureSemanticsAndUnknownAtomPolicyResolutionDecision,
) -> bytes:
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1(
    repo_root: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    fixed_payloads, predecessor_manifest = _verify_predecessor(repo_root)
    final_rows, table_payloads, table_rows = _load_sources(
        repo_root, fixed_payloads
    )
    extra_payloads = {
        path: fixed_payloads.get(path) or _base_bytes(repo_root, path)
        for path, _role, _kind, _selector in _source_specs()
    }
    lineage = _validate_categorical_lineage(extra_payloads)
    pair_manifest = _json(fixed_payloads[ATOM_PAIR_MANIFEST])
    masks = tuple(
        (row.get("semantic_name"), row.get("display_alias"))
        for row in pair_manifest.get("canonical_masks", [])
    )
    if masks != CANONICAL_MASKS:
        raise ValueError("canonical Exact5 mask contract drift")
    disposition_rows, projections = _disposition_rows(
        final_rows, table_payloads, table_rows
    )
    counts = _count_dispositions(disposition_rows)
    if counts != EXPECTED_COUNTS:
        raise ValueError(
            "current atom disposition counts drifted: "
            + json.dumps(counts, sort_keys=True, separators=(",", ":"))
        )
    if not all(row["verified"] for row in disposition_rows):
        raise ValueError("atom disposition verification failed closed")
    pair_rows = _csv_rows(fixed_payloads[ATOM_PAIR_MATRIX])
    sample_rows = _sample_projection_rows(
        final_rows, pair_rows, table_rows, projections
    )
    samples_valid = (
        len(sample_rows) == 11
        and all(row["sample_policy_outcome"] == "passed" for row in sample_rows)
        and all(row["verified"] for row in sample_rows)
    )
    all_pair_indices_remapped = (
        samples_valid
        and all(row["pair_projection_exact_one"] for row in sample_rows)
    )
    all_rows_classified = (
        len(disposition_rows) == EXPECTED_COUNTS["source_atom_row_count"]
        and all(row["symbol_class"] in SYMBOL_CLASSES for row in disposition_rows)
        and counts["unsupported_nonhydrogen_row_count"] == 0
        and counts["missing_or_invalid_symbol_row_count"] == 0
    )
    resolved = (
        all_rows_classified and samples_valid and all_pair_indices_remapped
    )
    if not resolved:
        raise ValueError("current resolution evidence failed closed")
    failure_rows = build_failure_matrix_rows_v1()
    if len(failure_rows) != 32 or not all(row["verified"] for row in failure_rows):
        raise ValueError("failure matrix did not fail closed")
    issue_payload, issue_rows = _issue_artifact(
        fixed_payloads[PREDECESSOR_ISSUES], projections_valid=resolved
    )
    open_issues = [
        row["issue_id"]
        for row in issue_rows
        if row["successor_effective_status"] == "open"
    ]
    if open_issues:
        raise ValueError(f"effective issue set remains open: {open_issues!r}")
    decision = TrainingFeatureSemanticsAndUnknownAtomPolicyResolutionDecision(
        schema_version=SCHEMA_VERSION,
        outcome="resolved_policy_contract",
        predecessor_verified=True,
        source_atom_row_count=counts["source_atom_row_count"],
        retained_heavy_atom_row_count=counts["retained_heavy_atom_row_count"],
        excluded_explicit_hydrogen_row_count=counts[
            "excluded_explicit_hydrogen_row_count"
        ],
        unsupported_nonhydrogen_row_count=counts[
            "unsupported_nonhydrogen_row_count"
        ],
        missing_or_invalid_symbol_row_count=counts[
            "missing_or_invalid_symbol_row_count"
        ],
        protein_unknown_atom_policy=UNKNOWN_ATOM_POLICY,
        ligand_unknown_atom_policy=UNKNOWN_ATOM_POLICY,
        explicit_hydrogen_policy=EXPLICIT_HYDROGEN_POLICY,
        unsupported_nonhydrogen_policy=UNSUPPORTED_NONHYDROGEN_POLICY,
        checkpoint_categorical_width=10,
        checkpoint_channel_order_preserved=True,
        preview_11d_checkpoint_authority=False,
        silent_zero_vector_fallback_allowed=False,
        all_atom_rows_classified=all_rows_classified,
        all_sample_projections_valid=samples_valid,
        all_pair_indices_remapped=all_pair_indices_remapped,
        hydrogen_filter_precedes_centering=True,
        unknown_atom_policy_contract_resolved=True,
        unknown_atom_runtime_enforcement_integrated=False,
        feature_semantics_known=True,
        checkpoint_compatibility_preserved=True,
        ready_for_tensor_label_loss_mask_contract_design=True,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        model_changed=False,
        dataloader_changed=False,
        tensorization_used=False,
        checkpoint_access=False,
        training_used=False,
        recommended_next_step=RECOMMENDED_NEXT_STEP,
    )
    source_rows = _source_inventory(
        repo_root, fixed_payloads, table_payloads, table_rows
    )
    return {
        "decision": decision,
        "predecessor_manifest": predecessor_manifest,
        "lineage": lineage,
        "counts": counts,
        "source_rows": source_rows,
        "disposition_rows": disposition_rows,
        "sample_rows": sample_rows,
        "failure_rows": failure_rows,
        "issue_rows": issue_rows,
        "issue_payload": issue_payload,
        "effective_open_issues": open_issues,
    }


def _non_manifest_artifacts(result: dict[str, Any]) -> dict[str, bytes]:
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(
            SOURCE_COLUMNS, result["source_rows"]
        ),
        DISPOSITION_FILE: _csv_bytes(
            DISPOSITION_COLUMNS, result["disposition_rows"]
        ),
        SAMPLE_PROJECTION_FILE: _csv_bytes(
            SAMPLE_COLUMNS, result["sample_rows"]
        ),
        FAILURE_MATRIX_FILE: _csv_bytes(
            FAILURE_COLUMNS, result["failure_rows"]
        ),
        ISSUE_INVENTORY_FILE: result["issue_payload"],
    }


def _manifest(
    result: dict[str, Any],
    evidence: dict[str, bytes],
) -> dict[str, Any]:
    decision = result["decision"]
    counts = result["counts"]
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "policy_resolution_completed": True,
        "resolution_outcome": decision.outcome,
        **counts,
        "protein_unknown_atom_policy": UNKNOWN_ATOM_POLICY,
        "ligand_unknown_atom_policy": UNKNOWN_ATOM_POLICY,
        "explicit_hydrogen_handling": EXPLICIT_HYDROGEN_POLICY,
        "supported_nonhydrogen_handling": SUPPORTED_NONHYDROGEN_POLICY,
        "unsupported_nonhydrogen_handling": UNSUPPORTED_NONHYDROGEN_POLICY,
        "missing_or_empty_type_symbol_handling": MISSING_OR_EMPTY_POLICY,
        "invalid_type_symbol_handling": INVALID_TYPE_SYMBOL_POLICY,
        "classification_authority": "explicit_type_symbol_only",
        "atom_name_inference_allowed": False,
        "checkpoint_categorical_width": 10,
        "checkpoint_channel_order": CHECKPOINT_CHANNEL_ORDER,
        "checkpoint_channel_order_preserved": True,
        "preview_11d_channel_order": PREVIEW_CHANNEL_ORDER,
        "preview_or_intermediate_only": True,
        "preview_11d_checkpoint_authority": False,
        "others_channel_checkpoint_input_allowed": False,
        "silent_zero_vector_fallback_allowed": False,
        "new_unknown_channel_allowed": False,
        "observed_step12d_silent_zero_vector_behavior": True,
        "observed_step12d_behavior_allowed_final_training_policy": False,
        "checkpoint_config_dataset": "crossdock",
        "checkpoint_config_datadir_semantics": "processed_crossdock_noH_full",
        "checkpoint_config_pocket_representation": "full-atom",
        "checkpoint_config_normalize_factors": [1, 4],
        "projection_order": list(PROJECTION_ORDER),
        "hydrogen_filter_before_coordinate_centering": True,
        "hydrogen_filter_before_node_count": True,
        "hydrogen_filter_before_batch_membership": True,
        "hydrogen_filter_before_mask_projection": True,
        "hydrogen_filter_before_atom_pair_index_projection": True,
        "centering_node_set": "retained_ligand_plus_pocket_heavy_atoms",
        "shared_retained_heavy_projection_consumers": list(
            SHARED_PROJECTION_CONSUMERS
        ),
        "all_atom_rows_classified": decision.all_atom_rows_classified,
        "all_sample_projections_valid": decision.all_sample_projections_valid,
        "all_pair_indices_remapped": decision.all_pair_indices_remapped,
        "pair_projection_valid_count": len(result["sample_rows"]),
        "feature_semantics_audit_completed": True,
        "all_current_model_input_semantics_frozen": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "unknown_atom_runtime_enforcement_integrated": False,
        "checkpoint_compatibility_preserved": True,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "canonical_mask_tensors_materialized": False,
        "source_inventory_row_count": len(result["source_rows"]),
        "atom_disposition_matrix_row_count": len(result["disposition_rows"]),
        "sample_projection_matrix_row_count": len(result["sample_rows"]),
        "failure_matrix_row_count": len(result["failure_rows"]),
        "failure_matrix_all_cases_verified": all(
            row["verified"] for row in result["failure_rows"]
        ),
        "issue_inventory_row_count": len(result["issue_rows"]),
        "ready_for_tensor_label_loss_mask_contract_design": True,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "planned_covalent_model_modules": list(PLANNED_COVALENT_MODEL_MODULES),
        "integrated_covalent_model_module_count": 0,
        "tensorization_used": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "training_used": False,
        "raw_read": False,
        "raw_write": False,
        "provider_used": False,
        "network_used": False,
        "download_used": False,
        "evidence_sha256": {
            name: _sha(payload) for name, payload in evidence.items()
        },
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def build_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    result = (
        derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1(
            repo_root
        )
    )
    artifacts = _non_manifest_artifacts(result)
    artifacts[MANIFEST_FILE] = (
        json.dumps(_manifest(result, artifacts), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return artifacts
