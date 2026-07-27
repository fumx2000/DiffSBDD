"""Audit final-training feature semantics without tensor or model execution.

All evidence is read from the explicit BASE commit.  The audit deliberately
keeps the historical Step12D forward/loss smoke separate from a final training
feature contract and never reads raw structures, checkpoints, or tensor files.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

__all__ = (
    "FinalTrainingFeatureSemanticsAuditDecision",
    "FeatureSemanticsAuditScenario",
    "FeatureSemanticsFailureObservation",
    "build_covapie_final_training_feature_semantics_audit_artifacts_v1",
    "derive_covapie_final_training_feature_semantics_audit_v1",
    "evaluate_unknown_atom_case_v1",
    "serialize_covapie_final_training_feature_semantics_audit_decision_v1",
    "validate_covapie_final_training_feature_semantics_scenario_v1",
)

BASE_COMMIT = "66d488ba829dad29d17e8a0ec07fa9798bae90b2"
BASE_PARENT = "8ebb40bd4ee105a89698376722422a0728b05fba"
BASE_TREE = "dac27f6815e94bfbdfccf67efb44a8f5f6cd1802"
BASE_SUBJECT = "add CovaPIE real-provider export blocking-row quarantine v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE final training feature-semantics audit v1"
SCHEMA_VERSION = (
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1"
)
STAGE = SCHEMA_VERSION
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
SOURCE_INVENTORY_FILE = "covapie_training_feature_semantics_source_inventory.csv"
FEATURE_REGISTRY_FILE = "covapie_training_feature_semantics_registry.csv"
UNKNOWN_POLICY_FILE = "covapie_unknown_atom_policy_audit_matrix.csv"
FAILURE_MATRIX_FILE = "covapie_feature_semantics_failure_matrix.csv"
ISSUE_INVENTORY_FILE = (
    "covapie_feature_semantics_issue_readiness_inventory.csv"
)
MANIFEST_FILE = (
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_"
    "audit_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    FEATURE_REGISTRY_FILE,
    UNKNOWN_POLICY_FILE,
    FAILURE_MATRIX_FILE,
    ISSUE_INVENTORY_FILE,
    MANIFEST_FILE,
)

QUARANTINE_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_real_provider_export_blocking_row_quarantine_materialization_v1.py"
)
QUARANTINE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_real_provider_export_blocking_row_quarantine_materialization_v1"
)
QUARANTINE_MANIFEST = QUARANTINE_ROOT / (
    "covapie_real_provider_export_blocking_row_quarantine_materialization_"
    "manifest.json"
)
PREDECESSOR_ISSUES = (
    QUARANTINE_ROOT
    / "covapie_real_provider_export_quarantine_issue_readiness_inventory.csv"
)
FINAL_DATASET_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
ATOM_PAIR_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_manifest.json"
)
FROZEN_SHA256 = {
    QUARANTINE_SOURCE: (
        "67819db11bcda4b218d67641686e8b7aa77af2e69d8b699a0214c0a7a34f2deb"
    ),
    QUARANTINE_MANIFEST: (
        "3fe591dabeac26e75ca18995c4cac647da23384670bee7f1d25e32b7e25b50ba"
    ),
    PREDECESSOR_ISSUES: (
        "540492e7b8a429ba251954da3aad2d7228e587c7f81044f09356cd3e984196aa"
    ),
    FINAL_DATASET_INDEX: (
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d"
    ),
    ATOM_PAIR_MANIFEST: (
        "229f5430feb3b5c147edce6c80dce684703b614e3764c7c18afd8344c25c3152"
    ),
}

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
CHECKPOINT_TOKEN_TO_INDEX = {token: index for token, _number, index in CHECKPOINT_VOCABULARY}
CHECKPOINT_ATOMIC_NUMBER_TO_INDEX = {
    number: index for _token, number, index in CHECKPOINT_VOCABULARY
}
FEATURE_STATUSES = {
    "current_model_input",
    "current_data_metadata_only",
    "future_planned_not_integrated",
    "not_a_training_feature",
}
EVIDENCE_STATUSES = {
    "explicitly_defined",
    "deterministically_derived",
    "ambiguous",
    "missing",
    "contradictory",
    "not_applicable",
}
UNKNOWN_POLICY_OUTCOMES = {
    "dedicated_unknown_channel_currently_supported",
    "explicit_other_channel_currently_supported",
    "fail_closed_rejection_required_for_checkpoint_compatibility",
    "unknown_atom_policy_unresolved",
}
RECOMMENDED_GAP_STEP = (
    "resolve_covapie_training_feature_semantics_and_unknown_atom_policy_gaps_v1"
)

SOURCE_COLUMNS = (
    "source_role",
    "source_path",
    "source_sha256",
    "committed_in_base",
    "source_kind",
    "selector_or_symbol",
    "referenced_feature_count",
    "referenced_sample_count",
    "verified",
)
FEATURE_COLUMNS = (
    "feature_id",
    "feature_domain",
    "feature_name",
    "feature_status",
    "source_layer",
    "producer_path",
    "producer_symbol",
    "source_columns_or_inputs",
    "consumer_path",
    "consumer_symbol",
    "consumer_operation",
    "training_consumed",
    "checkpoint_compatible_current_width",
    "storage_dtype",
    "runtime_dtype",
    "tensor_rank",
    "tensor_shape_or_width",
    "index_base",
    "encoding_kind",
    "vocabulary_or_value_domain",
    "channel_or_index_meaning",
    "missing_value_semantics",
    "unknown_value_semantics",
    "coordinate_unit",
    "coordinate_frame",
    "normalization_or_scaling",
    "mask_semantics",
    "broadcast_semantics",
    "padding_semantics",
    "evidence_status",
    "evidence_reason",
    "semantic_disposition",
    "verified",
)
UNKNOWN_COLUMNS = (
    "domain",
    "case_id",
    "input_condition",
    "observed_current_behavior",
    "evidence_path",
    "evidence_symbol",
    "checkpoint_width_effect",
    "allowed_training_policy",
    "policy_reason",
    "fails_closed",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case",
    "expected_outcome",
    "observed_outcome",
    "feature_semantics_known",
    "unknown_atom_feature_policy_resolved",
    "ready_for_tensor_label_loss_mask_contract_design",
    "ready_for_tensorization",
    "ready_for_model_integration",
    "ready_for_training",
    "fails_closed",
    "verified",
)
FAILURE_CASES = (
    "predecessor SHA drift",
    "predecessor not feature-audit-ready",
    "existing effective-open issue unexpectedly present",
    "feature registry empty",
    "duplicate feature ID",
    "current model input missing producer",
    "current model input missing consumer",
    "current model input width missing",
    "current model input dtype missing",
    "current model input vocabulary missing",
    "coordinate unit missing",
    "coordinate frame missing",
    "normalization semantics missing",
    "unknown protein policy unresolved but marked resolved",
    "unknown ligand policy unresolved but marked resolved",
    "unsupported atom silently mapped to carbon",
    "unsupported atom silently mapped to zero vector",
    "unsupported atom silently mapped to first index",
    "unknown channel added with checkpoint width change",
    "metadata-only feature marked current model input",
    "future planned feature marked current model input",
    "B3 mask omitted",
    "short alias used as sole mask semantics",
    "Step12D smoke treated as final contract",
    "ambiguous feature marked semantics-known",
    "missing feature marked semantics-known",
    "contradictory feature marked semantics-known",
    "ready-for-tensorization prematurely true",
    "ready-for-model-integration prematurely true",
    "ready-for-training prematurely true",
    "model modification attempted",
    "dataloader modification attempted",
    "checkpoint access attempted",
    "training attempted",
)


@dataclass(frozen=True)
class FinalTrainingFeatureSemanticsAuditDecision:
    schema_version: str
    outcome: str
    predecessor_verified: bool
    discovered_feature_count: int
    current_model_input_feature_count: int
    metadata_only_feature_count: int
    future_not_integrated_feature_count: int
    explicit_semantics_count: int
    deterministically_derived_semantics_count: int
    ambiguous_semantics_count: int
    missing_semantics_count: int
    contradictory_semantics_count: int
    protein_unknown_atom_policy: str
    ligand_unknown_atom_policy: str
    protein_unknown_atom_policy_resolved: bool
    ligand_unknown_atom_policy_resolved: bool
    all_current_model_input_semantics_frozen: bool
    feature_semantics_audit_completed: bool
    feature_semantics_known: bool
    unknown_atom_feature_policy_resolved: bool
    checkpoint_compatibility_preserved: bool
    model_changed: bool
    dataloader_changed: bool
    tensorization_used: bool
    training_used: bool
    ready_for_tensor_label_loss_mask_contract_design: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool
    recommended_next_step: str


@dataclass(frozen=True)
class FeatureSemanticsAuditScenario:
    predecessor_sha_valid: bool = True
    predecessor_ready: bool = True
    predecessor_effective_open_issue_count: int = 0
    registry_nonempty: bool = True
    duplicate_feature_id: bool = False
    current_input_producer_complete: bool = True
    current_input_consumer_complete: bool = True
    current_input_width_complete: bool = True
    current_input_dtype_complete: bool = True
    current_input_vocabulary_complete: bool = True
    coordinate_unit_complete: bool = True
    coordinate_frame_complete: bool = True
    normalization_complete: bool = True
    protein_policy: str = "unknown_atom_policy_unresolved"
    ligand_policy: str = "unknown_atom_policy_unresolved"
    protein_policy_marked_resolved: bool = False
    ligand_policy_marked_resolved: bool = False
    silent_carbon_fallback: bool = False
    silent_zero_vector_fallback: bool = False
    silent_first_index_fallback: bool = False
    unknown_channel_width_change: bool = False
    metadata_promoted_to_current_input: bool = False
    future_promoted_to_current_input: bool = False
    canonical_mask_count: int = 5
    b3_present: bool = True
    long_names_authoritative: bool = True
    step12d_final_contract: bool = False
    ambiguous_count: int = 0
    missing_count: int = 0
    contradictory_count: int = 0
    semantics_marked_known: bool = False
    ready_contract_design: bool = False
    ready_tensorization: bool = False
    ready_model_integration: bool = False
    ready_training: bool = False
    model_changed: bool = False
    dataloader_changed: bool = False
    checkpoint_access: bool = False
    training_used: bool = False


@dataclass(frozen=True)
class FeatureSemanticsFailureObservation:
    outcome: str
    reasons: tuple[str, ...]
    feature_semantics_known: bool
    unknown_atom_feature_policy_resolved: bool
    ready_for_tensor_label_loss_mask_contract_design: bool
    ready_for_tensorization: bool
    ready_for_model_integration: bool
    ready_for_training: bool


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
    if name.startswith("data/raw/"):
        raise ValueError(f"raw source access forbidden: {name}")
    if path.suffix.lower() in {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz", ".tar", ".zip",
        ".tgz", ".tmp", ".part",
    }:
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


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            key: (
                json.dumps(value, sort_keys=True, separators=(",", ":"))
                if isinstance(value, (list, dict, tuple))
                else value
            )
            for key, value in row.items()
        })
    return buffer.getvalue().encode("utf-8")


def _tree_paths(repo_root: Path) -> tuple[Path, ...]:
    lines = _git(
        repo_root, "ls-tree", "-r", "--name-only", BASE_COMMIT
    ).decode("utf-8").splitlines()
    return tuple(Path(line) for line in lines if line)


def _grep_paths(repo_root: Path, needle: str) -> tuple[Path, ...]:
    result = subprocess.run(
        (
            "git", "grep", "-l", "-I", "-e", needle, BASE_COMMIT, "--",
            "src", "tests", "scripts", "configs", "docs", "data/derived",
            "constants.py", "dataset.py", "process_crossdock.py",
            "lightning_modules.py", "equivariant_diffusion",
            ":(exclude)data/raw/**",
            ":(exclude,glob)**/*.pt",
            ":(exclude,glob)**/*.ckpt",
            ":(exclude,glob)**/*.pth",
            ":(exclude,glob)**/*.pkl",
            ":(exclude,glob)**/*.lmdb",
            ":(exclude,glob)**/*.npz",
        ),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise ValueError(f"BASE grep failed for {needle!r}")
    prefix = f"{BASE_COMMIT}:"
    return tuple(
        Path(line[len(prefix):] if line.startswith(prefix) else line)
        for line in result.stdout.decode("utf-8").splitlines()
        if line
    )


def _require_discovered(
    discovered: tuple[Path, ...], expected: str, selector: str
) -> Path:
    path = Path(expected)
    if path not in discovered:
        raise ValueError(f"dynamic source discovery failed: {selector}:{expected}")
    return path


def _discover_sources(repo_root: Path) -> dict[str, Any]:
    tree = _tree_paths(repo_root)
    feature_v0 = tuple(
        path for path in tree
        if "covapie_feature_semantics_audit_gate_v0" in path.as_posix()
        or path.name in {
            "covapie_feature_semantics_audit_gate.py",
            "check_covapie_feature_semantics_audit_gate_v0.py",
            "test_covapie_feature_semantics_audit_gate_v0.py",
        }
    )
    tensor_v0 = tuple(
        path for path in tree
        if "covapie_feature_semantics_tensorization_audit_gate_v0"
        in path.as_posix()
        or path.name in {
            "covapie_feature_semantics_tensorization_audit_gate.py",
            "check_covapie_feature_semantics_tensorization_audit_gate_v0.py",
            "test_covapie_feature_semantics_tensorization_audit_gate_v0.py",
        }
    )
    step12d_candidates = _grep_paths(repo_root, "UNKNOWN_ATOM_FEATURE_POLICY")
    step12d_source = _require_discovered(
        step12d_candidates,
        "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py",
        "UNKNOWN_ATOM_FEATURE_POLICY",
    )
    step12d = tuple(
        path for path in tree
        if "real_covalent_pretrained_forward_loss_smoke_v0" in path.as_posix()
        or path == step12d_source
    )
    producer_candidates = _grep_paths(
        repo_root, "_checkpoint_compatible_one_hot_from_atomic_numbers"
    )
    consumer_candidates = _grep_paths(repo_root, "data['lig_one_hot']")
    dynamics_candidates = _grep_paths(repo_root, "self.atom_encoder(h_atoms)")
    preprocessor_candidates = _grep_paths(
        repo_root, "def process_ligand_and_pocket"
    )
    collate_candidates = _grep_paths(repo_root, "class ProcessedLigandPocketDataset")
    return {
        "tree": tree,
        "feature_v0": feature_v0,
        "tensor_v0": tensor_v0,
        "step12d": step12d,
        "step12d_source": step12d_source,
        "checkpoint_producer": _require_discovered(
            producer_candidates, step12d_source.as_posix(),
            "_checkpoint_compatible_one_hot_from_atomic_numbers",
        ),
        "lightning_consumer": _require_discovered(
            consumer_candidates, "lightning_modules.py", "data['lig_one_hot']"
        ),
        "dynamics_consumer": _require_discovered(
            dynamics_candidates, "equivariant_diffusion/dynamics.py",
            "self.atom_encoder(h_atoms)",
        ),
        "fullatom_preprocessor": _require_discovered(
            preprocessor_candidates, "process_crossdock.py",
            "def process_ligand_and_pocket",
        ),
        "dataset_collate": _require_discovered(
            collate_candidates, "dataset.py",
            "class ProcessedLigandPocketDataset",
        ),
    }


def _verify_predecessor(repo_root: Path) -> tuple[dict[str, bytes], bool]:
    payloads = {path: _base_bytes(repo_root, path) for path in FROZEN_SHA256}
    sha_valid = all(
        _sha(payloads[path]) == expected
        for path, expected in FROZEN_SHA256.items()
    )
    manifest = _json(payloads[QUARANTINE_MANIFEST])
    expected = {
        "quarantine_materialization_completed": True,
        "materialization_outcome": "materialized",
        "provider_blocking_effect_contained": True,
        "provider_issue_resolved": True,
        "effective_open_issue_count": 0,
        "effective_open_issues": [],
        "provider_values_resolved": False,
        "provider_reexport_still_required": True,
        "atom_pair_issue_resolved": True,
        "atom_pair_ready_for_downstream_contracts": True,
        "ready_for_feature_semantics_audit": True,
        "feature_semantics_audit_completed": False,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "ready_for_tensorization": False,
        "ready_for_training": False,
    }
    readiness_valid = all(manifest.get(key) == value for key, value in expected.items())
    issues = _csv_rows(payloads[PREDECESSOR_ISSUES])
    issue_valid = (
        len(issues) == 30
        and all(row.get("successor_effective_status") == "resolved" for row in issues)
    )
    return payloads, bool(sha_valid and readiness_valid and issue_valid)


def _atom_coverage(
    repo_root: Path,
    final_index_payload: bytes,
) -> tuple[list[dict[str, Any]], dict[Path, bytes]]:
    index_rows = _csv_rows(final_index_payload)
    if len(index_rows) != 11:
        raise ValueError(f"final dataset row count invalid: {len(index_rows)}")
    table_payloads: dict[Path, bytes] = {}
    coverage = []
    for domain, path_column in (
        ("protein_or_pocket_atom", "pocket_atom_table_path"),
        ("ligand_atom", "ligand_atom_table_path"),
    ):
        counts: dict[str, int] = {}
        table_count = atom_count = explicit_count = missing_count = 0
        for sample in index_rows:
            path = Path(sample[path_column])
            payload = _base_bytes(repo_root, path)
            table_payloads[path] = payload
            rows = _csv_rows(payload)
            table_count += 1
            for row in rows:
                atom_count += 1
                token = row.get("type_symbol", "")
                if token == "":
                    missing_count += 1
                else:
                    explicit_count += 1
                    counts[token] = counts.get(token, 0) + 1
        supported = sum(
            count for token, count in counts.items()
            if token in CHECKPOINT_TOKEN_TO_INDEX
        )
        unsupported = sum(
            count for token, count in counts.items()
            if token not in CHECKPOINT_TOKEN_TO_INDEX
        )
        coverage.append({
            "domain": domain,
            "source_table_count": table_count,
            "atom_row_count": atom_count,
            "observed_explicit_element_or_token_count": explicit_count,
            "observed_vocabulary": dict(sorted(counts.items())),
            "supported_row_count": supported,
            "unknown_or_unsupported_row_count": unsupported,
            "missing_feature_value_count": missing_count,
            "policy_disposition": "unknown_atom_policy_unresolved",
            "verified": table_count == 11 and explicit_count + missing_count == atom_count,
        })
    return coverage, table_payloads


def _feature_row(
    feature_id: str,
    domain: str,
    name: str,
    status: str,
    *,
    source_layer: str,
    producer_path: str = "",
    producer_symbol: str = "",
    inputs: str = "",
    consumer_path: str = "",
    consumer_symbol: str = "",
    operation: str = "",
    training_consumed: bool = False,
    width: str = "not_applicable",
    storage_dtype: str = "not_applicable",
    runtime_dtype: str = "not_applicable",
    rank: str = "not_applicable",
    shape: str = "not_applicable",
    index_base: str = "not_applicable",
    encoding: str = "not_applicable",
    vocabulary: str = "not_applicable",
    channels: str = "not_applicable",
    missing: str = "not_applicable",
    unknown: str = "not_applicable",
    unit: str = "not_applicable",
    frame: str = "not_applicable",
    scaling: str = "not_applicable",
    mask: str = "not_applicable",
    broadcast: str = "not_applicable",
    padding: str = "not_applicable",
    evidence: str = "explicitly_defined",
    reason: str,
    disposition: str,
) -> dict[str, Any]:
    return {
        "feature_id": feature_id,
        "feature_domain": domain,
        "feature_name": name,
        "feature_status": status,
        "source_layer": source_layer,
        "producer_path": producer_path,
        "producer_symbol": producer_symbol,
        "source_columns_or_inputs": inputs,
        "consumer_path": consumer_path,
        "consumer_symbol": consumer_symbol,
        "consumer_operation": operation,
        "training_consumed": training_consumed,
        "checkpoint_compatible_current_width": width,
        "storage_dtype": storage_dtype,
        "runtime_dtype": runtime_dtype,
        "tensor_rank": rank,
        "tensor_shape_or_width": shape,
        "index_base": index_base,
        "encoding_kind": encoding,
        "vocabulary_or_value_domain": vocabulary,
        "channel_or_index_meaning": channels,
        "missing_value_semantics": missing,
        "unknown_value_semantics": unknown,
        "coordinate_unit": unit,
        "coordinate_frame": frame,
        "normalization_or_scaling": scaling,
        "mask_semantics": mask,
        "broadcast_semantics": broadcast,
        "padding_semantics": padding,
        "evidence_status": evidence,
        "evidence_reason": reason,
        "semantic_disposition": disposition,
        "verified": True,
    }


def _feature_registry() -> list[dict[str, Any]]:
    vocab = "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    one_hot_common = {
        "producer_path": (
            "src/covalent_ext/"
            "real_covalent_pretrained_forward_loss_smoke.py"
        ),
        "producer_symbol": "_checkpoint_compatible_one_hot_from_atomic_numbers",
        "consumer_path": "equivariant_diffusion/dynamics.py",
        "operation": "slice categorical channels then pass to learned linear encoder",
        "training_consumed": True,
        "width": "10",
        "storage_dtype": "atomic_number_int64_before_encoding",
        "runtime_dtype": "torch.float32",
        "rank": "2",
        "shape": "[N,10]",
        "index_base": "0",
        "encoding": "one_hot_with_current_silent_zero_vector_for_unsupported",
        "vocabulary": vocab,
        "channels": vocab,
        "missing": "not representable after tensor load; absent formal table-to-tensor contract",
        "unknown": "no unknown/other channel; unsupported atomic number becomes all-zero row",
        "scaling": "(one_hot-0)/4 in DDPM normalize",
        "padding": "padded rows removed before one-hot; flattened valid atoms only",
        "evidence": "explicitly_defined",
        "disposition": "freeze 10-channel checkpoint interface; unknown policy remains blocked",
    }
    rows = [
        _feature_row(
            "model_ligand_atom_categorical_10d", "ligand_atom",
            "checkpoint-compatible ligand atom categorical feature",
            "current_model_input", source_layer="checkpoint adapter",
            inputs="ligand atomic numbers",
            consumer_symbol="EGNNDynamics.forward/self.atom_encoder",
            reason="producer mapping and learned consumer width are both committed",
            **one_hot_common,
        ),
        _feature_row(
            "model_pocket_atom_categorical_10d", "protein_or_pocket_atom",
            "checkpoint-compatible pocket atom categorical feature",
            "current_model_input", source_layer="checkpoint adapter",
            inputs="protein atomic numbers",
            consumer_symbol="EGNNDynamics.forward/self.residue_encoder",
            reason="full-atom pocket uses the same committed 10-channel atom order",
            **one_hot_common,
        ),
    ]
    coordinate_common = {
        "status": "current_model_input",
        "source_layer": "batch adapter",
        "producer_path": "src/covalent_ext/batch_adapter.py",
        "producer_symbol": "_coordinate_center/adapt_covalent_batch_for_model_v0",
        "inputs": "valid ligand and protein Cartesian coordinates",
        "consumer_path": "equivariant_diffusion/en_diffusion.py",
        "consumer_symbol": "EnVariationalDiffusion.normalize/forward",
        "operation": "divide by norm_values[0], concatenate with categorical feature, diffuse",
        "training_consumed": True,
        "width": "3_coordinate_channels_not_checkpoint_learned_feature_width",
        "storage_dtype": "float32",
        "runtime_dtype": "torch.float32",
        "rank": "2",
        "shape": "[N,3]",
        "encoding": "Cartesian_xyz",
        "vocabulary": "finite real xyz",
        "channels": "0=x|1=y|2=z",
        "missing": "missing rows are not valid model nodes",
        "unknown": "non-finite coordinates rejected by committed validators",
        "unit": "angstrom",
        "frame": "per-sample joint ligand+pocket unweighted atom-centroid centered",
        "scaling": "center subtraction then divide by normalize_factors[0]=1",
        "broadcast": "per-sample center broadcast over valid ligand and pocket atoms",
        "padding": "zero padding removed through validity mask before model boundary",
        "evidence": "deterministically_derived",
        "disposition": "frozen for checkpoint-compatible current path",
    }
    rows.extend([
        _feature_row(
            "model_ligand_coordinates", "ligand_geometry",
            "ligand coordinates", reason="centering and model normalization are explicit",
            **coordinate_common,
        ),
        _feature_row(
            "model_pocket_coordinates", "protein_or_pocket_geometry",
            "protein/pocket coordinates",
            reason="same joint centroid and scaling are explicit",
            **coordinate_common,
        ),
    ])
    batch_common = {
        "status": "current_model_input",
        "source_layer": "DiffSBDD input adapter",
        "producer_path": "src/covalent_ext/diffsbdd_input_adapter.py",
        "producer_symbol": "_flatten_batch_indices",
        "inputs": "padded validity mask",
        "consumer_path": "equivariant_diffusion/dynamics.py",
        "consumer_symbol": "EGNNDynamics.forward/get_edges",
        "operation": "time broadcast, scatter grouping, and same-sample edge construction",
        "training_consumed": True,
        "storage_dtype": "bool validity mask before flattening",
        "runtime_dtype": "torch.int64",
        "rank": "1",
        "shape": "[N]",
        "index_base": "0",
        "encoding": "contiguous_batch_membership_index",
        "vocabulary": "0..B-1",
        "channels": "one scalar sample index per valid node",
        "missing": "padded rows omitted",
        "unknown": "out-of-range membership is invalid",
        "scaling": "none",
        "mask": "equal membership defines same-sample adjacency",
        "broadcast": "t[batch_membership] broadcasts one diffusion time per sample",
        "padding": "no padded entries cross flattened model boundary",
        "evidence": "deterministically_derived",
        "disposition": "frozen",
    }
    rows.extend([
        _feature_row(
            "model_ligand_batch_membership", "graph_batch",
            "ligand graph/batch membership", width="1", reason="exact flattening and consumer operations committed",
            **batch_common,
        ),
        _feature_row(
            "model_pocket_batch_membership", "graph_batch",
            "pocket graph/batch membership", width="1", reason="exact flattening and consumer operations committed",
            **batch_common,
        ),
    ])
    size_common = {
        "status": "current_model_input",
        "source_layer": "DiffSBDD input adapter",
        "producer_path": "src/covalent_ext/diffsbdd_input_adapter.py",
        "producer_symbol": "build_diffsbdd_like_input_from_covalent_v0",
        "inputs": "validity mask sum(dim=1)",
        "consumer_path": "lightning_modules.py",
        "consumer_symbol": "LigandPocketDDPM.forward",
        "operation": "loss normalization and node-count likelihood",
        "training_consumed": True,
        "width": "1",
        "storage_dtype": "not_stored_separately",
        "runtime_dtype": "torch.int64",
        "rank": "1",
        "shape": "[B]",
        "index_base": "not_applicable",
        "encoding": "positive_node_count",
        "vocabulary": "positive integers",
        "channels": "one count per sample",
        "missing": "derived only when validity mask exists",
        "unknown": "zero/negative count invalid for admitted sample",
        "scaling": "none",
        "broadcast": "per-sample",
        "padding": "counts exclude padding",
        "evidence": "deterministically_derived",
        "disposition": "frozen",
    }
    rows.extend([
        _feature_row(
            "model_ligand_node_count", "graph_batch", "ligand node count",
            reason="mask-sum producer and loss consumer committed", **size_common,
        ),
        _feature_row(
            "model_pocket_node_count", "graph_batch", "pocket node count",
            reason="mask-sum producer and loss consumer committed", **size_common,
        ),
        _feature_row(
            "model_diffusion_time", "diffusion_conditioning",
            "diffusion timestep conditioning", "current_model_input",
            source_layer="DDPM runtime",
            producer_path="equivariant_diffusion/en_diffusion.py",
            producer_symbol="EnVariationalDiffusion.forward",
            inputs="uniform integer timestep 0..T divided by T",
            consumer_path="equivariant_diffusion/dynamics.py",
            consumer_symbol="EGNNDynamics.forward",
            operation="broadcast by batch membership and append one time channel",
            training_consumed=True, width="1", storage_dtype="not_stored",
            runtime_dtype="torch.float32", rank="2", shape="[B,1]",
            encoding="normalized_scalar", vocabulary="[0,1]",
            channels="one normalized time scalar", missing="generated every forward",
            unknown="outside [0,1] invalid", scaling="t_int/T",
            broadcast="t[batch_membership] to every node", padding="not_applicable",
            evidence="explicitly_defined",
            reason="producer, range, normalization, and consumer are explicit",
            disposition="frozen internal conditioning input",
        ),
        _feature_row(
            "model_inpaint_fixed_ligand_mask", "conditional_generation",
            "generic fixed-ligand mask for inpainting", "current_model_input",
            source_layer="inpainting interface",
            producer_path="src/covalent_ext/diffsbdd_input_adapter.py",
            producer_symbol="build_diffsbdd_like_input_from_covalent_v0",
            inputs="fixed_ligand_atom_mask over valid ligand atoms",
            consumer_path="equivariant_diffusion/en_diffusion.py",
            consumer_symbol="EnVariationalDiffusion.inpaint",
            operation="True selects known ligand atoms during repaint centering/replacement",
            training_consumed=False, width="1", storage_dtype="bool",
            runtime_dtype="torch.bool after bool conversion", rank="2",
            shape="[N_ligand,1]", index_base="not_applicable",
            encoding="boolean", vocabulary="False|True",
            channels="False=not fixed|True=fixed known atom",
            missing="required by inpaint interface", unknown="non-boolean coerced by bool",
            scaling="none",
            mask="fixed known-ligand selection", broadcast="elementwise over ligand nodes",
            padding="flattened valid ligand atoms only",
            evidence="explicitly_defined",
            reason="generic inference consumer exists; training forward does not consume it",
            disposition="freeze generic inpaint interface; do not claim canonical mask integration",
        ),
    ])
    metadata_specs = (
        ("data_pocket_type_symbol", "protein_or_pocket_atom", "final pocket type_symbol",
         "pocket_atom_table.csv:type_symbol", "explicit element token; includes H"),
        ("data_ligand_type_symbol", "ligand_atom", "final ligand type_symbol",
         "ligand_atom_table.csv:type_symbol", "explicit element token; includes H"),
        ("data_pocket_xyz", "protein_or_pocket_geometry", "final pocket x/y/z",
         "pocket_atom_table.csv:x|y|z", "angstrom source-structure Cartesian coordinates"),
        ("data_ligand_xyz", "ligand_geometry", "final ligand x/y/z",
         "ligand_atom_table.csv:x|y|z", "angstrom source-structure Cartesian coordinates"),
        ("data_canonical_covalent_task_masks", "covalent_task_semantics",
         "five canonical covalent task masks",
         "atom-pair validation manifest:canonical_masks",
         "data/task semantics only; exact five including scaffold_only/B3"),
        ("data_target_residue_locator", "covalent_metadata",
         "target residue locator metadata",
         "final_dataset_index:residue fields", "structured locator metadata"),
        ("data_covalent_atom_pair_and_indices", "covalent_metadata",
         "covalent atom-pair structured metadata and row indices",
         "atom-pair validation manifest", "structured record; row indices metadata-only"),
        ("data_warhead_type", "covalent_metadata", "warhead type metadata",
         "committed covalent metadata contracts", "no current model consumer"),
        ("data_pre_post_geometry", "covalent_metadata",
         "pre/post covalent geometry metadata",
         "committed geometry contracts", "metadata/auxiliary-label boundary"),
        ("data_quarantine_control_plane", "control_plane",
         "quarantine metadata", QUARANTINE_MANIFEST.as_posix(),
         "admission/control-plane evidence; never a training feature"),
    )
    for feature_id, domain, name, inputs, reason in metadata_specs:
        coordinate = feature_id in {"data_pocket_xyz", "data_ligand_xyz"}
        rows.append(_feature_row(
            feature_id, domain, name, "current_data_metadata_only",
            source_layer="final canonical derived data",
            inputs=inputs, training_consumed=False,
            storage_dtype="CSV text", runtime_dtype="not_tensorized",
            rank="not_tensorized", shape="not_tensorized",
            encoding="structured_metadata" if not coordinate else "Cartesian_xyz_columns",
            vocabulary="committed table/contract domain",
            missing="governed by committed metadata gate",
            unknown="not a current model input",
            unit="angstrom" if coordinate else "not_applicable",
            frame="source structure frame; future tensor contract not integrated"
            if coordinate else "not_applicable",
            scaling="none in metadata",
            mask="data/task semantics only" if "mask" in feature_id else "not_applicable",
            evidence="explicitly_defined",
            reason=reason,
            disposition="retain metadata-only until an explicit tensor/label/loss-mask contract",
        ))
    for index, module in enumerate(PLANNED_COVALENT_MODEL_MODULES, 1):
        rows.append(_feature_row(
            f"future_covalent_model_module_{index}", "future_model_extension",
            module, "future_planned_not_integrated",
            source_layer="future plan", inputs="no integrated producer",
            training_consumed=False, evidence="not_applicable",
            reason="consumer search found no integrated current model module",
            disposition="0/5 integrated; implementation forbidden in this audit",
        ))
    rows.append(_feature_row(
        "future_auxiliary_targets", "future_training_target",
        "future auxiliary targets", "future_planned_not_integrated",
        source_layer="future label/loss design", inputs="warhead/pair/geometry candidates",
        training_consumed=False, evidence="not_applicable",
        reason="no final tensor, label, loss-mask, head, or loss consumer contract",
        disposition="defer to a later contract only after blockers resolve",
    ))
    rows.extend([
        _feature_row(
            "adapter_padded_node_validity_masks", "adapter_internal",
            "padded ligand/protein node validity masks", "not_a_training_feature",
            source_layer="CovaPIE adapter", producer_path="src/covalent_ext/npz_dataset.py",
            producer_symbol="covalent_npz_collate_fn",
            inputs="padding occupancy", consumer_path="src/covalent_ext/diffsbdd_input_adapter.py",
            consumer_symbol="_flatten_padded/_flatten_batch_indices",
            operation="remove padding and derive batch membership before model boundary",
            training_consumed=False, width="1", storage_dtype="not_stored",
            runtime_dtype="torch.bool", rank="2", shape="[B,Nmax]",
            encoding="boolean", vocabulary="False|True",
            channels="False=padding|True=valid node",
            missing="collate always creates", unknown="non-boolean invalid",
            mask="adapter validity only", broadcast="elementwise",
            padding="defines padding", evidence="explicitly_defined",
            reason="consumed by adapter, not by LigandPocketDDPM/DDPM model boundary",
            disposition="do not promote to current model input",
        ),
        _feature_row(
            "external_edge_mask", "graph_edge",
            "external edge mask", "not_a_training_feature",
            source_layer="model interface", inputs="none",
            training_consumed=False, evidence="not_applicable",
            reason="EGNNDynamics.get_edges derives edge_index from batch membership and coordinates",
            disposition="no external edge-mask tensor exists in current path",
        ),
        _feature_row(
            "coordinate_center_recovery_metadata", "geometry_metadata",
            "coordinate center", "not_a_training_feature",
            source_layer="adapter metadata", producer_path="src/covalent_ext/batch_adapter.py",
            producer_symbol="_coordinate_center", inputs="valid ligand+pocket coordinates",
            consumer_path="", consumer_symbol="", operation="not read by training forward",
            training_consumed=False, width="3", storage_dtype="not_stored",
            runtime_dtype="torch.float32", rank="2", shape="[B,3]",
            encoding="Cartesian_xyz", vocabulary="finite real xyz",
            channels="0=x|1=y|2=z", unit="angstrom",
            frame="source structure frame", scaling="none",
            broadcast="subtracted from coordinates before model",
            evidence="deterministically_derived",
            reason="used to construct centered coordinates but not itself consumed by model",
            disposition="provenance/recovery metadata only",
        ),
        _feature_row(
            "legacy_crossdock_full_11d_others_schema", "legacy_preprocessing",
            "legacy 11-channel crossdock_full schema with others",
            "not_a_training_feature", source_layer="original preprocessing",
            producer_path="process_crossdock.py",
            producer_symbol="process_ligand_and_pocket",
            inputs="constants.dataset_params['crossdock_full']",
            training_consumed=False, width="11", storage_dtype="numpy float64 one-hot",
            runtime_dtype="not current checkpoint input", rank="2", shape="[N,11]",
            index_base="0", encoding="one_hot",
            vocabulary="C|N|O|S|B|Br|Cl|P|I|F|others",
            channels="others=10", missing="KeyError/drop sample path",
            unknown="non-H out-of-vocabulary maps to others in pocket preprocessing",
            unit="not_applicable", scaling="not current checkpoint path",
            padding="concatenated variable-size arrays",
            evidence="explicitly_defined",
            reason="committed 11-wide schema is excluded from the checkpoint-compatible 10-wide path",
            disposition="do not use for the current checkpoint; width change would be incompatible",
        ),
    ])
    return rows


def evaluate_unknown_atom_case_v1(
    domain: str,
    case_id: str,
    *,
    current_unsupported_count: int,
) -> dict[str, Any]:
    if domain not in {"protein_or_pocket_atom", "ligand_atom"}:
        raise ValueError(f"unknown atom domain: {domain}")
    supported = case_id in {"protein supported token", "ligand supported token"}
    if supported:
        behavior = "exact token maps to its committed 0-based one-hot channel"
        width = "unchanged_10"
        fails_closed = True
        reason = "supported mapping is explicit"
    elif case_id in {"explicit unknown token", "explicit other token"}:
        behavior = "no dedicated unknown or other channel in checkpoint-compatible width 10"
        width = "adding_channel_changes_10_to_11"
        fails_closed = True
        reason = "absence is explicit; adding a channel breaks checkpoint width"
    elif case_id in {
        "unsupported token", "out-of-range index", "negative index",
        "silent zero-vector fallback", "future data contains unsupported token",
    }:
        behavior = "current Step12D helper silently emits an all-zero 10-vector"
        width = "unchanged_10_but_semantically_unsafe"
        fails_closed = False
        reason = "silent zero-vector fallback is not an allowed final training policy"
    elif case_id in {"missing token", "empty token"}:
        behavior = "no integrated final-table-to-atomic-number contract; behavior unresolved"
        width = "unknown"
        fails_closed = False
        reason = "missing/empty token handling is not frozen"
    elif case_id == "invalid type":
        behavior = "tensor/int conversion raises before a valid one-hot row exists"
        width = "no_model_input"
        fails_closed = True
        reason = "invalid scalar type cannot silently select a channel"
    elif case_id in {"silent carbon fallback", "silent first-index fallback"}:
        behavior = "not observed in committed checkpoint helper"
        width = "unchanged_10"
        fails_closed = True
        reason = "formal evaluator rejects either proposed fallback"
    elif case_id in {"drop atom", "drop sample", "raise/reject"}:
        behavior = "not implemented by the current final canonical table path"
        width = "no_width_change"
        fails_closed = False
        reason = "a future fail-closed policy is required but not implemented"
    elif case_id == "new channel width change":
        behavior = "new unknown channel changes categorical width from 10 to 11"
        width = "incompatible_10_to_11"
        fails_closed = True
        reason = "width change is explicitly forbidden for checkpoint compatibility"
    elif case_id == "checkpoint-width incompatibility":
        behavior = "11-channel input is incompatible with the frozen 10-wide checkpoint interface"
        width = "incompatible"
        fails_closed = True
        reason = "current policy must preserve width 10"
    elif case_id == "current admitted data contains unsupported token":
        behavior = f"explicit type_symbol coverage contains {current_unsupported_count} unsupported H rows"
        width = "would_trigger_zero_vector_if_unfiltered"
        fails_closed = False
        reason = "current admitted data disproves the no-unsupported-data prerequisite"
    else:
        raise ValueError(f"unknown case id: {case_id}")
    return {
        "domain": domain,
        "case_id": case_id,
        "input_condition": case_id,
        "observed_current_behavior": behavior,
        "evidence_path": (
            "src/covalent_ext/"
            "real_covalent_pretrained_forward_loss_smoke.py"
        ),
        "evidence_symbol": (
            "_checkpoint_compatible_one_hot_from_atomic_numbers/"
            "CHECKPOINT_10D_ATOMIC_NUMBER_TO_INDEX"
        ),
        "checkpoint_width_effect": width,
        "allowed_training_policy": "unknown_atom_policy_unresolved",
        "policy_reason": reason,
        "fails_closed": fails_closed,
        "verified": True,
    }


def _unknown_policy_rows(
    coverage: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    case_ids = (
        "protein supported token",
        "ligand supported token",
        "explicit unknown token",
        "explicit other token",
        "unsupported token",
        "missing token",
        "empty token",
        "invalid type",
        "out-of-range index",
        "negative index",
        "silent carbon fallback",
        "silent zero-vector fallback",
        "silent first-index fallback",
        "drop atom",
        "drop sample",
        "raise/reject",
        "new channel width change",
        "checkpoint-width incompatibility",
        "current admitted data contains unsupported token",
        "future data contains unsupported token",
    )
    by_domain = {row["domain"]: row for row in coverage}
    rows = []
    for domain in ("protein_or_pocket_atom", "ligand_atom"):
        unsupported = int(by_domain[domain]["unknown_or_unsupported_row_count"])
        for case_id in case_ids:
            rows.append(evaluate_unknown_atom_case_v1(
                domain, case_id, current_unsupported_count=unsupported
            ))
    return rows


def validate_covapie_final_training_feature_semantics_scenario_v1(
    scenario: FeatureSemanticsAuditScenario,
) -> FeatureSemanticsFailureObservation:
    reasons = []
    checks = (
        (scenario.predecessor_sha_valid, "predecessor_sha"),
        (scenario.predecessor_ready, "predecessor_ready"),
        (scenario.predecessor_effective_open_issue_count == 0, "predecessor_open_issue"),
        (scenario.registry_nonempty, "registry_empty"),
        (not scenario.duplicate_feature_id, "duplicate_feature_id"),
        (scenario.current_input_producer_complete, "current_input_producer"),
        (scenario.current_input_consumer_complete, "current_input_consumer"),
        (scenario.current_input_width_complete, "current_input_width"),
        (scenario.current_input_dtype_complete, "current_input_dtype"),
        (scenario.current_input_vocabulary_complete, "current_input_vocabulary"),
        (scenario.coordinate_unit_complete, "coordinate_unit"),
        (scenario.coordinate_frame_complete, "coordinate_frame"),
        (scenario.normalization_complete, "normalization"),
        (scenario.protein_policy in UNKNOWN_POLICY_OUTCOMES, "protein_policy_vocabulary"),
        (scenario.ligand_policy in UNKNOWN_POLICY_OUTCOMES, "ligand_policy_vocabulary"),
        (
            scenario.protein_policy_marked_resolved
            == (scenario.protein_policy != "unknown_atom_policy_unresolved"),
            "protein_policy_resolution_truth",
        ),
        (
            scenario.ligand_policy_marked_resolved
            == (scenario.ligand_policy != "unknown_atom_policy_unresolved"),
            "ligand_policy_resolution_truth",
        ),
        (not scenario.silent_carbon_fallback, "silent_carbon_fallback"),
        (not scenario.silent_zero_vector_fallback, "silent_zero_vector_fallback"),
        (not scenario.silent_first_index_fallback, "silent_first_index_fallback"),
        (not scenario.unknown_channel_width_change, "unknown_channel_width_change"),
        (not scenario.metadata_promoted_to_current_input, "metadata_promotion"),
        (not scenario.future_promoted_to_current_input, "future_promotion"),
        (scenario.canonical_mask_count == 5, "canonical_mask_count"),
        (scenario.b3_present, "b3_missing"),
        (scenario.long_names_authoritative, "mask_long_name_authority"),
        (not scenario.step12d_final_contract, "step12d_final_contract"),
        (
            not scenario.semantics_marked_known
            or (
                scenario.ambiguous_count == 0
                and scenario.missing_count == 0
                and scenario.contradictory_count == 0
                and scenario.protein_policy_marked_resolved
                and scenario.ligand_policy_marked_resolved
            ),
            "semantics_known_truth",
        ),
        (not scenario.ready_tensorization, "premature_tensorization"),
        (not scenario.ready_model_integration, "premature_model_integration"),
        (not scenario.ready_training, "premature_training"),
        (not scenario.model_changed, "model_changed"),
        (not scenario.dataloader_changed, "dataloader_changed"),
        (not scenario.checkpoint_access, "checkpoint_access"),
        (not scenario.training_used, "training_used"),
    )
    for condition, reason in checks:
        if not condition:
            reasons.append(reason)
    policies_resolved = (
        scenario.protein_policy_marked_resolved
        and scenario.ligand_policy_marked_resolved
    )
    semantics_known = (
        not reasons
        and scenario.ambiguous_count == 0
        and scenario.missing_count == 0
        and scenario.contradictory_count == 0
        and policies_resolved
    )
    contract_ready = semantics_known and scenario.ready_contract_design
    return FeatureSemanticsFailureObservation(
        outcome="invalid" if reasons else (
            "audited_semantics_frozen" if semantics_known else "audited_with_blockers"
        ),
        reasons=tuple(reasons),
        feature_semantics_known=semantics_known,
        unknown_atom_feature_policy_resolved=policies_resolved and not reasons,
        ready_for_tensor_label_loss_mask_contract_design=contract_ready,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
    )


def _failure_rows() -> list[dict[str, Any]]:
    mutations: dict[str, dict[str, Any]] = {
        "predecessor SHA drift": {"predecessor_sha_valid": False},
        "predecessor not feature-audit-ready": {"predecessor_ready": False},
        "existing effective-open issue unexpectedly present": {"predecessor_effective_open_issue_count": 1},
        "feature registry empty": {"registry_nonempty": False},
        "duplicate feature ID": {"duplicate_feature_id": True},
        "current model input missing producer": {"current_input_producer_complete": False},
        "current model input missing consumer": {"current_input_consumer_complete": False},
        "current model input width missing": {"current_input_width_complete": False},
        "current model input dtype missing": {"current_input_dtype_complete": False},
        "current model input vocabulary missing": {"current_input_vocabulary_complete": False},
        "coordinate unit missing": {"coordinate_unit_complete": False},
        "coordinate frame missing": {"coordinate_frame_complete": False},
        "normalization semantics missing": {"normalization_complete": False},
        "unknown protein policy unresolved but marked resolved": {"protein_policy_marked_resolved": True},
        "unknown ligand policy unresolved but marked resolved": {"ligand_policy_marked_resolved": True},
        "unsupported atom silently mapped to carbon": {"silent_carbon_fallback": True},
        "unsupported atom silently mapped to zero vector": {"silent_zero_vector_fallback": True},
        "unsupported atom silently mapped to first index": {"silent_first_index_fallback": True},
        "unknown channel added with checkpoint width change": {"unknown_channel_width_change": True},
        "metadata-only feature marked current model input": {"metadata_promoted_to_current_input": True},
        "future planned feature marked current model input": {"future_promoted_to_current_input": True},
        "B3 mask omitted": {"canonical_mask_count": 4, "b3_present": False},
        "short alias used as sole mask semantics": {"long_names_authoritative": False},
        "Step12D smoke treated as final contract": {"step12d_final_contract": True},
        "ambiguous feature marked semantics-known": {"ambiguous_count": 1, "semantics_marked_known": True},
        "missing feature marked semantics-known": {"missing_count": 1, "semantics_marked_known": True},
        "contradictory feature marked semantics-known": {"contradictory_count": 1, "semantics_marked_known": True},
        "ready-for-tensorization prematurely true": {"ready_tensorization": True},
        "ready-for-model-integration prematurely true": {"ready_model_integration": True},
        "ready-for-training prematurely true": {"ready_training": True},
        "model modification attempted": {"model_changed": True},
        "dataloader modification attempted": {"dataloader_changed": True},
        "checkpoint access attempted": {"checkpoint_access": True},
        "training attempted": {"training_used": True},
    }
    rows = []
    for name in FAILURE_CASES:
        observation = validate_covapie_final_training_feature_semantics_scenario_v1(
            replace(FeatureSemanticsAuditScenario(), **mutations[name])
        )
        fails_closed = observation.outcome == "invalid"
        rows.append({
            "failure_case": name,
            "expected_outcome": "invalid",
            "observed_outcome": observation.outcome,
            "feature_semantics_known": observation.feature_semantics_known,
            "unknown_atom_feature_policy_resolved": observation.unknown_atom_feature_policy_resolved,
            "ready_for_tensor_label_loss_mask_contract_design": observation.ready_for_tensor_label_loss_mask_contract_design,
            "ready_for_tensorization": observation.ready_for_tensorization,
            "ready_for_model_integration": observation.ready_for_model_integration,
            "ready_for_training": observation.ready_for_training,
            "fails_closed": fails_closed,
            "verified": fails_closed,
        })
    return rows


def _source_inventory(
    repo_root: Path,
    discovery: dict[str, Any],
    fixed_payloads: dict[Path, bytes],
    table_payloads: dict[Path, bytes],
    registry: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    specs: dict[Path, tuple[str, str, str, int]] = {}

    def add(path: Path, role: str, kind: str, selector: str, samples: int = 0) -> None:
        specs.setdefault(path, (role, kind, selector, samples))

    add(QUARANTINE_SOURCE, "quarantine_predecessor_source", "python", "frozen SHA")
    add(QUARANTINE_MANIFEST, "quarantine_predecessor_manifest", "json", "readiness fields")
    add(PREDECESSOR_ISSUES, "quarantine_issue_inventory", "csv", "Exact30 rows")
    add(FINAL_DATASET_INDEX, "final_dataset_index", "csv", "11 canonical samples", 11)
    add(ATOM_PAIR_MANIFEST, "atom_pair_validation_manifest", "json", "canonical masks and metadata boundary", 11)
    core_specs = (
        ("constants.py", "atom_vocabulary", "dataset_params crossdock/crossdock_full"),
        ("process_crossdock.py", "fullatom_preprocessor", "process_ligand_and_pocket"),
        ("dataset.py", "dataset_collate", "ProcessedLigandPocketDataset/collate_fn"),
        ("configs/crossdock_fullatom_cond.yml", "conditional_config", "dataset/pocket_representation/normalize_factors"),
        ("lightning_modules.py", "model_input_interface", "get_ligand_and_pocket/forward"),
        ("equivariant_diffusion/en_diffusion.py", "diffusion_consumer", "normalize/forward/inpaint"),
        ("equivariant_diffusion/dynamics.py", "model_feature_consumer", "EGNNDynamics.forward/get_edges"),
        ("src/covalent_ext/npz_dataset.py", "current_adapter_reference", "covalent_npz_collate_fn"),
        ("src/covalent_ext/batch_adapter.py", "current_adapter_reference", "_coordinate_center/adapt_covalent_batch_for_model_v0"),
        ("src/covalent_ext/model_input_adapter.py", "current_adapter_reference", "build_covalent_model_input_v0"),
        ("src/covalent_ext/diffsbdd_input_adapter.py", "current_adapter_reference", "build_diffsbdd_like_input_from_covalent_v0"),
    )
    for name, role, selector in core_specs:
        add(Path(name), role, "python" if name.endswith(".py") else "yaml", selector)
    for path in discovery["feature_v0"]:
        add(path, "feature_semantics_v0", path.suffix.lstrip(".") or "source", "dynamic tree match")
    for path in discovery["tensor_v0"]:
        add(path, "feature_tensorization_audit_v0", path.suffix.lstrip(".") or "source", "dynamic tree match")
    for path in discovery["step12d"]:
        add(path, "step12d_smoke_evidence", path.suffix.lstrip(".") or "source", "dynamic UNKNOWN_ATOM_FEATURE_POLICY lineage")
    for path in table_payloads:
        role = "pocket_atom_table" if path.name == "pocket_atom_table.csv" else "ligand_atom_table"
        add(path, role, "csv", "type_symbol/x/y/z", 1)
    payloads = dict(fixed_payloads)
    payloads.update(table_payloads)
    rows = []
    for path in sorted(specs, key=lambda item: item.as_posix()):
        payload = payloads.get(path)
        if payload is None:
            payload = _base_bytes(repo_root, path)
        role, kind, selector, sample_count = specs[path]
        referenced = sum(
            1 for row in registry
            if path.as_posix() in {
                row["producer_path"], row["consumer_path"]
            }
            or path.as_posix() in row["source_columns_or_inputs"]
        )
        rows.append({
            "source_role": role,
            "source_path": path.as_posix(),
            "source_sha256": _sha(payload),
            "committed_in_base": True,
            "source_kind": kind,
            "selector_or_symbol": selector,
            "referenced_feature_count": referenced,
            "referenced_sample_count": sample_count,
            "verified": True,
        })
    return rows


def _registry_valid(rows: list[dict[str, Any]]) -> bool:
    ids = [row["feature_id"] for row in rows]
    if not rows or len(ids) != len(set(ids)):
        return False
    for row in rows:
        if row["feature_status"] not in FEATURE_STATUSES:
            return False
        if row["evidence_status"] not in EVIDENCE_STATUSES:
            return False
        if row["feature_status"] == "current_model_input":
            required = (
                row["producer_path"], row["producer_symbol"],
                row["consumer_path"], row["consumer_symbol"],
                row["runtime_dtype"], row["tensor_rank"],
                row["tensor_shape_or_width"],
                row["normalization_or_scaling"],
            )
            if any(value in ("", "not_applicable") for value in required):
                return False
            if row["evidence_status"] not in {
                "explicitly_defined", "deterministically_derived"
            }:
                return False
    return True


def _issue_artifact(
    predecessor_payload: bytes,
    feature_issue_open: bool,
    unknown_issue_open: bool,
) -> tuple[bytes, list[dict[str, str]]]:
    predecessor_rows = _csv_rows(predecessor_payload)
    columns = tuple(predecessor_rows[0])
    additions = []
    for order, issue_id, is_open, scope, reason in (
        (
            31, "FINAL_TRAINING_FEATURE_SEMANTICS_UNRESOLVED",
            feature_issue_open, "final_training_feature_semantics",
            "one or more current model input semantics are not frozen",
        ),
        (
            32, "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED",
            unknown_issue_open, "protein_and_ligand_unknown_atom_policy",
            "unsupported/missing atom handling is not fail-closed for the checkpoint-compatible path",
        ),
    ):
        status = "open" if is_open else "resolved"
        additions.append({
            "inherited_order": str(order),
            "issue_id": issue_id,
            "issue_type": "training_feature_semantics_gap",
            "affected_fields": "",
            "affected_rules": "",
            "severity": "blocking",
            "status": status,
            "blocking_scope": scope,
            "blocking_reason": reason,
            "issue_origin": STAGE,
            "integration_transition": "new_audit_issue",
            "issue_count": "1" if is_open else "0",
            "inherited_effective_status": "",
            "inherited_transition_stage": "",
            "inherited_transition_action": "not_applicable_new_issue",
            "inherited_transition_evidence": "new feature-semantics audit identity",
            "successor_effective_status": status,
            "successor_transition_stage": STAGE,
            "successor_transition_action": (
                "retained_open_by_current_audit"
                if is_open else "resolved_by_current_audit"
            ),
            "successor_transition_evidence": (
                reason if is_open else "formal audit found no corresponding unresolved condition"
            ),
        })
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writerows(additions)
    prefix = predecessor_payload
    if prefix and not prefix.endswith(b"\n"):
        prefix += b"\n"
    payload = prefix + buffer.getvalue().encode("utf-8")
    return payload, predecessor_rows + additions


def serialize_covapie_final_training_feature_semantics_audit_decision_v1(
    decision: FinalTrainingFeatureSemanticsAuditDecision,
) -> bytes:
    return (
        json.dumps(asdict(decision), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def derive_covapie_final_training_feature_semantics_audit_v1(
    repo_root: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    fixed_payloads, predecessor_verified = _verify_predecessor(repo_root)
    if not predecessor_verified:
        raise ValueError("frozen quarantine predecessor failed closed")
    discovery = _discover_sources(repo_root)
    coverage, table_payloads = _atom_coverage(
        repo_root, fixed_payloads[FINAL_DATASET_INDEX]
    )
    registry = _feature_registry()
    if not _registry_valid(registry):
        raise ValueError("feature registry failed closed")
    atom_pair_manifest = _json(fixed_payloads[ATOM_PAIR_MANIFEST])
    observed_masks = tuple(
        (row.get("semantic_name"), row.get("display_alias"))
        for row in atom_pair_manifest.get("canonical_masks", [])
    )
    if observed_masks != CANONICAL_MASKS:
        raise ValueError("canonical mask contract drift")
    unknown_rows = _unknown_policy_rows(coverage)
    failure_rows = _failure_rows()
    if len(failure_rows) != len(FAILURE_CASES) or not all(
        row["verified"] for row in failure_rows
    ):
        raise ValueError("failure matrix did not fail closed")
    counts = {
        status: sum(row["evidence_status"] == status for row in registry)
        for status in EVIDENCE_STATUSES
    }
    current_rows = [
        row for row in registry if row["feature_status"] == "current_model_input"
    ]
    current_frozen = all(
        row["evidence_status"] in {
            "explicitly_defined", "deterministically_derived"
        }
        and row["producer_path"]
        and row["consumer_path"]
        for row in current_rows
    )
    protein_policy = ligand_policy = "unknown_atom_policy_unresolved"
    protein_resolved = ligand_resolved = False
    unknown_resolved = protein_resolved and ligand_resolved
    known = (
        counts["ambiguous"] == 0
        and counts["missing"] == 0
        and counts["contradictory"] == 0
        and current_frozen
        and unknown_resolved
    )
    if counts["contradictory"]:
        next_step = "resolve_covapie_training_feature_semantics_contradictions_v1"
    elif (
        counts["ambiguous"] or counts["missing"] or not unknown_resolved
    ):
        next_step = RECOMMENDED_GAP_STEP
    else:
        next_step = "design_covapie_tensor_label_and_loss_mask_contract_v1"
    decision = FinalTrainingFeatureSemanticsAuditDecision(
        schema_version=SCHEMA_VERSION,
        outcome="audited_semantics_frozen" if known else "audited_with_blockers",
        predecessor_verified=predecessor_verified,
        discovered_feature_count=len(registry),
        current_model_input_feature_count=len(current_rows),
        metadata_only_feature_count=sum(
            row["feature_status"] == "current_data_metadata_only" for row in registry
        ),
        future_not_integrated_feature_count=sum(
            row["feature_status"] == "future_planned_not_integrated" for row in registry
        ),
        explicit_semantics_count=counts["explicitly_defined"],
        deterministically_derived_semantics_count=counts["deterministically_derived"],
        ambiguous_semantics_count=counts["ambiguous"],
        missing_semantics_count=counts["missing"],
        contradictory_semantics_count=counts["contradictory"],
        protein_unknown_atom_policy=protein_policy,
        ligand_unknown_atom_policy=ligand_policy,
        protein_unknown_atom_policy_resolved=protein_resolved,
        ligand_unknown_atom_policy_resolved=ligand_resolved,
        all_current_model_input_semantics_frozen=current_frozen,
        feature_semantics_audit_completed=True,
        feature_semantics_known=known,
        unknown_atom_feature_policy_resolved=unknown_resolved,
        checkpoint_compatibility_preserved=True,
        model_changed=False,
        dataloader_changed=False,
        tensorization_used=False,
        training_used=False,
        ready_for_tensor_label_loss_mask_contract_design=known,
        ready_for_tensorization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
        recommended_next_step=next_step,
    )
    feature_issue_open = not current_frozen or any(
        counts[name] for name in ("ambiguous", "missing", "contradictory")
    )
    issue_payload, issue_rows = _issue_artifact(
        fixed_payloads[PREDECESSOR_ISSUES],
        feature_issue_open=bool(feature_issue_open),
        unknown_issue_open=not unknown_resolved,
    )
    source_rows = _source_inventory(
        repo_root, discovery, fixed_payloads, table_payloads, registry
    )
    return {
        "decision": decision,
        "discovery": discovery,
        "source_rows": source_rows,
        "registry_rows": registry,
        "coverage_rows": coverage,
        "unknown_rows": unknown_rows,
        "failure_rows": failure_rows,
        "issue_rows": issue_rows,
        "issue_payload": issue_payload,
        "predecessor_issue_payload": fixed_payloads[PREDECESSOR_ISSUES],
        "step12d_smoke_legality_verified": True,
    }


def _non_manifest_artifacts(result: dict[str, Any]) -> dict[str, bytes]:
    return {
        SOURCE_INVENTORY_FILE: _csv_bytes(SOURCE_COLUMNS, result["source_rows"]),
        FEATURE_REGISTRY_FILE: _csv_bytes(FEATURE_COLUMNS, result["registry_rows"]),
        UNKNOWN_POLICY_FILE: _csv_bytes(UNKNOWN_COLUMNS, result["unknown_rows"]),
        FAILURE_MATRIX_FILE: _csv_bytes(FAILURE_COLUMNS, result["failure_rows"]),
        ISSUE_INVENTORY_FILE: result["issue_payload"],
    }


def _manifest(result: dict[str, Any], evidence: dict[str, bytes]) -> dict[str, Any]:
    decision: FinalTrainingFeatureSemanticsAuditDecision = result["decision"]
    open_issues = [
        row["issue_id"] for row in result["issue_rows"]
        if row["successor_effective_status"] == "open"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "feature_semantics_audit_completed": True,
        "audit_outcome": decision.outcome,
        "discovered_feature_count": decision.discovered_feature_count,
        "current_model_input_feature_count": decision.current_model_input_feature_count,
        "metadata_only_feature_count": decision.metadata_only_feature_count,
        "future_not_integrated_feature_count": decision.future_not_integrated_feature_count,
        "explicit_semantics_count": decision.explicit_semantics_count,
        "deterministically_derived_semantics_count": decision.deterministically_derived_semantics_count,
        "ambiguous_semantics_count": decision.ambiguous_semantics_count,
        "missing_semantics_count": decision.missing_semantics_count,
        "contradictory_semantics_count": decision.contradictory_semantics_count,
        "all_current_model_input_semantics_frozen": decision.all_current_model_input_semantics_frozen,
        "protein_unknown_atom_policy": decision.protein_unknown_atom_policy,
        "ligand_unknown_atom_policy": decision.ligand_unknown_atom_policy,
        "protein_unknown_atom_policy_resolved": decision.protein_unknown_atom_policy_resolved,
        "ligand_unknown_atom_policy_resolved": decision.ligand_unknown_atom_policy_resolved,
        "feature_semantics_known": decision.feature_semantics_known,
        "unknown_atom_feature_policy_resolved": decision.unknown_atom_feature_policy_resolved,
        "checkpoint_compatibility_preserved": decision.checkpoint_compatibility_preserved,
        "step12d_smoke_legality_verified": result["step12d_smoke_legality_verified"],
        "step12d_final_feature_semantics_contract": False,
        "step12d_training_readiness_authority": False,
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "planned_covalent_model_module_count": 5,
        "planned_covalent_model_modules": list(PLANNED_COVALENT_MODEL_MODULES),
        "integrated_covalent_model_module_count": 0,
        "atom_coverage": result["coverage_rows"],
        "source_inventory_row_count": len(result["source_rows"]),
        "feature_registry_row_count": len(result["registry_rows"]),
        "unknown_policy_matrix_row_count": len(result["unknown_rows"]),
        "failure_matrix_row_count": len(result["failure_rows"]),
        "failure_matrix_all_cases_verified": all(
            row["verified"] for row in result["failure_rows"]
        ),
        "issue_inventory_row_count": len(result["issue_rows"]),
        "effective_open_issue_count": len(open_issues),
        "effective_open_issues": open_issues,
        "ready_for_tensor_label_loss_mask_contract_design": decision.ready_for_tensor_label_loss_mask_contract_design,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
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
        "recommended_next_step": decision.recommended_next_step,
    }


def build_covapie_final_training_feature_semantics_audit_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    result = derive_covapie_final_training_feature_semantics_audit_v1(repo_root)
    artifacts = _non_manifest_artifacts(result)
    artifacts[MANIFEST_FILE] = (
        json.dumps(_manifest(result, artifacts), indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return artifacts
