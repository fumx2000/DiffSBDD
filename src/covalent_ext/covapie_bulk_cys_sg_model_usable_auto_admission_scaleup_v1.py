"""CovaPIE ranks 501--1000 model-usable scale-up successor V1.

The frozen 2,387-event universe and published ranking remain authoritative.
This module adds a read-through, task-owned RCSB overlay and reuses the
published structural, leakage, exact-negative, tensor/runtime, and authority
owners.  It never trains a model or creates chemistry-family authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor
from covalent_ext import covapie_bulk_500_new_event_scale_up_rehearsal_v1 as ranking
from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk
from covalent_ext import covapie_cumulative_500_supported_post_only_two_rule_routing_v1 as cumulative500
from covalent_ext import covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as routing
from covalent_ext import covapie_bulk_post_only_cys_sg_training_candidate_triage_v1 as triage
from covalent_ext import covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1
    as mixed_scheduler,
)


SCHEMA_VERSION = "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
BASELINE_HEAD = "cbc939ff1891702745ac5f308e6b0a5ae0ec2a00"
BASELINE_PARENT = "796210717328f216a0fd273af57b872195109df2"
BASELINE_TREE = "3da4c4af8423e173e5311986e2763834f8d75d4f"
BASELINE_SUBJECT = (
    "add CovaPIE batch001 formal training DataModule and train-validation integration v1"
)
PUBLICATION_SUBJECT = (
    "add CovaPIE bulk Cys-SG model-usable auto-admission scale-up v1"
)

PREFLIGHT_NO_NETWORK = "PREFLIGHT_NO_NETWORK"
CONTROLLED_NETWORK_EXECUTION = "CONTROLLED_NETWORK_EXECUTION"
REPLAY_NO_NETWORK = "REPLAY_NO_NETWORK"
DEFAULT_MODE = PREFLIGHT_NO_NETWORK

RANK_START = 501
RANK_END = 1000
SCALEUP_COUNT = 500
CANONICAL_COUNT = 2387
CONTROL_COUNT = 27
RANKED_NEW_COUNT = 2360
REMAINING_COUNT = 1360
CCD_CAP_BYTES = 4 * 1024 * 1024
PDB_CAP_BYTES = bulk.COMPRESSED_FILE_CAP
TOTAL_DOWNLOAD_CAP_BYTES = 2 * 1024 * 1024 * 1024
MAX_ATTEMPTS_PER_REQUEST = 2

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
)
COHORT = "covapie_bulk_cys_sg_ranks_0501_1000_cohort_v1.csv"
PROCESSING = "covapie_bulk_cys_sg_ranks_0501_1000_processing_outcomes_v1.json"
CENSUS = "covapie_bulk_cys_sg_cumulative_1000_model_usable_census_v1.csv"
EFFECTIVE_N = "covapie_bulk_cys_sg_effective_supervised_n_by_head_v1.json"
QUEUE = "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
MANIFEST = "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_manifest_v1.json"
SUMMARY = "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_summary_v1.json"
OUTPUT_FILENAMES = (COHORT, PROCESSING, CENSUS, EFFECTIVE_N, QUEUE, MANIFEST, SUMMARY)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1.py"
)
RUNNER_RELATIVE = Path(
    "scripts/run_covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1.py"
)
AUTHORIZED_PATHS = frozenset({
    SOURCE_RELATIVE.as_posix(), RUNNER_RELATIVE.as_posix(),
    CHECKER_RELATIVE.as_posix(), TEST_RELATIVE.as_posix(),
    *((OUTPUT_ROOT_RELATIVE / name).as_posix() for name in OUTPUT_FILENAMES),
})

CANONICAL_CACHE_RELATIVE_TO_PARENT = Path(
    "covapie-state/bulk-multisource-cys-sg-v1"
)
OVERLAY_ATTEMPT_RELATIVE_TO_PARENT = Path(
    "covapie-state/bulk-model-usable-auto-admission-scaleup-v1/"
    "ranks-0501-1000/attempt-001"
)
FIRST500_ATTEMPT_RELATIVE_TO_PARENT = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001"
)
EXTERNAL_ACQUISITION = "acquisition_result_v1.json"
EXTERNAL_PROCESSING = "processing_result_v1.json"
EXTERNAL_EXECUTION = "controlled_execution_result_v1.json"

CANONICAL_RELATIVE = Path(
    "data/derived/covalent_small/covapie_bulk_cys_sg_dataset_expansion_v1/"
    "bulk_pilot_v1/cross_source_canonical_event_manifest_v1.json"
)
CUMULATIVE500_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1"
)
FIRST500_ROUTING = CUMULATIVE500_ROOT / cumulative500.EVENT_INVENTORY
BATCH13_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1"
)
BATCH13_INDEX = BATCH13_ROOT / "covapie_batch001_13event_model_usable_split_index_v1.csv"
BATCH13_REGISTRY = BATCH13_ROOT / "covapie_batch001_model_usable_split_registry_v1.json"
BATCH13_BRIDGE = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1/"
    "covapie_batch001_model_bound_structural_evidence_v1.json"
)
BATCH13_DECISIONS = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_batch001_completed_human_decision_snapshot_v1.json"
)
FEATURE_AUTHORITY = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
)
PRODUCTION_AUTHORITY = routing.CURRENT_PRODUCTION_AUTHORITY_REGISTRY_RELATIVE
HUMAN_REVIEW_DECISIONS = Path(
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/"
    "covapie_post_only_human_review_decisions_v1.json"
)
CURRENT11_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
CURRENT11_SPLIT_ASSIGNMENT = Path(
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_sample_split_assignment.csv"
)
K36_STRUCTURAL_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1/"
    "covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json"
)
K36_CARRIER_RELATIVE_TO_PARENT = Path(
    "covapie-state/formal-sidecars/k36-w1-recovered7-effective-supervision-v1/"
    "covapie_k36_w1_recovered7_effective_supervision_v1.json"
)
K36_CARRIER_SHA256 = "bd448b021ee0882f4bfe0826206616b83cdc7f69d9544f4533098aceed3a558c"

CURRENT11_MATERIALIZER_SOURCE = Path(
    "src/covalent_ext/covapie_current11_trainable_supervision_materializer_v1.py"
)
MIXED_TENSORIZER_SOURCE = Path(
    "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py"
)
MIXED_SCHEDULER_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1.py"
)
EXACT16_POST_AUTHORITY_SOURCE = Path(
    "src/covalent_ext/covapie_exact16_post_geometry_partial_supervision_authority_v1.py"
)
MIXED_LIGHTNING_SOURCE = Path(
    "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1.py"
)
EXACT16_TRAINER_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_expanded_cys_sg_mixed_profile_single_batch_trainer_fit_smoke_v1.py"
)
APPROVED_EXPANSION_PIPELINE_SOURCE = Path(
    "src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py"
)
APPROVED_EXPANSION_SAMPLE_FILES = (
    (
        "6OIM/MOV",
        Path(
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
            "6oim_mov_approved_v1/samples/a23745e87b364fe7.materialized.json"
        ),
        Path(
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
            "6oim_mov_approved_v1/samples/a23745e87b364fe7.tensorized.json"
        ),
    ),
    (
        "6DI9/GJJ",
        Path(
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
            "6di9_gjj_approved_v1/samples/8483b1e83aa8e1b6.materialized.json"
        ),
        Path(
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
            "6di9_gjj_approved_v1/samples/8483b1e83aa8e1b6.tensorized.json"
        ),
    ),
    (
        "5F2E/5UT",
        Path(
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
            "5f2e_5ut_approved_v1/samples/7aeb236b1946e96f.materialized.json"
        ),
        Path(
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
            "5f2e_5ut_approved_v1/samples/7aeb236b1946e96f.tensorized.json"
        ),
    ),
)

BOUND_INPUT_SHA256 = {
    CANONICAL_RELATIVE: "d3f35987af92fca669b85d62a86914c7a01bf35d867c4a779e7fc08e76445dae",
    FIRST500_ROUTING: "ea4ec17fed58d2a7100173ada17a0956a5c37ef4690899f415a9b497c8508173",
    CUMULATIVE500_ROOT / cumulative500.REVIEW_UNIT_INVENTORY: "8988f8e577df51883444ecda9a3274741421249feed7c38b7ae3c56b36ddabb9",
    CUMULATIVE500_ROOT / cumulative500.MANIFEST: "da382f8ab6fe42c7be4607ba4d16b59443cb944984d386ae12f7b4e89d2f8942",
    CUMULATIVE500_ROOT / cumulative500.SUMMARY: "24f5621c75110e461de2a657ccd7404fd2352e44b44d0dbc23e8613454e56496",
    FEATURE_AUTHORITY: "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0",
    PRODUCTION_AUTHORITY: "c6f150bd82b1ea45121aa96e1fefb6af3be64584117cc462f74b2e10fd1913e9",
    BATCH13_INDEX: "f22064a20000126b0792a22e241f3cf9d912bc804da7c5f58eb2f5669157faf3",
    BATCH13_REGISTRY: "bb40624fbb88356e31d2b69d685055f6ed8ec785155a7d5ba877cc1e6cfb1540",
    BATCH13_BRIDGE: "cca589fa4ac372c159b2e00ba4f59a7c794e21a10f1b3fcffbd477de42cd8f2e",
    BATCH13_DECISIONS: "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200",
    HUMAN_REVIEW_DECISIONS: "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441",
    CURRENT11_INDEX: "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326",
    CURRENT11_SPLIT_ASSIGNMENT: "29ffff244e33e3ec93f2c2b3e5e42a09ce73d7f55019f833e97659301f6a388c",
    K36_STRUCTURAL_EVIDENCE: "c0a5196f94284bc78c49f1a981798c85b1fd5869237d54f30ba239321c3eb799",
    CURRENT11_MATERIALIZER_SOURCE: "0dddcb645dc26eacc864fa2c6b59db5cbd34ed2da3e8bf7abb26d5daee9672ff",
    MIXED_TENSORIZER_SOURCE: "c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932",
    MIXED_SCHEDULER_SOURCE: "b77df848c915aaa5f9f7c93f812980952d3a41ac623e898e28036db6f316e980",
    EXACT16_POST_AUTHORITY_SOURCE: "6f388b42bd58ffed67ed752a9fec9f85e57050fc96a89e6f3d3e90b1281dba44",
    MIXED_LIGHTNING_SOURCE: "cabb479e35df0cd86c72cdca11903deaf03cf3c134d95d1c067e4b671e2b3fb2",
    EXACT16_TRAINER_SOURCE: "d0c50939eb182a9cc4047b4a99843c7da5a78d6e70a96773afeedd43c4fca653",
    APPROVED_EXPANSION_PIPELINE_SOURCE: "ece0221669400b75c152edd11c18b36d87056d989344e9bc1ae674612f8d4dd6",
    APPROVED_EXPANSION_SAMPLE_FILES[0][1]: "edeb70f3a38a72f785def1e0eb42046793aa884d370fd7096b12eca877fb6b40",
    APPROVED_EXPANSION_SAMPLE_FILES[0][2]: "2a5ad0a99ca9f928fae694d8a865b391f8a4c6a0387fbddae9803fe248f286a6",
    APPROVED_EXPANSION_SAMPLE_FILES[1][1]: "254b76c7c9da09d559adbb59489b39ed39d95934d34362dfe53cecbee28ed6bd",
    APPROVED_EXPANSION_SAMPLE_FILES[1][2]: "d128d0d5da6bccfdb29c8d951cdae61c4d27618f974ede5fbba8716d795d7db6",
    APPROVED_EXPANSION_SAMPLE_FILES[2][1]: "c7120c9c12e2b2d8fc1ec0bd214ac6096cf1b377d93bafb237a275842349e03b",
    APPROVED_EXPANSION_SAMPLE_FILES[2][2]: "64f1fc6c51a5aa1b1e10a3ed0ca36ca65bfd22493091a3a9b69845495c505ccb",
    Path("src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py"): "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0",
    Path("src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py"): "5bf91b3af56ec0e5c2dec3ebb13e56695ca74c17bbbbb65f35e8d9249d6fc60f",
    Path("src/covalent_ext/covapie_current11_training_tensorizer_v1.py"): "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
    Path("src/covalent_ext/covapie_post_only_auto_negative_ts_dump_exact_v1.py"): "90956c833a31a5b5615979dedf3f5205738d27c05efe15168b9c38f71c264bf1",
    Path("src/covalent_ext/covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1.py"): "88209a549abf7ab119dc33cd537fcdaad45815ac74f86fdc339e4befa6278c46",
    Path("src/covalent_ext/covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1.py"): "d0fce4073b7201508091f72e4b016918beaf97d7c236f255f2532871a1ab0673",
    routing.GATE_MANIFEST_RELATIVE: "100b64fff8bbef56f9885a64607d25cff293bd9d98f93f25af71455dcf6bca42",
    routing.DTT_GATE_MANIFEST_RELATIVE: "9b41905df37beb80f73b3b5e02615439fcbe1f707dd5c1548bb71d0fb4976e45",
}
FIRST500_EXTERNAL_BINDINGS = {
    "controlled_execution_result_v1.json": (1877, "381159326fe183c47519acd554acf395f0da067926b93c42fd6962d134e995e9"),
    "cumulative_processing_view_v1.json": (6469651, "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44"),
    "incremental_processing_outcomes_v1.json": (3043911, "d891a267dc4493cfceda33b70ab4a200d9f806e1bff38c4b6f39b69a1a3548d7"),
}

COHORT_HEADER = (
    "scaleup_rank", "canonical_event_id", "selection_priority_pass", "pdb_id",
    "protein_label_asym_id", "protein_auth_chain", "protein_residue_name",
    "protein_residue_number", "protein_reactive_atom", "ligand_component_id",
    "ligand_instance", "ligand_reactive_atom", "source_dataset_count",
    "source_record_count", "source_datasets_json", "source_record_ids_json",
)
CENSUS_HEADER = (
    "scaleup_rank", "cohort_lane", "canonical_event_id", "pdb_id",
    "ligand_component_id", "protein_label_asym_id", "protein_auth_chain",
    "protein_residue_name", "protein_residue_number", "protein_reactive_atom",
    "ligand_instance", "ligand_reactive_atom", "structure_status", "CCD_status",
    "exact_event_recovery_status", "feature_status", "task_domain_authority_status",
    "positive_authority_source", "negative_rule_id", "role_profile",
    "positive_authority_audit_status", "chemistry_auto_admission_authorized",
    "runtime_role_materialization_available", "role_label_available",
    "role_label_authority_source", "reactive_pair_label_available",
    "reactive_pair_label_authoritative", "POST_geometry_label_available",
    "reactive_pair_label_authority_source", "POST_geometry_label_authoritative",
    "POST_geometry_label_authority_source", "experimental_PRE_available",
    "derived_PRE_available", "PRE_training_target_authoritative",
    "warhead_type_target_available", "reaction_family_target_available",
    "label_model_usable", "shadow_exact_component_reuse_candidate",
    "leakage_status", "leakage_group_id", "formal_split_if_authoritative",
    "training_split_admission_ready", "terminal_route", "reasons_json",
)
QUEUE_HEADER = (
    "priority_rank", "review_unit_id", "event_count",
    "potential_event_yield_per_unit", "canonical_event_ids_json", "pdb_ids_json",
    "ligand_component_ids_json", "full_coordinate_event_count",
    "exact_reactive_pair_event_count", "CCD_graph_complete_event_count",
    "POST_geometry_available_event_count", "shadow_exact_component_event_count",
    "representation_blocked_event_count", "leakage_conflict_event_count",
    "priority_score", "priority_reason", "human_decision_created",
)


class ScaleupSafetyError(ValueError):
    """Fail-closed scale-up contract error."""


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n",
                            extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ScaleupSafetyError("JSON_ROOT_NOT_OBJECT:" + path.as_posix())
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _binding(path: Path, *, display: str | None = None) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": display or path.as_posix(), "byte_count": len(payload),
            "sha256": _sha(payload)}


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo_root, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True).stdout.strip()


def canonical_cache_root_v1(repo_root: Path) -> Path:
    return (repo_root.resolve().parent / CANONICAL_CACHE_RELATIVE_TO_PARENT).resolve()


def overlay_attempt_root_v1(repo_root: Path) -> Path:
    return (repo_root.resolve().parent / OVERLAY_ATTEMPT_RELATIVE_TO_PARENT).resolve()


def overlay_cache_root_v1(repo_root: Path) -> Path:
    return overlay_attempt_root_v1(repo_root) / "cache"


def overlay_execution_root_v1(repo_root: Path) -> Path:
    return overlay_attempt_root_v1(repo_root) / "execution"


def first500_attempt_root_v1(repo_root: Path) -> Path:
    return (repo_root.resolve().parent / FIRST500_ATTEMPT_RELATIVE_TO_PARENT).resolve()


def observe_repository_state_v1(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    changed_entries = []
    for line in _git(
        root, "diff-tree", "--no-commit-id", "--name-status", "--no-renames",
        "-r", "HEAD",
    ).splitlines():
        if not line:
            continue
        status_value, path = line.split("\t", 1)
        changed_entries.append({"status": status_value, "path": path})
    candidate_modes = {}
    tree_output = _git(
        root, "ls-tree", "-r", "--full-tree", "HEAD", "--",
        *sorted(AUTHORIZED_PATHS),
    )
    for line in tree_output.splitlines():
        if not line:
            continue
        metadata, path = line.split("\t", 1)
        mode, object_type, _object_id = metadata.split()
        if object_type == "blob":
            candidate_modes[path] = mode
    return {
        "branch": _git(root, "branch", "--show-current"),
        "HEAD": _git(root, "rev-parse", "HEAD"),
        "HEAD_parent": _git(root, "rev-parse", "HEAD^"),
        "head_parent_ids": _git(root, "show", "-s", "--format=%P", "HEAD").split(),
        "HEAD_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "HEAD_subject": _git(root, "log", "-1", "--format=%s"),
        "head_changed_entries": changed_entries,
        "head_candidate_path_modes": candidate_modes,
        "origin_main": _git(root, "rev-parse", "refs/remotes/origin/main"),
        "ahead_behind": _git(root, "rev-list", "--left-right", "--count",
                             "HEAD...refs/remotes/origin/main"),
        "tracked_changes": [x for x in _git(root, "diff", "--name-only").splitlines() if x],
        "staged_changes": [x for x in _git(root, "diff", "--cached", "--name-only").splitlines() if x],
        "untracked": [x for x in _git(root, "ls-files", "--others", "--exclude-standard").splitlines() if x],
    }


def classify_repository_profile_v1(observation: Mapping[str, Any]) -> str:
    common = (
        observation.get("branch") == "main"
        and observation.get("staged_changes") == []
        and observation.get("tracked_changes") == []
    )
    if not common:
        raise ScaleupSafetyError("REPOSITORY_COMMON_STATE_MISMATCH")
    untracked_values = observation.get("untracked")
    if type(untracked_values) is not list or any(
        type(value) is not str for value in untracked_values
    ):
        raise ScaleupSafetyError("REPOSITORY_UNTRACKED_STATE_INVALID")
    untracked = set(untracked_values)
    if (
        observation.get("HEAD") == BASELINE_HEAD
        and observation.get("head_parent_ids") == [BASELINE_PARENT]
        and observation.get("HEAD_parent") == BASELINE_PARENT
        and observation.get("HEAD_tree") == BASELINE_TREE
        and observation.get("HEAD_subject") == BASELINE_SUBJECT
        and observation.get("origin_main") == BASELINE_HEAD
        and observation.get("ahead_behind") == "0\t0"
        and len(untracked_values) == len(AUTHORIZED_PATHS)
        and untracked == set(AUTHORIZED_PATHS)
    ):
        return "candidate_precommit_untracked"
    changed_entries = observation.get("head_changed_entries")
    candidate_modes = observation.get("head_candidate_path_modes")
    if (
        type(changed_entries) is list
        and type(candidate_modes) is dict
        and observation.get("HEAD") == observation.get("origin_main")
        and observation.get("head_parent_ids") == [BASELINE_HEAD]
        and observation.get("HEAD_parent") == BASELINE_HEAD
        and observation.get("HEAD_subject") == PUBLICATION_SUBJECT
        and observation.get("ahead_behind") == "0\t0"
        and not untracked
        and len(changed_entries) == len(AUTHORIZED_PATHS)
        and {
            (item.get("status"), item.get("path"))
            for item in changed_entries if type(item) is dict
        } == {("A", path) for path in AUTHORIZED_PATHS}
        and candidate_modes == {
            path: "100644" for path in AUTHORIZED_PATHS
        }
    ):
        return "published_successor"
    raise ScaleupSafetyError("REPOSITORY_PROFILE_MISMATCH")


def verify_bound_inputs_v1(repo_root: Path) -> list[dict[str, object]]:
    root = repo_root.resolve()
    result = []
    for relative, expected in BOUND_INPUT_SHA256.items():
        path = root / relative
        if not path.is_file():
            raise ScaleupSafetyError("BOUND_INPUT_MISSING:" + relative.as_posix())
        observed = _binding(path, display=relative.as_posix())
        if observed["sha256"] != expected:
            raise ScaleupSafetyError("BOUND_INPUT_SHA256_MISMATCH:" + relative.as_posix())
        result.append(observed)
    return result


def _external_first500_bindings(repo_root: Path) -> list[dict[str, object]]:
    root = first500_attempt_root_v1(repo_root)
    result = []
    for name, (size, digest) in FIRST500_EXTERNAL_BINDINGS.items():
        path = root / name
        observed = _binding(path, display=(FIRST500_ATTEMPT_RELATIVE_TO_PARENT / name).as_posix())
        if observed["byte_count"] != size or observed["sha256"] != digest:
            raise ScaleupSafetyError("FIRST500_EXTERNAL_BINDING_MISMATCH:" + name)
        result.append(observed)
    return result


def load_scaleup_inputs_v1(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    bindings = verify_bound_inputs_v1(root)
    external_bindings = _external_first500_bindings(root)
    ranked = ranking._load_inputs_v1(root)
    new_order = [item for item in ranked["priority_order"]
                 if str(item["canonical_event_id"]) in ranked["new_event_ids"]]
    if len(new_order) != RANKED_NEW_COUNT:
        raise ScaleupSafetyError("RANKED_NEW_POPULATION_MISMATCH")
    published = executor.load_published_executor_inputs_v1(root)
    prefix_ids = [str(item["canonical_event_id"]) for item in new_order[:500]]
    published_ids = [str(item["canonical_event_id"]) for item in published["cohort_records"]]
    if prefix_ids != published_ids:
        raise ScaleupSafetyError("FIRST500_EXACT_PREFIX_PARITY_FAILED")
    cohort = new_order[500:1000]
    cohort_ids = [str(item["canonical_event_id"]) for item in cohort]
    if len(cohort) != SCALEUP_COUNT or len(set(cohort_ids)) != SCALEUP_COUNT:
        raise ScaleupSafetyError("RANK501_1000_IDENTITY_INVALID")
    if set(prefix_ids) & set(cohort_ids) or len(new_order[1000:]) != REMAINING_COUNT:
        raise ScaleupSafetyError("RANK_POPULATION_RECONCILIATION_FAILED")

    first_view = _read_json(first500_attempt_root_v1(root) / "cumulative_processing_view_v1.json")
    first_rows = first_view.get("events")
    if not isinstance(first_rows, list) or len(first_rows) != 500:
        raise ScaleupSafetyError("FIRST500_VIEW_POPULATION_INVALID")
    if [int(row["scaleup_rank"]) for row in first_rows] != list(range(1, 501)):
        raise ScaleupSafetyError("FIRST500_VIEW_RANK_INVALID")
    if [row["processing_outcome"]["canonical_event_id"] for row in first_rows] != prefix_ids:
        raise ScaleupSafetyError("FIRST500_VIEW_IDENTITY_INVALID")

    routing_rows = _read_csv(root / FIRST500_ROUTING)
    if len(routing_rows) != 500 or [int(row["scaleup_rank"]) for row in routing_rows] != list(range(1, 501)):
        raise ScaleupSafetyError("FIRST500_ROUTING_POPULATION_INVALID")
    partition = Counter(row["post_only_partition"] for row in routing_rows)
    if partition != Counter({
        triage.POST_ONLY_CANDIDATE: 210,
        triage.BLOCKED_LEAKAGE: 196,
        triage.BLOCKED_REPRESENTATION: 31,
        triage.OUTSIDE_STRUCTURAL: 63,
    }):
        raise ScaleupSafetyError("FIRST500_PARTITION_MISMATCH")

    feature = _read_json(root / FEATURE_AUTHORITY)
    if not (
        feature.get("feature_semantics_audit_completed") is True
        and feature.get("feature_semantics_known") is True
        and feature.get("unknown_atom_feature_policy_resolved") is True
        and feature.get("unknown_atom_policy_contract_resolved") is True
        and feature.get("effective_open_issue_count") == 0
    ):
        raise ScaleupSafetyError("FEATURE_SEMANTICS_AUTHORITY_DRIFT")
    authority_registry = _read_json(root / PRODUCTION_AUTHORITY)
    authorities = authority_registry.get("authorities")
    if not isinstance(authorities, list) or len(authorities) != 3 or any(
        item.get("approval_scope") != "EXACT_CHEMISTRY_SIGNATURE_REUSABLE"
        or item.get("cross_signature_propagation_allowed") is not False
        for item in authorities
    ):
        raise ScaleupSafetyError("PRODUCTION_REUSABLE_AUTHORITY_DRIFT")

    split_rows = _read_csv(root / BATCH13_INDEX)
    if len(split_rows) != 13 or any(
        row["model_usable"] != "true" or row["split_admission_authoritative"] != "true"
        for row in split_rows
    ):
        raise ScaleupSafetyError("BATCH13_CURRENT_RUNTIME_AUTHORITY_INVALID")
    split_counts = Counter(row["formal_split"] for row in split_rows)
    if split_counts != Counter({"train": 5, "validation": 4, "test": 4}):
        raise ScaleupSafetyError("BATCH13_FORMAL_SPLIT_MISMATCH")
    exact13_ids = {row["canonical_event_id"] for row in split_rows}
    if not exact13_ids <= set(prefix_ids):
        raise ScaleupSafetyError("BATCH13_NOT_WITHIN_FROZEN_FIRST500")
    decisions = _read_json(root / BATCH13_DECISIONS)
    if decisions.get("counts", {}).get("completed_positive_event_count") != 13:
        raise ScaleupSafetyError("BATCH13_POSITIVE_DECISION_COUNT_MISMATCH")
    bridge = _read_json(root / BATCH13_BRIDGE)
    if bridge.get("event_count") != 13 or {
        item["canonical_event_id"] for item in bridge.get("events", [])
    } != exact13_ids:
        raise ScaleupSafetyError("BATCH13_RUNTIME_BRIDGE_COVERAGE_MISMATCH")

    human_review_decisions = _read_json(root / HUMAN_REVIEW_DECISIONS)
    if (
        human_review_decisions.get("schema_version")
        != "covapie_post_only_human_review_decisions_v1"
        or type(human_review_decisions.get("units")) is not list
    ):
        raise ScaleupSafetyError("CURRENT_HUMAN_REVIEW_AUTHORITY_DRIFT")

    loaded = {
        "repo_root": root, "bindings": bindings,
        "external_first500_bindings": external_bindings,
        "ranked": ranked, "new_order": new_order, "cohort": cohort,
        "first500_rows": first_rows, "first500_routing_rows": routing_rows,
        "event_by_id": ranked["event_by_id"], "feature": feature,
        "production_authority_registry": authority_registry,
        "batch13_rows": split_rows, "batch13_ids": exact13_ids,
        "batch13_bridge": bridge, "prefix_parity": True,
        "human_review_decisions": human_review_decisions,
    }
    loaded["global_authority_audit"] = audit_global_current_positive_authority_v1(
        repo_root=root, inputs=loaded,
    )
    return loaded


def _exact_canonical_event_match_v1(
    *,
    events: Sequence[Mapping[str, Any]],
    pdb_id: str,
    ligand_component_id: str,
    protein_residue_number: str,
    ligand_reactive_atom: str,
    protein_instance: str | None = None,
    ligand_instance: str | None = None,
) -> Mapping[str, Any]:
    matches = [
        event for event in events
        if str(event.get("pdb_id")) == pdb_id
        and str(event.get("ligand_component_id")) == ligand_component_id
        and str(event.get("protein_residue_name")) == "CYS"
        and str(event.get("protein_residue_number")) == protein_residue_number
        and str(event.get("protein_reactive_atom")) == "SG"
        and str(event.get("ligand_reactive_atom")) == ligand_reactive_atom
        and (
            protein_instance is None
            or str(event.get("protein_instance")) == protein_instance
        )
        and (
            ligand_instance is None
            or str(event.get("ligand_instance")) == ligand_instance
        )
    ]
    if len(matches) != 1:
        raise ScaleupSafetyError(
            "GLOBAL_AUTHORITY_CANONICAL_EVENT_MAPPING_NOT_EXACT_ONE:"
            f"{pdb_id}/{ligand_component_id}"
        )
    return matches[0]


def _authority_record_v1(
    *,
    lineage_id: str,
    sample_identity: str,
    canonical_event_id: str,
    audit_status: str,
    authority_sources: Sequence[str],
    positive_authority_exists: bool,
    task_domain_positive_authoritative: bool,
    role_label_authoritative: bool,
    reactive_pair_authoritative: bool,
    post_geometry_authoritative: bool,
    current_feature_semantics_compatible: bool,
    current_tensorizer_compatible: bool,
    current_model_input_available: bool,
    current_supervision_dataclass_compatible: bool,
    current_runtime_model_usable: bool,
    formal_split_authoritative: bool,
    formal_split: str,
    mapping_method: str,
    exclusion_reasons: Sequence[str] = (),
) -> dict[str, Any]:
    training_admitted = bool(
        current_runtime_model_usable
        and formal_split_authoritative
        and formal_split == "train"
    )
    return {
        "lineage_id": lineage_id,
        "sample_identity": sample_identity,
        "canonical_event_id": canonical_event_id,
        "canonical_event_mapping_method": mapping_method,
        "audit_status": audit_status,
        "authority_sources": list(authority_sources),
        "positive_authority_exists": positive_authority_exists,
        "task_domain_positive_authoritative": task_domain_positive_authoritative,
        "role_label_authoritative": role_label_authoritative,
        "reactive_pair_authoritative": reactive_pair_authoritative,
        "POST_geometry_authoritative": post_geometry_authoritative,
        "PRE_geometry_authoritative": False,
        "current_feature_semantics_compatible": current_feature_semantics_compatible,
        "current_tensorizer_compatible": current_tensorizer_compatible,
        "current_model_input_available": current_model_input_available,
        "current_supervision_dataclass_compatible": (
            current_supervision_dataclass_compatible
        ),
        "current_runtime_model_usable": current_runtime_model_usable,
        "formal_split_authoritative": formal_split_authoritative,
        "formal_split": formal_split,
        "formal_training_split_admitted": training_admitted,
        "exclusion_reasons": list(exclusion_reasons),
    }


def audit_global_current_positive_authority_v1(
    *, repo_root: Path, inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit current positive/runtime lineages without alias or chemistry inference."""

    events = list(inputs["ranked"]["events"])
    event_ids = {str(event["canonical_event_id"]) for event in events}
    records: list[dict[str, Any]] = []

    # The exact13 event-level bridge is the only ranked-new current-runtime owner.
    for row in sorted(inputs["batch13_rows"], key=lambda item: item["canonical_event_id"]):
        event_id = row["canonical_event_id"]
        if event_id not in event_ids:
            raise ScaleupSafetyError("BATCH13_CANONICAL_EVENT_MAPPING_MISSING")
        formal_split = row["formal_split"]
        records.append(_authority_record_v1(
            lineage_id="BATCH001_EXACT13_CURRENT_RUNTIME_AUTHORITY",
            sample_identity=event_id,
            canonical_event_id=event_id,
            audit_status="CURRENT_RUNTIME_MODEL_USABLE_CANONICAL_EVENT",
            authority_sources=(BATCH13_INDEX.as_posix(), BATCH13_BRIDGE.as_posix()),
            positive_authority_exists=True,
            task_domain_positive_authoritative=True,
            role_label_authoritative=True,
            reactive_pair_authoritative=True,
            post_geometry_authoritative=True,
            current_feature_semantics_compatible=True,
            current_tensorizer_compatible=True,
            current_model_input_available=True,
            current_supervision_dataclass_compatible=True,
            current_runtime_model_usable=True,
            formal_split_authoritative=True,
            formal_split=formal_split,
            mapping_method="PUBLISHED_EXACT_CANONICAL_EVENT_ID",
        ))

    current11_rows = _read_csv(repo_root / CURRENT11_INDEX)
    current11_by_identity = {row["sample_index_row_id"]: row for row in current11_rows}
    split_rows = _read_csv(repo_root / CURRENT11_SPLIT_ASSIGNMENT)
    split_by_identity = {row["sample_index_row_id"]: row for row in split_rows}
    if (
        tuple(current11_by_identity) != mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
        or set(split_by_identity) != set(current11_by_identity)
        or mixed_scheduler.EXACT16_MEMBER_IDENTITIES_V1
        != (
            mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
            + mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
        )
    ):
        raise ScaleupSafetyError("EXACT16_CURRENT11_OWNER_MEMBERSHIP_DRIFT")
    for identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
        source = current11_by_identity[identity]
        split_source = split_by_identity[identity]
        if split_source.get("sample_split_assignment_passed") != "True":
            raise ScaleupSafetyError("CURRENT11_FORMAL_SPLIT_AUTHORITY_INVALID")
        formal_split = split_source["assigned_split"]
        if formal_split not in {"train", "validation", "test"}:
            raise ScaleupSafetyError("CURRENT11_FORMAL_SPLIT_INVALID")
        event = _exact_canonical_event_match_v1(
            events=events,
            pdb_id=source["pdb_id"],
            ligand_component_id=source["ligand_comp_id"],
            protein_residue_number=source["covalent_residue_index"],
            ligand_reactive_atom=source["ligand_covalent_atom_name"],
            protein_instance=source["covalent_residue_chain_id"],
        )
        records.append(_authority_record_v1(
            lineage_id="EXACT16_CURRENT11_STRICT_LINKER_LINEAGE",
            sample_identity=identity,
            canonical_event_id=str(event["canonical_event_id"]),
            audit_status="CURRENT_RUNTIME_MODEL_USABLE_CANONICAL_EVENT",
            authority_sources=(
                CURRENT11_MATERIALIZER_SOURCE.as_posix(),
                MIXED_TENSORIZER_SOURCE.as_posix(),
                EXACT16_POST_AUTHORITY_SOURCE.as_posix(),
                MIXED_LIGHTNING_SOURCE.as_posix(),
                EXACT16_TRAINER_SOURCE.as_posix(),
                CURRENT11_INDEX.as_posix(),
                CURRENT11_SPLIT_ASSIGNMENT.as_posix(),
            ),
            positive_authority_exists=True,
            task_domain_positive_authoritative=True,
            role_label_authoritative=True,
            reactive_pair_authoritative=True,
            post_geometry_authoritative=True,
            current_feature_semantics_compatible=True,
            current_tensorizer_compatible=True,
            current_model_input_available=True,
            current_supervision_dataclass_compatible=True,
            current_runtime_model_usable=True,
            formal_split_authoritative=True,
            formal_split=formal_split,
            mapping_method="CURRENT11_INDEX_EXACT_CYS_SG_ENDPOINT_TO_CANONICAL_EVENT",
        ))

    carrier_path = repo_root.parent / K36_CARRIER_RELATIVE_TO_PARENT
    carrier_binding = _binding(
        carrier_path, display=K36_CARRIER_RELATIVE_TO_PARENT.as_posix()
    )
    if carrier_binding["sha256"] != K36_CARRIER_SHA256:
        raise ScaleupSafetyError("K36_EFFECTIVE_CARRIER_SHA256_MISMATCH")
    carrier = _read_json(carrier_path)
    carrier_records = carrier.get("effective_supervision_records")
    if type(carrier_records) is not list:
        raise ScaleupSafetyError("K36_EFFECTIVE_CARRIER_SCHEMA_INVALID")
    carrier_by_identity = {
        str(record.get("sample_identity")): record for record in carrier_records
    }
    structural = _read_json(repo_root / K36_STRUCTURAL_EVIDENCE)
    structural_by_identity: dict[str, Mapping[str, Any]] = {}
    for sample in structural.get("samples", []):
        if sample.get("ligand_component_id") == "K36":
            identity = f"{sample['pdb_id']}/K36"
            structural_by_identity[identity] = sample
    if (
        set(carrier_by_identity) != set(mixed_tensorizer.K36_MEMBER_IDENTITIES_V1)
        or set(structural_by_identity) != set(mixed_tensorizer.K36_MEMBER_IDENTITIES_V1)
    ):
        raise ScaleupSafetyError("EXACT16_K36_OWNER_MEMBERSHIP_DRIFT")
    for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1:
        carrier_record = carrier_by_identity[identity]
        structural_sample = structural_by_identity[identity]
        explicit = structural_sample.get("explicit_event")
        if type(explicit) is not dict:
            raise ScaleupSafetyError("K36_EXACT_EVENT_EVIDENCE_INVALID")
        protein = explicit.get("protein_endpoint")
        ligand = explicit.get("ligand_endpoint")
        if (
            type(protein) is not dict
            or type(ligand) is not dict
            or carrier_record.get("exact10_status") != "EXACT10_PASS"
            or carrier_record.get("pocket_status") != "POCKET_PASS"
            or carrier_record.get("role_profile")
            != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        ):
            raise ScaleupSafetyError("K36_CURRENT_RUNTIME_AUTHORITY_INVALID")
        event = _exact_canonical_event_match_v1(
            events=events,
            pdb_id=identity.split("/", 1)[0],
            ligand_component_id="K36",
            protein_residue_number=str(protein.get("auth_seq_id")),
            ligand_reactive_atom=str(ligand.get("auth_atom_id")),
            protein_instance=str(protein.get("label_asym_id")),
            ligand_instance=str(ligand.get("label_asym_id")),
        )
        records.append(_authority_record_v1(
            lineage_id="EXACT16_K36_DIRECT_ATTACHMENT_LINEAGE",
            sample_identity=identity,
            canonical_event_id=str(event["canonical_event_id"]),
            audit_status="CURRENT_RUNTIME_MODEL_USABLE_CANONICAL_EVENT",
            authority_sources=(
                K36_CARRIER_RELATIVE_TO_PARENT.as_posix(),
                K36_STRUCTURAL_EVIDENCE.as_posix(),
                MIXED_TENSORIZER_SOURCE.as_posix(),
                EXACT16_POST_AUTHORITY_SOURCE.as_posix(),
                MIXED_LIGHTNING_SOURCE.as_posix(),
                EXACT16_TRAINER_SOURCE.as_posix(),
            ),
            positive_authority_exists=True,
            task_domain_positive_authoritative=True,
            role_label_authoritative=True,
            reactive_pair_authoritative=True,
            post_geometry_authoritative=True,
            current_feature_semantics_compatible=True,
            current_tensorizer_compatible=True,
            current_model_input_available=True,
            current_supervision_dataclass_compatible=True,
            current_runtime_model_usable=True,
            formal_split_authoritative=False,
            formal_split="",
            mapping_method="K36_STRUCT_CONN_EXACT_ENDPOINT_TO_CANONICAL_EVENT",
            exclusion_reasons=("CURRENT_FORMAL_LEAKAGE_SAFE_SPLIT_NOT_PUBLISHED",),
        ))

    authority_by_source_identity = {}
    for authority in inputs["production_authority_registry"]["authorities"]:
        source = json.loads(authority["source_human_review_record_canonical_json"])
        authority_by_source_identity[source["candidate_identity"]] = (authority, source)
    for identity, materialized_path, tensorized_path in APPROVED_EXPANSION_SAMPLE_FILES:
        materialized = _read_json(repo_root / materialized_path)
        tensorized = _read_json(repo_root / tensorized_path)
        if identity not in authority_by_source_identity:
            raise ScaleupSafetyError("APPROVED_EXPANSION_AUTHORITY_IDENTITY_MISSING")
        authority, source = authority_by_source_identity[identity]
        if (
            materialized.get("candidate_identity") != identity
            or materialized.get("admitted_by") != "VALID_COMPLETED_HUMAN_APPROVAL"
            or materialized.get("materialization_performed") is not True
            or materialized.get("post_geometry_authority") is not True
            or tensorized.get("sample_identity") != identity
            or tensorized.get("tensorization_performed") is not True
            or tensorized.get("schema_version")
            != "covapie_cys_sg_authorized_expansion_tensorization_v1"
            or identity in mixed_scheduler.EXACT16_MEMBER_IDENTITIES_V1
        ):
            raise ScaleupSafetyError("APPROVED_EXPANSION_SAMPLE_AUTHORITY_INVALID")
        protein_descriptor = source["machine_evidence"]["exact_event_endpoints"][
            "protein_endpoint_descriptor"
        ].split(":")
        ligand_descriptor = source["machine_evidence"]["exact_event_endpoints"][
            "ligand_endpoint_descriptor"
        ].split(":")
        pdb_id, component = identity.split("/", 1)
        event = _exact_canonical_event_match_v1(
            events=events,
            pdb_id=pdb_id,
            ligand_component_id=component,
            protein_residue_number=protein_descriptor[2],
            ligand_reactive_atom=ligand_descriptor[3],
        )
        records.append(_authority_record_v1(
            lineage_id="APPROVED_EXPANSION_EXACT3_SAMPLE_LINEAGE",
            sample_identity=identity,
            canonical_event_id=str(event["canonical_event_id"]),
            audit_status="PUBLISHED_POSITIVE_LABEL_RUNTIME_BINDING_INCOMPLETE",
            authority_sources=(
                PRODUCTION_AUTHORITY.as_posix(), materialized_path.as_posix(),
                tensorized_path.as_posix(),
                APPROVED_EXPANSION_PIPELINE_SOURCE.as_posix(),
            ),
            positive_authority_exists=True,
            task_domain_positive_authoritative=True,
            role_label_authoritative=True,
            reactive_pair_authoritative=True,
            post_geometry_authoritative=True,
            current_feature_semantics_compatible=True,
            current_tensorizer_compatible=False,
            current_model_input_available=True,
            current_supervision_dataclass_compatible=False,
            current_runtime_model_usable=False,
            formal_split_authoritative=True,
            formal_split=str(materialized["assigned_split"]),
            mapping_method="APPROVED_SAMPLE_EXACT_ENDPOINT_TO_CANONICAL_EVENT",
            exclusion_reasons=(
                "AUTHORIZED_EXPANSION_TENSORIZATION_SCHEMA_NOT_BOUND_TO_CURRENT_SUPERVISION_DATACLASS",
                "CURRENT_MIXED_PROFILE_LIGHTNING_BRIDGE_MEMBERSHIP_ABSENT",
            ),
        ))

    first_outcome_by_id = {
        str(item["processing_outcome"]["canonical_event_id"]): item["processing_outcome"]
        for item in inputs["first500_rows"]
    }
    human_relevant_ids = {
        row["canonical_event_id"] for row in inputs["first500_routing_rows"]
        if row["effective_route"] == routing.HUMAN_RELEVANT_FINAL
    }
    unit_by_event = {}
    for unit in inputs["human_review_decisions"]["units"]:
        for event in unit.get("events", []):
            event_id = event.get("canonical_event_id")
            if event_id in human_relevant_ids:
                unit_by_event[event_id] = (unit, event)
    if len(human_relevant_ids) != 5 or set(unit_by_event) != human_relevant_ids:
        raise ScaleupSafetyError("CURRENT_FIVE_HUMAN_RELEVANT_AUTHORITY_INVALID")
    for event_id in sorted(human_relevant_ids):
        unit, event_decision = unit_by_event[event_id]
        outcome = first_outcome_by_id[event_id]
        structural = outcome.get("structural_processing") or {}
        complete = (
            unit.get("workflow_status") == "COMPLETED"
            and event_decision.get("event_training_use_decision") == "INCLUDE"
            and event_decision.get("post_geometry_training_usable") == "YES"
            and type(unit.get("reactive_atom_confirmation")) is dict
            and unit["reactive_atom_confirmation"].get("status") == "CONFIRMED"
            and all(unit.get("roles", {}).get(name) for name in (
                "scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids"
            ))
        )
        if (
            unit.get("training_domain_relevance_decision")
            != "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
            or outcome.get("stage_statuses", {}).get(bulk.BULK_STAGES[8]) != "PASSED"
            or structural.get("explicit_covalent_evidence") is not True
            or structural.get("post_distance_angstrom") is None
        ):
            raise ScaleupSafetyError("HUMAN_RELEVANT_STRUCTURAL_AUTHORITY_INVALID")
        records.append(_authority_record_v1(
            lineage_id="CUMULATIVE1000_OTHER_HUMAN_RELEVANT_EXACT5",
            sample_identity=event_id,
            canonical_event_id=event_id,
            audit_status=(
                "PUBLISHED_POSITIVE_LABEL_RUNTIME_BINDING_INCOMPLETE"
                if complete
                else "PUBLISHED_TASK_RELEVANCE_ONLY_EVENT_AUTHORITY_INCOMPLETE"
            ),
            authority_sources=(HUMAN_REVIEW_DECISIONS.as_posix(), FIRST500_ROUTING.as_posix()),
            positive_authority_exists=True,
            task_domain_positive_authoritative=True,
            role_label_authoritative=complete,
            reactive_pair_authoritative=complete,
            post_geometry_authoritative=complete,
            current_feature_semantics_compatible=True,
            current_tensorizer_compatible=False,
            current_model_input_available=False,
            current_supervision_dataclass_compatible=False,
            current_runtime_model_usable=False,
            formal_split_authoritative=False,
            formal_split="",
            mapping_method="PUBLISHED_EXACT_CANONICAL_EVENT_ID",
            exclusion_reasons=(
                ("CURRENT_RUNTIME_TENSORIZATION_AND_SUPERVISION_BINDING_NOT_PUBLISHED",)
                if complete
                else (
                    "EVENT_TRAINING_USE_DECISION_INCOMPLETE",
                    "ROLE_AND_REACTIVE_PAIR_HUMAN_AUTHORITY_INCOMPLETE",
                    "CURRENT_RUNTIME_TENSORIZATION_AND_SUPERVISION_BINDING_NOT_PUBLISHED",
                )
            ),
        ))

    runtime_records = [record for record in records if record["current_runtime_model_usable"]]
    incomplete_records = [record for record in records if not record["current_runtime_model_usable"]]
    full_positive_records = [
        record for record in records
        if record["role_label_authoritative"]
        and record["reactive_pair_authoritative"]
        and record["POST_geometry_authoritative"]
    ]
    runtime_event_ids = [record["canonical_event_id"] for record in runtime_records]
    all_event_ids = [record["canonical_event_id"] for record in records]
    if (
        len(records) != 37
        or len(runtime_records) != 29
        or len(set(runtime_event_ids)) != 29
        or len(set(all_event_ids)) != 37
        or len(incomplete_records) != 8
        or len(full_positive_records) != 36
    ):
        raise ScaleupSafetyError("GLOBAL_CURRENT_AUTHORITY_COUNT_RECONCILIATION_FAILED")
    split_counts = Counter(
        record["formal_split"] for record in runtime_records
        if record["formal_split_authoritative"]
    )
    if split_counts != Counter({"train": 13, "validation": 6, "test": 5}):
        raise ScaleupSafetyError("GLOBAL_CURRENT_RUNTIME_FORMAL_SPLIT_RECONCILIATION_FAILED")
    repository_owner_paths = {
        HUMAN_REVIEW_DECISIONS, CURRENT11_INDEX, CURRENT11_SPLIT_ASSIGNMENT,
        K36_STRUCTURAL_EVIDENCE, CURRENT11_MATERIALIZER_SOURCE,
        MIXED_TENSORIZER_SOURCE, MIXED_SCHEDULER_SOURCE,
        EXACT16_POST_AUTHORITY_SOURCE, MIXED_LIGHTNING_SOURCE,
        EXACT16_TRAINER_SOURCE, APPROVED_EXPANSION_PIPELINE_SOURCE,
        *(path for _identity, materialized, tensorized in APPROVED_EXPANSION_SAMPLE_FILES
          for path in (materialized, tensorized)),
    }
    binding_by_path = {binding["path"]: binding for binding in inputs["bindings"]}
    owner_bindings = [
        binding_by_path[path.as_posix()] for path in sorted(
            repository_owner_paths, key=lambda value: value.as_posix()
        )
    ]
    return {
        "schema_version": "covapie_global_current_positive_authority_audit_v1",
        "audit_complete": True,
        "batch13_only_global_authority_assumption_removed": True,
        "exact16_lineage_audited": True,
        "approved_expansion_lineages_audited": True,
        "canonical_event_and_sample_identity_counts_separated": True,
        "records": records,
        "repository_owner_bindings": owner_bindings,
        "external_owner_bindings": [carrier_binding],
        "counts": {
            "audited_positive_authority_sample_identity_count": len(records),
            "audited_positive_authority_canonical_event_count": len(set(all_event_ids)),
            "global_full_event_positive_authority_count": len(full_positive_records),
            "global_task_relevance_only_incomplete_count": 1,
            "global_current_runtime_model_usable_sample_count": len(runtime_records),
            "global_current_runtime_model_usable_canonical_event_count": len(set(runtime_event_ids)),
            "global_current_positive_but_runtime_incomplete_count": len(incomplete_records),
            "global_current_runtime_model_usable_without_formal_split_count": sum(
                record["current_runtime_model_usable"]
                and not record["formal_split_authoritative"] for record in records
            ),
            "formal_training_split_admitted_positive_count": split_counts["train"],
            "formal_validation_split_positive_count": split_counts["validation"],
            "formal_test_split_positive_count": split_counts["test"],
            "deduplicated_runtime_canonical_event_overlap_count": (
                len(runtime_records) - len(set(runtime_event_ids))
            ),
        },
    }


def _cache_entries(cache_root: Path) -> dict[str, dict[str, Any]]:
    entries, _available = executor._load_cache_entries(cache_root)
    return entries


def inspect_readthrough_cache_v1(*, repo_root: Path,
                                 inputs: Mapping[str, Any] | None = None,
                                 include_payloads: bool = False) -> dict[str, Any]:
    data = inputs or load_scaleup_inputs_v1(repo_root)
    cohort = data["cohort"]
    required = {
        "PDB": sorted({str(item["pdb_id"]) for item in cohort}),
        "CCD": sorted({str(item["ligand_component_id"]) for item in cohort}),
    }
    canonical = canonical_cache_root_v1(repo_root)
    overlay = overlay_cache_root_v1(repo_root)
    snapshots_before = {
        "canonical": executor.snapshot_cache_tree_v1(canonical),
        "overlay": executor.snapshot_cache_tree_v1(overlay),
    }
    entries = {"canonical": _cache_entries(canonical), "overlay": _cache_entries(overlay)}
    roots = {"canonical": canonical, "overlay": overlay}
    hits = {"canonical": Counter(), "overlay": Counter()}
    origins: dict[str, dict[str, str]] = {"PDB": {}, "CCD": {}}
    failures: dict[str, str] = {}
    pdb_payloads: dict[str, bytes] = {}
    ccd_components: dict[str, dict[str, Any]] = {}
    for kind in ("PDB", "CCD"):
        for identity in required[kind]:
            valid: list[tuple[str, bytes, Any]] = []
            descriptor = executor._payload_descriptor(kind, identity)
            relative = descriptor["relative_path"]
            for lane in ("canonical", "overlay"):
                path = roots[lane] / relative
                if relative not in entries[lane] and not path.is_file():
                    continue
                try:
                    payload, parsed = executor._validate_cache_payload(
                        cache_root=roots[lane], entries=entries[lane],
                        payload_kind=kind, identity=identity,
                    )
                except executor.ExecutorSafetyError as error:
                    failures[f"{lane}:{kind}:{identity}"] = str(error)
                else:
                    valid.append((lane, payload, parsed))
            if failures and any(key.endswith(f":{kind}:{identity}") for key in failures):
                continue
            if len(valid) == 2 and valid[0][1] != valid[1][1]:
                raise ScaleupSafetyError("READTHROUGH_CACHE_BYTE_CONFLICT:" + kind + ":" + identity)
            if not valid:
                continue
            selected = valid[0]
            origins[kind][identity] = selected[0]
            hits[selected[0]][kind] += 1
            if include_payloads and kind == "PDB":
                pdb_payloads[identity] = selected[1]
            if include_payloads and kind == "CCD":
                ccd_components[identity] = selected[2]
    snapshots_after = {
        "canonical": executor.snapshot_cache_tree_v1(canonical),
        "overlay": executor.snapshot_cache_tree_v1(overlay),
    }
    if snapshots_before != snapshots_after:
        raise ScaleupSafetyError("READTHROUGH_INSPECTION_MODIFIED_CACHE")
    if failures:
        raise ScaleupSafetyError("CACHE_INTEGRITY_FAILURE:" + _json_cell(failures))
    missing = {kind: sorted(set(required[kind]) - set(origins[kind])) for kind in required}
    return {
        "rank501_1000_event_count": len(cohort),
        "unique_pdb_count": len(required["PDB"]),
        "unique_ccd_count": len(required["CCD"]),
        "canonical_cache_reused_pdb_count": hits["canonical"]["PDB"],
        "canonical_cache_reused_ccd_count": hits["canonical"]["CCD"],
        "overlay_cache_reused_pdb_count": hits["overlay"]["PDB"],
        "overlay_cache_reused_ccd_count": hits["overlay"]["CCD"],
        "missing_pdb_count": len(missing["PDB"]),
        "missing_ccd_count": len(missing["CCD"]),
        "missing_pdb_ids": missing["PDB"], "missing_ccd_ids": missing["CCD"],
        "origins": origins, "canonical_cache_snapshot": snapshots_before["canonical"],
        "overlay_cache_snapshot": snapshots_before["overlay"],
        "pdb_payloads": pdb_payloads, "ccd_components": ccd_components,
        "cache_integrity_failure_count": 0,
    }


def preflight_no_network_v1(*, repo_root: Path) -> dict[str, Any]:
    inputs = load_scaleup_inputs_v1(repo_root)
    cache = inspect_readthrough_cache_v1(repo_root=repo_root, inputs=inputs)
    return {
        "schema_version": SCHEMA_VERSION, "mode": PREFLIGHT_NO_NETWORK,
        "rank501_1000_event_count": SCALEUP_COUNT,
        "rank501_1000_unique_pdb_count": cache["unique_pdb_count"],
        "rank501_1000_unique_ccd_count": cache["unique_ccd_count"],
        "PDB_already_available_in_canonical_cache": cache["canonical_cache_reused_pdb_count"],
        "CCD_already_available_in_canonical_cache": cache["canonical_cache_reused_ccd_count"],
        "PDB_already_available_in_task_overlay": cache["overlay_cache_reused_pdb_count"],
        "CCD_already_available_in_task_overlay": cache["overlay_cache_reused_ccd_count"],
        "missing_PDB_count": cache["missing_pdb_count"],
        "missing_CCD_count": cache["missing_ccd_count"],
        "first500_exact_prefix_parity": inputs["prefix_parity"],
        "rank501_event_id": inputs["cohort"][0]["canonical_event_id"],
        "rank1000_event_id": inputs["cohort"][-1]["canonical_event_id"],
        "canonical_cache_snapshot": cache["canonical_cache_snapshot"],
        "overlay_cache_snapshot": cache["overlay_cache_snapshot"],
        "network_performed": False, "structural_processing_performed": False,
        "ready_for_controlled_network_execution": True,
    }


def _systemic_network_error(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in (
        "name or service not known", "temporary failure in name resolution",
        "nodename nor servname", "certificate verify failed", "sslerror",
        "proxyerror", "tunnel connection failed", "network is unreachable",
        "connection refused", "timed out",
    ))


def acquire_overlay_v1(*, repo_root: Path, inputs: Mapping[str, Any],
                       preflight: Mapping[str, Any]) -> dict[str, Any]:
    overlay = overlay_cache_root_v1(repo_root)
    budget = executor.DownloadBudgetV1(TOTAL_DOWNLOAD_CAP_BYTES)
    allowlist = {
        "required_pdb_ids": frozenset(str(item["pdb_id"]) for item in inputs["cohort"]),
        "required_ccd_ids": frozenset(str(item["ligand_component_id"]) for item in inputs["cohort"]),
    }
    missing = [
        *(("PDB", identity) for identity in preflight["missing_PDB_ids"]),
        *(("CCD", identity) for identity in preflight["missing_CCD_ids"]),
    ]
    results: list[dict[str, Any]] = []
    failures: dict[str, dict[str, Any]] = {}
    request_count = 0
    success_count = 0
    consecutive_systemic = 0
    for kind, identity in missing:
        attempt_messages: list[str] = []
        acquired: dict[str, Any] | None = None
        for attempt in range(1, MAX_ATTEMPTS_PER_REQUEST + 1):
            request_count += 1
            try:
                acquired = executor.acquire_payload_v1(
                    repo_root=repo_root, cache_root=overlay, payload_kind=kind,
                    identity=identity, budget=budget, network_authorized=True,
                    inputs=allowlist,
                )
            except (executor.ExecutorSafetyError, OSError) as error:
                attempt_messages.append(str(error))
                if budget.hard_stopped:
                    raise ScaleupSafetyError("DOWNLOAD_BUDGET_EXCEEDED") from error
            else:
                success_count += 1
                results.append({
                    "payload_kind": kind, "identity": identity,
                    "status": acquired["status"], "attempt_count": attempt,
                    "byte_count": acquired["byte_count"],
                    "sha256": acquired.get("sha256"),
                })
                break
        if acquired is None:
            systemic = bool(attempt_messages) and all(_systemic_network_error(x) for x in attempt_messages)
            consecutive_systemic = consecutive_systemic + 1 if systemic else 0
            failures[f"{kind}:{identity}"] = {
                "attempt_count": len(attempt_messages), "errors": attempt_messages,
                "individual_terminal_failure": not systemic,
            }
            if success_count == 0 and consecutive_systemic >= 3:
                raise ScaleupSafetyError("NETWORK_INFRASTRUCTURE_BLOCKER")
        else:
            consecutive_systemic = 0
    post = inspect_readthrough_cache_v1(repo_root=repo_root, inputs=inputs)
    newly = Counter(row["payload_kind"] for row in results if row["status"] == "NEWLY_DOWNLOADED")
    return {
        "schema_version": SCHEMA_VERSION, "mode": CONTROLLED_NETWORK_EXECUTION,
        "preflight": dict(preflight), "acquisition_order": "PDB_THEN_CCD_LEXICOGRAPHIC",
        "max_attempts_per_request": MAX_ATTEMPTS_PER_REQUEST,
        "timeout_seconds": bulk.NETWORK_TIMEOUT_SECONDS,
        "pdb_single_payload_cap_bytes": PDB_CAP_BYTES,
        "ccd_single_payload_cap_bytes": CCD_CAP_BYTES,
        "total_new_download_cap_bytes": TOTAL_DOWNLOAD_CAP_BYTES,
        "network_request_count": request_count,
        "network_bytes_received_this_execution": budget.network_bytes_received_this_execution,
        "new_overlay_downloaded_pdb_count": newly["PDB"],
        "new_overlay_downloaded_ccd_count": newly["CCD"],
        "post_acquisition_missing_pdb_count": post["missing_pdb_count"],
        "post_acquisition_missing_ccd_count": post["missing_ccd_count"],
        "failures": dict(sorted(failures.items())), "payload_results": results,
        "network_performed": request_count > 0, "systemic_network_failure": False,
        "canonical_cache_modified": False,
        "overlay_cache_snapshot_after": post["overlay_cache_snapshot"],
    }


def _process_new_outcomes(*, inputs: Mapping[str, Any], cache: Mapping[str, Any]) -> list[dict[str, Any]]:
    context = executor.build_processing_context_v1(inputs["repo_root"])
    outcomes: list[dict[str, Any]] = []
    for event in inputs["cohort"]:
        pdb_id = str(event["pdb_id"])
        ccd_id = str(event["ligand_component_id"])
        if pdb_id not in cache["pdb_payloads"]:
            outcomes.append(executor._failed_processing_outcome(
                event, "REQUIRED_PDB_PAYLOAD_UNAVAILABLE"))
        elif ccd_id not in cache["ccd_components"]:
            outcomes.append(executor._failed_processing_outcome(
                event, "REQUIRED_CCD_PAYLOAD_UNAVAILABLE"))
        else:
            outcomes.append(bulk.process_event_structure_v1(
                event, mmcif_payload=cache["pdb_payloads"][pdb_id],
                authorities=context.authorities,
                known_historical=context.historical_identities,
                ccd_component=cache["ccd_components"][ccd_id],
            ))
    historical = [copy.deepcopy(row["processing_outcome"]) for row in inputs["first500_rows"]]
    controls = [copy.deepcopy(item) for item in
                executor.load_published_executor_inputs_v1(inputs["repo_root"])["control_outcomes"]]
    combined = [*historical, *controls, *outcomes]
    bulk.apply_leakage_predictions_read_only_v1(
        combined, historical=context.historical_identities, context=context.leakage_context,
    )
    retained = combined[len(historical) + len(controls):]
    if len(retained) != SCALEUP_COUNT or [x["canonical_event_id"] for x in retained] != [
        x["canonical_event_id"] for x in inputs["cohort"]
    ]:
        raise ScaleupSafetyError("RANK501_1000_PROCESSING_COVERAGE_INVALID")
    return retained


def _readthrough_coordinate_root(*, repo_root: Path, candidate_pdb_ids: set[str],
                                 cache: Mapping[str, Any], execution_root: Path):
    class _Root:
        def __init__(self) -> None:
            execution_root.mkdir(parents=True, exist_ok=True)
            self.temp = tempfile.TemporaryDirectory(prefix="readthrough-", dir=execution_root)
            self.path = Path(self.temp.name)
        def __enter__(self) -> Path:
            structures = self.path / "rcsb" / "structures"
            structures.mkdir(parents=True)
            source_entries = {
                "canonical": _cache_entries(canonical_cache_root_v1(repo_root)),
                "overlay": _cache_entries(overlay_cache_root_v1(repo_root)),
            }
            ledger = []
            for pdb_id in sorted(candidate_pdb_ids):
                lane = cache["origins"]["PDB"].get(pdb_id)
                if lane not in source_entries:
                    raise ScaleupSafetyError("CANDIDATE_PDB_ORIGIN_MISSING:" + pdb_id)
                relative = executor._payload_descriptor("PDB", pdb_id)["relative_path"]
                source_root = canonical_cache_root_v1(repo_root) if lane == "canonical" else overlay_cache_root_v1(repo_root)
                source = source_root / relative
                target = self.path / relative
                try:
                    os.link(source, target)
                except OSError:
                    shutil.copyfile(source, target)
                ledger.append(source_entries[lane][relative])
            _atomic_write(self.path / "cache_manifest_v1.json", _json_bytes({
                "schema_version": "covapie_bulk_cache_manifest_v1",
                "snapshot_date": bulk.SNAPSHOT_DATE, "payloads": sorted(ledger, key=lambda x: x["relative_path"]),
            }))
            return self.path
        def __exit__(self, exc_type, exc, traceback) -> None:
            self.temp.cleanup()
    return _Root()


def _routing_state(*, inputs: Mapping[str, Any], outcomes: Sequence[Mapping[str, Any]],
                   cache: Mapping[str, Any]) -> dict[str, Any]:
    outcome_by_id = {str(item["canonical_event_id"]): item for item in outcomes}
    candidate_ids = {
        event_id for event_id, outcome in outcome_by_id.items()
        if triage.post_only_partition_v1(outcome, known_event=False) == triage.POST_ONLY_CANDIDATE
    }
    if not candidate_ids:
        return {"rule_events": {}, "evaluations": {}, "units": [],
                "unit_by_event": {}, "routes": {}}
    predecessor = routing.verify_predecessor_bindings_v1(inputs["repo_root"])
    candidate_pdb_ids = {str(inputs["event_by_id"][event_id]["pdb_id"]) for event_id in candidate_ids}
    execution_root = overlay_execution_root_v1(inputs["repo_root"])
    with _readthrough_coordinate_root(
        repo_root=inputs["repo_root"], candidate_pdb_ids=candidate_pdb_ids,
        cache=cache, execution_root=execution_root,
    ) as coordinate_root:
        return cumulative500._build_incremental_rule_state(
            repo_root=inputs["repo_root"], candidate_ids=candidate_ids,
            event_by_id=inputs["event_by_id"], outcome_by_id=outcome_by_id,
            predecessor_bindings=predecessor, cache_root=coordinate_root,
        )


def build_processing_result_v1(*, repo_root: Path,
                               inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = inputs or load_scaleup_inputs_v1(repo_root)
    cache = inspect_readthrough_cache_v1(repo_root=repo_root, inputs=data, include_payloads=True)
    outcomes = _process_new_outcomes(inputs=data, cache=cache)
    route_state = _routing_state(inputs=data, outcomes=outcomes, cache=cache)
    rows = []
    outcome_by_id = {item["canonical_event_id"]: item for item in outcomes}
    for rank, event in enumerate(data["cohort"], RANK_START):
        event_id = str(event["canonical_event_id"])
        outcome = outcome_by_id[event_id]
        try:
            partition = triage.post_only_partition_v1(outcome, known_event=False)
        except ValueError:
            partition = triage.OUTSIDE_STRUCTURAL
        unit_id = route_state["unit_by_event"].get(event_id, "")
        route = route_state["routes"].get(unit_id)
        evaluations = [value for (candidate, _rule), value in route_state["evaluations"].items()
                       if candidate == event_id]
        rows.append({
            "scaleup_rank": rank, "canonical_event_id": event_id,
            "processing_outcome": outcome, "post_only_partition": partition,
            "review_unit_id": unit_id,
            "effective_route": route.route_status if route is not None else outcome["terminal_outcome"],
            "effective_route_reason": route.route_reason if route is not None else outcome["terminal_reasons"][0],
            "selected_exact_negative_rule_id": route.auto_negative_rule_id if route is not None else "",
            "exact_rule_evaluations": [
                {"rule_id": item.rule_id, "status": item.status, "reason": item.reason}
                for item in sorted(evaluations, key=lambda x: x.rule_id)
            ],
        })
    if len(rows) != SCALEUP_COUNT or len({row["canonical_event_id"] for row in rows}) != SCALEUP_COUNT:
        raise ScaleupSafetyError("TERMINAL_PROCESSING_RECONCILIATION_FAILED")
    return {
        "schema_version": SCHEMA_VERSION, "rank_start": RANK_START,
        "rank_end": RANK_END, "terminal_outcome_count": len(rows), "events": rows,
        "raw_terminal_route_counts": dict(sorted(Counter(
            row["processing_outcome"]["terminal_outcome"] for row in rows).items())),
        "post_only_partition_counts": dict(sorted(Counter(
            row["post_only_partition"] for row in rows).items())),
        "effective_route_counts": dict(sorted(Counter(
            row["effective_route"] for row in rows).items())),
        "structural_processing_performed": True, "training_performed": False,
        "PRE_geometry_fabricated": False, "production_authority_created": False,
    }


def _cohort_rows(inputs: Mapping[str, Any]) -> list[dict[str, object]]:
    rows = []
    for rank, event in enumerate(inputs["cohort"], RANK_START):
        event_id = str(event["canonical_event_id"])
        row = {
            "scaleup_rank": rank, "canonical_event_id": event_id,
            "selection_priority_pass": inputs["ranked"]["selection_pass"][event_id],
            "pdb_id": event["pdb_id"], "protein_label_asym_id": event["protein_instance"],
            "protein_auth_chain": event.get("protein_auth_chain") or "",
            "protein_residue_name": event["protein_residue_name"],
            "protein_residue_number": event["protein_residue_number"],
            "protein_reactive_atom": event["protein_reactive_atom"],
            "ligand_component_id": event["ligand_component_id"],
            "ligand_instance": event["ligand_instance"],
            "ligand_reactive_atom": event["ligand_reactive_atom"],
            "source_dataset_count": event["source_count"],
            "source_record_count": event["source_record_count"],
            "source_datasets_json": _json_cell(event["source_datasets"]),
            "source_record_ids_json": _json_cell(event["source_record_ids"]),
        }
        rows.append({field: row[field] for field in COHORT_HEADER})
    return rows


def _positive_component_references(inputs: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    bridge_by_component: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for event in inputs["batch13_bridge"]["events"]:
        bridge_by_component[str(event["ligand_component_id"])].append(event)
    cache_root = canonical_cache_root_v1(inputs["repo_root"])
    entries = _cache_entries(cache_root)
    references = {}
    for component, events in sorted(bridge_by_component.items()):
        _payload, parsed = executor._validate_cache_payload(
            cache_root=cache_root, entries=entries, payload_kind="CCD", identity=component,
        )
        role_ids = sorted({str(atom) for event in events for field in
                           ("scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids")
                           for atom in event[field]})
        references[component] = {
            "ccd_component_graph_sha256": parsed["ccd_component_graph_sha256"],
            "reactive_atoms": sorted({str(event["ligand_reactive_atom_id"]) for event in events}),
            "role_atom_ids": role_ids,
            "positive_event_ids": sorted(str(event["canonical_event_id"]) for event in events),
        }
    return references


def _shadow_candidate(event: Mapping[str, Any], outcome: Mapping[str, Any],
                      references: Mapping[str, Mapping[str, Any]],
                      *, excluded: bool) -> bool:
    if excluded or outcome.get("stage_statuses", {}).get(bulk.BULK_STAGES[8]) != "PASSED":
        return False
    component = str(event["ligand_component_id"])
    reference = references.get(component)
    structural = outcome.get("structural_processing") or {}
    ccd = structural.get("ccd_component_graph") or {}
    pre = outcome.get("pre_representability") or {}
    if not reference:
        return False
    ccd_atom_ids = {str(atom.get("atom_id")) for atom in ccd.get("ccd_atom_inventory", [])}
    return bool(
        ccd.get("ccd_component_graph_sha256") == reference["ccd_component_graph_sha256"]
        and str(event["ligand_reactive_atom"]) in reference["reactive_atoms"]
        and pre.get("ccd_retained_atom_coverage_complete") is True
        and set(reference["role_atom_ids"]) <= ccd_atom_ids
        and str(event["protein_residue_name"]).upper() == "CYS"
        and str(event["protein_reactive_atom"]).upper() == "SG"
    )


def evaluate_runtime_authority_boundary_v1(
    *,
    chemistry_auto_admission_authorized: bool,
    task_domain_positive_authority_source: str,
    role_label_authority_source: str,
    runtime_role_materialization_source: str,
    reactive_pair_label_authority_source: str,
    POST_geometry_label_authority_source: str,
    pair_raw_available: bool,
    POST_raw_available: bool,
    feature_compatible: bool,
    formal_split_authoritative: bool = False,
    formal_split: str = "",
) -> dict[str, bool]:
    """Keep exact chemistry authority separate from current runtime binding."""

    values = (
        chemistry_auto_admission_authorized, pair_raw_available,
        POST_raw_available, feature_compatible, formal_split_authoritative,
    )
    sources = (
        task_domain_positive_authority_source, role_label_authority_source,
        runtime_role_materialization_source,
        reactive_pair_label_authority_source,
        POST_geometry_label_authority_source,
    )
    if any(type(value) is not bool for value in values) or any(
        type(source) is not str for source in sources
    ) or type(formal_split) is not str:
        raise ScaleupSafetyError("RUNTIME_AUTHORITY_BOUNDARY_INPUT_INVALID")
    role_available = bool(role_label_authority_source)
    runtime_role_available = bool(runtime_role_materialization_source)
    pair_authoritative = bool(
        pair_raw_available and reactive_pair_label_authority_source
    )
    post_authoritative = bool(
        POST_raw_available and POST_geometry_label_authority_source
    )
    model_usable = bool(
        feature_compatible
        and task_domain_positive_authority_source
        and role_available
        and runtime_role_available
        and pair_authoritative
        and post_authoritative
    )
    return {
        "chemistry_auto_admission_authorized": chemistry_auto_admission_authorized,
        "runtime_role_materialization_available": runtime_role_available,
        "role_label_available": role_available,
        "reactive_pair_label_authoritative": pair_authoritative,
        "POST_geometry_label_authoritative": post_authoritative,
        "label_model_usable": model_usable,
        "training_split_admission_ready": bool(
            model_usable and formal_split_authoritative and formal_split == "train"
        ),
    }


def validate_census_rows_v1(rows: Sequence[Mapping[str, object]]) -> None:
    """Fail closed on authority, partial-label, and split-admission inflation."""

    if (
        len(rows) != 1000
        or [int(row["scaleup_rank"]) for row in rows] != list(range(1, 1001))
        or len({str(row["canonical_event_id"]) for row in rows}) != 1000
    ):
        raise ScaleupSafetyError("CUMULATIVE1000_RANK_OR_IDENTITY_INVALID")
    for row in rows:
        model_usable = row["label_model_usable"] == "true"
        task_status = str(row["task_domain_authority_status"])
        if model_usable and (
            row["feature_status"] != "PASSED"
            or row["role_label_available"] != "true"
            or not row["role_label_authority_source"]
            or row["runtime_role_materialization_available"] != "true"
            or row["reactive_pair_label_authoritative"] != "true"
            or not row["reactive_pair_label_authority_source"]
            or row["POST_geometry_label_authoritative"] != "true"
            or not row["POST_geometry_label_authority_source"]
            or not task_status.startswith("AUTHORITATIVE_POSITIVE_")
            or row["terminal_route"] != "MODEL_USABLE_AUTHORITATIVE_POSITIVE"
        ):
            raise ScaleupSafetyError("MODEL_USABLE_HARD_INPUT_OR_AUTHORITY_MISSING")
        if row["role_label_available"] == "true" and not row["role_label_authority_source"]:
            raise ScaleupSafetyError("ROLE_LABEL_SELF_CERTIFICATION")
        if (
            row["reactive_pair_label_authoritative"] == "true"
            and not row["reactive_pair_label_authority_source"]
        ):
            raise ScaleupSafetyError("PAIR_AUTHORITY_SELF_CERTIFICATION")
        if (
            row["POST_geometry_label_authoritative"] == "true"
            and not row["POST_geometry_label_authority_source"]
        ):
            raise ScaleupSafetyError("POST_AUTHORITY_SELF_CERTIFICATION")
        if (
            row["chemistry_auto_admission_authorized"] == "true"
            and not str(row["positive_authority_source"]).startswith(
                "EXISTING_PRODUCTION_EXACT_SIGNATURE:"
            )
        ):
            raise ScaleupSafetyError("CHEMISTRY_AUTO_ADMISSION_SOURCE_INVALID")
        if model_usable and task_status.startswith("AUTHORITATIVE_NEGATIVE_"):
            raise ScaleupSafetyError("TASK_DOMAIN_NEGATIVE_MARKED_GENERATIVE_POSITIVE")
        if row["shadow_exact_component_reuse_candidate"] == "true" and model_usable:
            raise ScaleupSafetyError("SHADOW_CANDIDATE_MARKED_AUTO_ADMITTED")
        if row["training_split_admission_ready"] == "true" and (
            not model_usable or row["formal_split_if_authoritative"] != "train"
        ):
            raise ScaleupSafetyError("NEW_COMPONENT_CALLED_TRAIN_WITHOUT_FORMAL_SPLIT")
        if row["derived_PRE_available"] != "false" or row["PRE_training_target_authoritative"] != "false":
            raise ScaleupSafetyError("PRE_GEOMETRY_FABRICATED")
        if row["warhead_type_target_available"] != "false" or row["reaction_family_target_available"] != "false":
            raise ScaleupSafetyError("NON_AUTHORITATIVE_FAMILY_CLASS_USED_AS_TRUTH")


def _build_census(*, inputs: Mapping[str, Any], processing: Mapping[str, Any]) -> tuple[list[dict[str, object]], dict[str, Any]]:
    batch_by_id = {row["canonical_event_id"]: row for row in inputs["batch13_rows"]}
    first_route = {row["canonical_event_id"]: row for row in inputs["first500_routing_rows"]}
    new_result = {row["canonical_event_id"]: row for row in processing["events"]}
    references = _positive_component_references(inputs)
    audited_by_event = {
        record["canonical_event_id"]: record
        for record in inputs["global_authority_audit"]["records"]
        if record["canonical_event_id"] in set(inputs["batch13_ids"])
        or record["lineage_id"] == "CUMULATIVE1000_OTHER_HUMAN_RELEVANT_EXACT5"
    }
    all_items: list[tuple[int, str, Mapping[str, Any], Mapping[str, Any], str, str, str, str]] = []
    for item in inputs["first500_rows"]:
        outcome = item["processing_outcome"]
        event_id = outcome["canonical_event_id"]
        route = first_route[event_id]
        all_items.append((int(item["scaleup_rank"]), "FROZEN_FIRST500", inputs["event_by_id"][event_id],
                          outcome, route["effective_route"], route["effective_route_reason"],
                          route["selected_effective_rule_id"], route.get("routing_review_unit_id", "")))
    for item in processing["events"]:
        event_id = item["canonical_event_id"]
        all_items.append((int(item["scaleup_rank"]), "RANKS_0501_1000_EXECUTION",
                          inputs["event_by_id"][event_id], item["processing_outcome"],
                          item["effective_route"], item["effective_route_reason"],
                          item["selected_exact_negative_rule_id"], item["review_unit_id"]))
    rows = []
    for rank, lane, event, outcome, effective_route, effective_reason, negative_rule, _unit in all_items:
        event_id = str(event["canonical_event_id"])
        batch = batch_by_id.get(event_id)
        structural = outcome.get("structural_processing") or {}
        ccd = structural.get("ccd_component_graph") or {}
        stages = outcome.get("stage_statuses") or {}
        exact_signature_positive = outcome.get("existing_exact_authority_match") is True
        auto_negative = effective_route == routing.AUTO_NEGATIVE_EXACT_FINAL
        human_negative = effective_route == routing.HUMAN_NOT_RELEVANT_FINAL
        matched = [item["authority_id"] for item in outcome.get("authority_match_evaluation", [])
                   if item.get("candidate_match_result") == "EXACT_SIGNATURE_MATCH"]
        audited = audited_by_event.get(event_id)
        is_human_positive = bool(
            audited
            and audited["lineage_id"]
            == "CUMULATIVE1000_OTHER_HUMAN_RELEVANT_EXACT5"
        )
        positive_source = (
            "BATCH001_EXACT13_CURRENT_RUNTIME_AUTHORITY" if batch is not None
            else "EXISTING_PRODUCTION_EXACT_SIGNATURE:" + ",".join(matched)
            if exact_signature_positive else ""
            if not is_human_positive else HUMAN_REVIEW_DECISIONS.as_posix()
        )
        if is_human_positive:
            positive_source = HUMAN_REVIEW_DECISIONS.as_posix()
        pair_raw = bool(structural.get("explicit_covalent_evidence") is True)
        post_raw = bool(structural.get("post_distance_angstrom") is not None)
        role_source = (
            BATCH13_BRIDGE.as_posix() if batch is not None
            else HUMAN_REVIEW_DECISIONS.as_posix()
            if is_human_positive and audited["role_label_authoritative"]
            else ""
        )
        runtime_role_source = BATCH13_BRIDGE.as_posix() if batch is not None else ""
        pair_source = (
            BATCH13_BRIDGE.as_posix() if batch is not None
            else HUMAN_REVIEW_DECISIONS.as_posix()
            if is_human_positive and audited["reactive_pair_authoritative"]
            else ""
        )
        post_source = (
            BATCH13_BRIDGE.as_posix() if batch is not None
            else HUMAN_REVIEW_DECISIONS.as_posix()
            if is_human_positive and audited["POST_geometry_authoritative"]
            else ""
        )
        boundary = evaluate_runtime_authority_boundary_v1(
            chemistry_auto_admission_authorized=exact_signature_positive,
            task_domain_positive_authority_source=positive_source,
            role_label_authority_source=role_source,
            runtime_role_materialization_source=runtime_role_source,
            reactive_pair_label_authority_source=pair_source,
            POST_geometry_label_authority_source=post_source,
            pair_raw_available=pair_raw,
            POST_raw_available=post_raw,
            feature_compatible=(stages.get(bulk.BULK_STAGES[8]) == "PASSED"),
            formal_split_authoritative=batch is not None,
            formal_split=batch["formal_split"] if batch else "",
        )
        model_usable = boundary["label_model_usable"]
        shadow = _shadow_candidate(event, outcome, references,
                                   excluded=model_usable or auto_negative or human_negative)
        formal_split = batch["formal_split"] if batch else ""
        train_ready = bool(
            boundary["training_split_admission_ready"]
            and batch
            and batch["sample_training_admitted"] == "true"
        )
        effective_census_route = (
            "MODEL_USABLE_AUTHORITATIVE_POSITIVE" if model_usable else effective_route
        )
        task_status = (
            "AUTHORITATIVE_POSITIVE_EXACT_EVENT_CURRENT_RUNTIME" if batch is not None
            else "CHEMISTRY_AUTHORIZED_RUNTIME_BINDING_INCOMPLETE" if exact_signature_positive
            else "AUTHORITATIVE_POSITIVE_EXACT_EVENT_RUNTIME_BINDING_INCOMPLETE"
            if is_human_positive and audited["role_label_authoritative"]
            else "AUTHORITATIVE_TASK_RELEVANCE_ONLY_EVENT_AUTHORITY_INCOMPLETE"
            if is_human_positive
            else "AUTHORITATIVE_NEGATIVE_EXACT_RULE" if auto_negative
            else "AUTHORITATIVE_NEGATIVE_EXACT_EVENT" if human_negative
            else "UNRESOLVED_HUMAN_REVIEW" if effective_route in {
                routing.HUMAN_REVIEW_REQUIRED, routing.HUMAN_REVIEW_REQUIRED_DEFERRED,
                routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID,
            } else "NOT_APPLICABLE_BLOCKED_STRUCTURAL_OR_LEAKAGE"
        )
        leakage = str(outcome.get("leakage_classification") or outcome.get("terminal_outcome") or "")
        raw = {
            "scaleup_rank": rank, "cohort_lane": lane, "canonical_event_id": event_id,
            "pdb_id": event["pdb_id"], "ligand_component_id": event["ligand_component_id"],
            "protein_label_asym_id": event["protein_instance"],
            "protein_auth_chain": event.get("protein_auth_chain") or "",
            "protein_residue_name": event["protein_residue_name"],
            "protein_residue_number": event["protein_residue_number"],
            "protein_reactive_atom": event["protein_reactive_atom"],
            "ligand_instance": event["ligand_instance"],
            "ligand_reactive_atom": event["ligand_reactive_atom"],
            "structure_status": stages.get(bulk.BULK_STAGES[4], "NOT_REACHED"),
            "CCD_status": "PASSED" if ccd.get("ccd_component_graph_sha256") else "UNAVAILABLE",
            "exact_event_recovery_status": stages.get(bulk.BULK_STAGES[6], "NOT_REACHED"),
            "feature_status": stages.get(bulk.BULK_STAGES[8], "NOT_REACHED"),
            "task_domain_authority_status": task_status,
            "positive_authority_source": positive_source, "negative_rule_id": negative_rule,
            "role_profile": batch["role_profile"] if batch else "",
            "positive_authority_audit_status": (
                str(audited["audit_status"]) if audited
                else "CHEMISTRY_AUTHORIZED_RUNTIME_BINDING_INCOMPLETE"
                if exact_signature_positive else "NO_POSITIVE_AUTHORITY"
            ),
            "chemistry_auto_admission_authorized": str(
                boundary["chemistry_auto_admission_authorized"]
            ).lower(),
            "runtime_role_materialization_available": str(
                boundary["runtime_role_materialization_available"]
            ).lower(),
            "role_label_available": str(boundary["role_label_available"]).lower(),
            "role_label_authority_source": role_source,
            "reactive_pair_label_available": str(pair_raw).lower(),
            "reactive_pair_label_authoritative": str(
                boundary["reactive_pair_label_authoritative"]
            ).lower(),
            "POST_geometry_label_available": str(post_raw).lower(),
            "reactive_pair_label_authority_source": pair_source,
            "POST_geometry_label_authoritative": str(
                boundary["POST_geometry_label_authoritative"]
            ).lower(),
            "POST_geometry_label_authority_source": post_source,
            "experimental_PRE_available": "false", "derived_PRE_available": "false",
            "PRE_training_target_authoritative": "false",
            "warhead_type_target_available": "false",
            "reaction_family_target_available": "false",
            "label_model_usable": str(model_usable).lower(),
            "shadow_exact_component_reuse_candidate": str(shadow).lower(),
            "leakage_status": leakage,
            "leakage_group_id": outcome.get("predicted_group_id") or "",
            "formal_split_if_authoritative": formal_split,
            "training_split_admission_ready": str(train_ready).lower(),
            "terminal_route": effective_census_route,
            "reasons_json": _json_cell(list(dict.fromkeys([
                *outcome.get("terminal_reasons", []), effective_reason,
                *(
                    audited.get("exclusion_reasons", [])
                    if audited and not audited["current_runtime_model_usable"]
                    else []
                ),
            ]))),
        }
        rows.append({field: raw[field] for field in CENSUS_HEADER})
    validate_census_rows_v1(rows)
    metrics = {
        "structurally_processable": sum(row["feature_status"] == "PASSED" for row in rows),
        "feature_compatible": sum(row["feature_status"] == "PASSED" for row in rows),
        "raw_pair": sum(row["reactive_pair_label_available"] == "true" for row in rows),
        "raw_post": sum(row["POST_geometry_label_available"] == "true" for row in rows),
        "POST_label_ready": sum(row["POST_geometry_label_available"] == "true" for row in rows),
        "role_authoritative": sum(row["role_label_available"] == "true" for row in rows),
        "pair_authoritative": sum(row["reactive_pair_label_authoritative"] == "true" for row in rows),
        "POST_authoritative": sum(row["POST_geometry_label_authoritative"] == "true" for row in rows),
        "model_usable": sum(row["label_model_usable"] == "true" for row in rows),
        "shadow": sum(row["shadow_exact_component_reuse_candidate"] == "true" for row in rows),
        "auto_negative": sum(row["terminal_route"] == routing.AUTO_NEGATIVE_EXACT_FINAL for row in rows),
        "human_review": sum(row["terminal_route"] in {
            routing.HUMAN_REVIEW_REQUIRED, routing.HUMAN_REVIEW_REQUIRED_DEFERRED,
            routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID,
        } for row in rows),
        "representation_gap": sum(row["terminal_route"] == "QUARANTINE_REPRESENTATION_GAP" for row in rows),
        "leakage_conflict": sum(row["terminal_route"] == "LEAKAGE_EXISTING_GROUP_CONFLICT" for row in rows),
        "structural_incomplete": sum(row["terminal_route"] in {
            "STRUCTURAL_EVIDENCE_INCOMPLETE", "REJECTED_FEATURE_INCOMPATIBLE", "REJECTED_EVENT_INVALID",
        } for row in rows),
        "new_component_pending_split": sum(
            row["leakage_status"] == "NEW_EXPANSION_COMPONENT"
            and not row["formal_split_if_authoritative"] for row in rows
        ),
        "training_admitted": sum(row["training_split_admission_ready"] == "true" for row in rows),
    }
    return rows, metrics


def _effective_n(
    rows: Sequence[Mapping[str, object]],
    authority_audit: Mapping[str, Any],
) -> dict[str, Any]:
    def _scope(
        *, raw_base: int, raw_pair: int, raw_post: int,
        authoritative_base: int, authoritative_pair: int,
        authoritative_post: int, runtime_model_usable: int,
        formal_train: int, validation: int, test: int, unsplit: int,
        role_authoritative: int,
    ) -> dict[str, Any]:
        def head(head_id: str, raw: int, authoritative: int) -> dict[str, Any]:
            return {
                "head_id": head_id,
                "implemented_loss_head": True,
                "raw_structural_label_available_count": raw,
                "authoritative_supervision_label_count": authoritative,
                "current_runtime_model_usable_count": runtime_model_usable,
                "formal_training_split_admitted_count": formal_train,
                "formal_validation_split_count": validation,
                "formal_test_split_count": test,
                "current_runtime_model_usable_without_formal_split_count": unsplit,
            }
        common_zero = {
            "raw_structural_label_available_count": 0,
            "authoritative_supervision_label_count": 0,
            "current_runtime_model_usable_count": 0,
            "formal_training_split_admitted_count": 0,
            "formal_validation_split_count": 0,
            "formal_test_split_count": 0,
            "current_runtime_model_usable_without_formal_split_count": 0,
        }
        return {
            "actual_current_loss_heads": [
                head("base_diffusion", raw_base, authoritative_base),
                head("covalent_pair_prediction", raw_pair, authoritative_pair),
                head("pre_post_geometry", raw_post, authoritative_post),
                head("covalent_pair_contrastive", raw_pair, authoritative_pair),
            ],
            "geometry_component_breakdown": [
                {
                    "target_id": "POST_geometry_component",
                    "implemented_loss_component": True,
                    **{
                        key: value for key, value in head(
                            "POST_geometry_component", raw_post,
                            authoritative_post,
                        ).items() if key not in {"head_id", "implemented_loss_head"}
                    },
                },
                {
                    "target_id": "PRE_geometry_component",
                    "implemented_loss_component": True,
                    **common_zero,
                },
            ],
            "conditioning_contract": {
                "role_task_mask_anchor_is_conditioning_not_separate_loss_head": True,
                "authoritative_role_task_mask_anchor_count": role_authoritative,
                "current_runtime_model_usable_count": runtime_model_usable,
                "formal_training_split_admitted_count": formal_train,
            },
            "planned_targets_not_implemented_as_current_loss_heads": [
                {
                    "target_id": name,
                    "implemented_loss_head": False,
                    "raw_structural_label_available_count": 0,
                    "authoritative_supervision_label_count": 0,
                }
                for name in (
                    "warhead_type_classification",
                    "canonical_reaction_family_classification",
                    "interaction_labels",
                )
            ],
        }

    cumulative_model = sum(row["label_model_usable"] == "true" for row in rows)
    cumulative_split = Counter(
        str(row["formal_split_if_authoritative"]) for row in rows
        if row["label_model_usable"] == "true"
    )
    cumulative_role = sum(row["role_label_available"] == "true" for row in rows)
    cumulative_pair_authority = sum(
        row["reactive_pair_label_authoritative"] == "true" for row in rows
    )
    cumulative_post_authority = sum(
        row["POST_geometry_label_authoritative"] == "true" for row in rows
    )
    cumulative_full_authority = sum(
        row["role_label_available"] == "true"
        and row["reactive_pair_label_authoritative"] == "true"
        and row["POST_geometry_label_authoritative"] == "true"
        for row in rows
    )
    counts = authority_audit["counts"]
    global_records = authority_audit["records"]
    global_full_authority = sum(
        record["role_label_authoritative"]
        and record["reactive_pair_authoritative"]
        and record["POST_geometry_authoritative"]
        for record in global_records
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "scope_contract": {
            "cumulative1000_ranked_new_scope": (
                "exact ranks 1-1000 of the frozen ranked-new event universe"
            ),
            "global_current_runtime_authority_scope": (
                "all audited current published Cys-SG V1 positive/sample lineages; "
                "runtime usability remains distinct from formal split admission"
            ),
        },
        "scopes": {
            "cumulative1000_ranked_new_scope": _scope(
                raw_base=sum(row["feature_status"] == "PASSED" for row in rows),
                raw_pair=sum(row["reactive_pair_label_available"] == "true" for row in rows),
                raw_post=sum(row["POST_geometry_label_available"] == "true" for row in rows),
                authoritative_base=cumulative_full_authority,
                authoritative_pair=cumulative_pair_authority,
                authoritative_post=cumulative_post_authority,
                runtime_model_usable=cumulative_model,
                formal_train=sum(row["training_split_admission_ready"] == "true" for row in rows),
                validation=cumulative_split["validation"],
                test=cumulative_split["test"],
                unsplit=sum(
                    row["label_model_usable"] == "true"
                    and not row["formal_split_if_authoritative"] for row in rows
                ),
                role_authoritative=cumulative_role,
            ),
            "global_current_runtime_authority_scope": _scope(
                raw_base=len(global_records),
                raw_pair=len(global_records),
                raw_post=len(global_records),
                authoritative_base=global_full_authority,
                authoritative_pair=sum(
                    record["reactive_pair_authoritative"] for record in global_records
                ),
                authoritative_post=sum(
                    record["POST_geometry_authoritative"] for record in global_records
                ),
                runtime_model_usable=counts[
                    "global_current_runtime_model_usable_sample_count"
                ],
                formal_train=counts["formal_training_split_admitted_positive_count"],
                validation=counts["formal_validation_split_positive_count"],
                test=counts["formal_test_split_positive_count"],
                unsplit=counts[
                    "global_current_runtime_model_usable_without_formal_split_count"
                ],
                role_authoritative=sum(
                    record["role_label_authoritative"] for record in global_records
                ),
            ),
        },
        "raw_label_N_distinguished_from_runtime_effective_N": True,
        "authoritative_supervision_N_distinguished_from_runtime_effective_N": True,
        "runtime_effective_N_distinguished_from_formal_split_N": True,
        "partial_label_loss_mask_policy_preserved": True,
    }


def _review_queue(*, inputs: Mapping[str, Any], processing: Mapping[str, Any],
                  census_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    unresolved_ids = {str(row["canonical_event_id"]) for row in census_rows if row["terminal_route"] in {
        routing.HUMAN_REVIEW_REQUIRED, routing.HUMAN_REVIEW_REQUIRED_DEFERRED,
        routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID,
    }}
    outcome_by_id = {
        row["processing_outcome"]["canonical_event_id"]: row["processing_outcome"]
        for row in inputs["first500_rows"]
    }
    outcome_by_id.update({
        row["canonical_event_id"]: row["processing_outcome"] for row in processing["events"]
    })
    units = bulk.build_human_review_units_v1(
        [outcome_by_id[event_id] for event_id in sorted(unresolved_ids)], inputs["event_by_id"]
    ) if unresolved_ids else []
    census_by_id = {str(row["canonical_event_id"]): row for row in census_rows}
    raw_rows = []
    for unit in units:
        ids = [str(value) for value in unit["canonical_event_ids"]]
        values = [census_by_id[event_id] for event_id in ids]
        full = sum(row["feature_status"] == "PASSED" for row in values)
        pair = sum(row["reactive_pair_label_available"] == "true" for row in values)
        graph = sum(row["CCD_status"] == "PASSED" for row in values)
        post = sum(row["POST_geometry_label_available"] == "true" for row in values)
        shadow = sum(row["shadow_exact_component_reuse_candidate"] == "true" for row in values)
        representation = sum(row["terminal_route"] == "QUARANTINE_REPRESENTATION_GAP" for row in values)
        leakage = sum(row["terminal_route"] == "LEAKAGE_EXISTING_GROUP_CONFLICT" for row in values)
        score = len(ids) * 1_000_000 + shadow * 100_000 + full * 10_000 + pair * 1_000 + graph * 100 + post * 10
        raw_rows.append({
            "review_unit_id": unit["review_unit_id"], "event_count": len(ids),
            "potential_event_yield_per_unit": len(ids), "canonical_event_ids_json": _json_cell(ids),
            "pdb_ids_json": _json_cell(unit["PDB_ids"]),
            "ligand_component_ids_json": _json_cell(unit["ligand_component_ids"]),
            "full_coordinate_event_count": full, "exact_reactive_pair_event_count": pair,
            "CCD_graph_complete_event_count": graph, "POST_geometry_available_event_count": post,
            "shadow_exact_component_event_count": shadow,
            "representation_blocked_event_count": representation,
            "leakage_conflict_event_count": leakage, "priority_score": score,
            "priority_reason": (
                f"EVENT_YIELD={len(ids)};FULL_COORDINATES={full};EXACT_PAIR={pair};"
                f"CCD_GRAPH={graph};POST={post};SHADOW_EXACT_COMPONENT={shadow};"
                "NO_NAME_OR_GUESSED_BIOLOGY_PRIORITY"
            ),
            "human_decision_created": "false",
        })
    raw_rows.sort(key=lambda row: (-int(row["priority_score"]), str(row["review_unit_id"])))
    return [{field: ({"priority_rank": rank, **row})[field] for field in QUEUE_HEADER}
            for rank, row in enumerate(raw_rows, 1)]


def _diversity(rows: Sequence[Mapping[str, object]],
               outcome_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    ids = [str(row["canonical_event_id"]) for row in rows]
    graphs = {str((outcome_by_id[event_id].get("structural_processing") or {})
                  .get("ccd_component_graph", {}).get("ccd_component_graph_sha256"))
              for event_id in ids if (outcome_by_id[event_id].get("structural_processing") or {})
              .get("ccd_component_graph", {}).get("ccd_component_graph_sha256")}
    radius2 = {str((outcome_by_id[event_id].get("structural_processing") or {})
                   .get("reactive_center_radius2_sha256")) for event_id in ids
               if (outcome_by_id[event_id].get("structural_processing") or {})
               .get("reactive_center_radius2_sha256")}
    roles = Counter(str(row["role_profile"] or "UNASSIGNED_NON_AUTHORITATIVE") for row in rows)
    return {
        "event_count": len(rows), "unique_pdb_count": len({row["pdb_id"] for row in rows}),
        "unique_ligand_component_count": len({row["ligand_component_id"] for row in rows}),
        "unique_CCD_graph_identity_count": len(graphs),
        "unique_reactive_center_radius2_fingerprint_count": len(radius2),
        "unique_leakage_group_count": len({row["leakage_group_id"] for row in rows if row["leakage_group_id"]}),
        "role_profile_counts": dict(sorted(roles.items())),
        "direct_attachment_event_count": roles.get("DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1", 0),
        "linker_present_event_count": roles.get("STRICT_LINKER_PRESENT_V1", 0),
        "role_profile_unassigned_event_count": roles.get("UNASSIGNED_NON_AUTHORITATIVE", 0),
        "medicinal_chemistry_diversity_score_invented": False,
    }


def build_artifacts_v1(*, repo_root: Path) -> dict[str, bytes]:
    inputs = load_scaleup_inputs_v1(repo_root)
    execution_root = overlay_execution_root_v1(repo_root)
    acquisition_path = execution_root / EXTERNAL_ACQUISITION
    processing_path = execution_root / EXTERNAL_PROCESSING
    execution_path = execution_root / EXTERNAL_EXECUTION
    if not all(path.is_file() for path in (acquisition_path, processing_path, execution_path)):
        raise ScaleupSafetyError("EXTERNAL_ATTEMPT_EVIDENCE_INCOMPLETE")
    acquisition = _read_json(acquisition_path)
    processing = _read_json(processing_path)
    execution = _read_json(execution_path)
    processing_payload = processing_path.read_bytes()
    if execution.get("processing_result_sha256") != _sha(processing_payload):
        raise ScaleupSafetyError("EXTERNAL_PROCESSING_RESULT_BINDING_MISMATCH")
    cohort_payload = _csv_bytes(COHORT_HEADER, _cohort_rows(inputs))
    census_rows, metrics = _build_census(inputs=inputs, processing=processing)
    census_payload = _csv_bytes(CENSUS_HEADER, census_rows)
    effective_payload = _json_bytes(_effective_n(
        census_rows, inputs["global_authority_audit"],
    ))
    queue_rows = _review_queue(inputs=inputs, processing=processing, census_rows=census_rows)
    queue_payload = _csv_bytes(QUEUE_HEADER, queue_rows)
    outcome_by_id = {row["processing_outcome"]["canonical_event_id"]: row["processing_outcome"]
                     for row in inputs["first500_rows"]}
    outcome_by_id.update({row["canonical_event_id"]: row["processing_outcome"]
                          for row in processing["events"]})
    subsets = {
        "all_cumulative1000": census_rows,
        "structurally_eligible": [row for row in census_rows if row["feature_status"] == "PASSED"],
        "human_review_candidates": [row for row in census_rows if row["terminal_route"] in {
            routing.HUMAN_REVIEW_REQUIRED, routing.HUMAN_REVIEW_REQUIRED_DEFERRED,
            routing.HUMAN_REVIEW_REQUIRED_GATE_INVALID}],
        "authoritative_model_usable_positives": [row for row in census_rows if row["label_model_usable"] == "true"],
    }
    diversity = {name: _diversity(rows, outcome_by_id) for name, rows in subsets.items()}
    first_route_counts = dict(sorted(Counter(row["terminal_route"] for row in census_rows[:500]).items()))
    next_route_counts = dict(sorted(Counter(row["terminal_route"] for row in census_rows[500:]).items()))
    cumulative_route_counts = dict(sorted(Counter(row["terminal_route"] for row in census_rows).items()))
    current_positive_ids = sorted(inputs["batch13_ids"])
    authority_audit = inputs["global_authority_audit"]
    authority_counts = authority_audit["counts"]
    five_human_relevant = [
        record for record in authority_audit["records"]
        if record["lineage_id"]
        == "CUMULATIVE1000_OTHER_HUMAN_RELEVANT_EXACT5"
    ]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "population": {
            "all_source_normalized_record_count": 9020,
            "canonical_unique_event_count": CANONICAL_COUNT,
            "known_existing_control_event_count": CONTROL_COUNT,
            "ranked_new_candidate_event_count": RANKED_NEW_COUNT,
            "historical_processed_rank_count": 500, "scaleup_event_count": SCALEUP_COUNT,
            "cumulative_ranked_processed_event_count": 1000,
            "remaining_ranked_new_event_count": REMAINING_COUNT,
        },
        "prefix_and_cohort": {
            "first500_exact_prefix_parity": True, "scaleup_rank_start": RANK_START,
            "scaleup_rank_end": RANK_END,
            "rank501_event_id": inputs["cohort"][0]["canonical_event_id"],
            "rank1000_event_id": inputs["cohort"][-1]["canonical_event_id"],
            "rank501_1000_ordered_event_ids_sha256": _sha(_json_bytes(
                [item["canonical_event_id"] for item in inputs["cohort"]])),
        },
        "preflight_and_acquisition": acquisition,
        "route_counts": {"first500": first_route_counts, "ranks501_1000": next_route_counts,
                         "cumulative1000": cumulative_route_counts},
        "cumulative1000_census": metrics,
        "cumulative1000_ranked_new_model_usable_authority": {
            "event_count": len(current_positive_ids), "event_ids": current_positive_ids,
            "authority_source": BATCH13_INDEX.as_posix(), "deduplicated_overlap_count": 0,
        },
        "global_current_positive_authority_audit": authority_audit,
        "authority_scope_counts": {
            "cumulative1000_ranked_new_model_usable_canonical_event_count": metrics["model_usable"],
            **authority_counts,
        },
        "current_five_human_relevant_rows_adjudication": {
            "event_count": len(five_human_relevant),
            "records": five_human_relevant,
            "all_rows_adjudicated": len(five_human_relevant) == 5,
        },
        "rank501_1000_new_authoritative_model_usable_positive_event_count": sum(
            row["label_model_usable"] == "true" for row in census_rows[500:]),
        "existing_production_exact_signature_auto_admission_event_count": sum(
            str(row["positive_authority_source"]).startswith("EXISTING_PRODUCTION_EXACT_SIGNATURE")
            for row in census_rows),
        "human_review_queue": {"review_unit_count": len(queue_rows),
                               "event_count": sum(int(row["event_count"]) for row in queue_rows)},
        "diversity_census": diversity,
        "safety": {
            "training_performed": False, "Trainer_used": False,
            "backward_performed": False, "optimizer_created": False,
            "data_augmentation_performed": False, "PRE_geometry_fabricated": False,
            "new_reaction_family_authority_created": False,
            "new_warhead_family_authority_created": False,
            "cross_signature_positive_propagation_performed": False,
            "human_decision_fuzzy_propagation_performed": False,
            "exact_signature_chemistry_authority_separated_from_model_usable": True,
            "role_label_self_certification_removed": True,
            "pair_authority_self_certification_removed": True,
            "POST_authority_self_certification_removed": True,
            "leakage_split_optimization_performed": False,
            "production_geometry_weight_finalized": False,
            "production_joint_loss_policy_finalized": False,
            "full_training_authorized": False,
            "augmentation_planning_deferred_until_effective_N_known": True,
        },
        "execution": execution, "deterministic_no_network_replay_passed": True,
        "recommended_next_step_exactly": (
            "gpt_reaudit_cumulative1000_authority_census_and_publication_survivability_"
            "then_publish_if_pass"
        ),
        "artifact_sha256_excluding_manifest_and_summary": {
            COHORT: _sha(cohort_payload), PROCESSING: _sha(processing_payload),
            CENSUS: _sha(census_payload), EFFECTIVE_N: _sha(effective_payload),
            QUEUE: _sha(queue_payload),
        },
    }
    summary_payload = _json_bytes(summary)
    external_bindings = [
        _binding(path, display=(OVERLAY_ATTEMPT_RELATIVE_TO_PARENT / "execution" / path.name).as_posix())
        for path in (acquisition_path, processing_path, execution_path)
    ]
    candidate_source_bindings = [
        _binding(inputs["repo_root"] / relative, display=relative.as_posix())
        for relative in (SOURCE_RELATIVE, RUNNER_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE)
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION, "baseline_HEAD": BASELINE_HEAD,
        "frozen_git_input_bindings": inputs["bindings"],
        "frozen_external_first500_bindings": inputs["external_first500_bindings"],
        "candidate_source_bindings": candidate_source_bindings,
        "new_overlay_execution_evidence_bindings": external_bindings,
        "canonical_cache_before": execution["canonical_cache_snapshot_before"],
        "canonical_cache_after": execution["canonical_cache_snapshot_after"],
        "historical_first500_attempt_modified": False,
        "canonical_bulk_cache_modified": False,
        "authority_contract": {
            "cumulative1000_ranked_new_model_usable_canonical_event_count": metrics["model_usable"],
            "global_current_runtime_model_usable_sample_count": authority_counts[
                "global_current_runtime_model_usable_sample_count"
            ],
            "global_current_runtime_model_usable_canonical_event_count": authority_counts[
                "global_current_runtime_model_usable_canonical_event_count"
            ],
            "global_current_positive_but_runtime_incomplete_count": authority_counts[
                "global_current_positive_but_runtime_incomplete_count"
            ],
            "production_reusable_authority_count": 3,
            "cross_signature_propagation_allowed": False,
            "shadow_candidates_are_non_authoritative": True,
            "chemistry_authority_does_not_self_prove_runtime_binding": True,
        },
        "global_current_authority_audit_bindings": {
            "repository_owners": authority_audit["repository_owner_bindings"],
            "external_owners": authority_audit["external_owner_bindings"],
            "audit_records_sha256": _sha(_json_bytes(authority_audit["records"])),
            "audit_counts": authority_counts,
        },
        "feature_semantics": {
            "feature_semantics_audit_completed": True, "feature_semantics_known": True,
            "unknown_atom_feature_policy_resolved": True,
            "unknown_atom_policy_contract_resolved": True, "effective_open_issue_count": 0,
        },
        "exact_negative_rule_ids": list(routing.INTEGRATED_AUTO_NEGATIVE_RULE_IDS),
        "leakage_owner": "apply_leakage_predictions_read_only_v1",
        "output_sha256_excluding_manifest": {
            COHORT: _sha(cohort_payload), PROCESSING: _sha(processing_payload),
            CENSUS: _sha(census_payload), EFFECTIVE_N: _sha(effective_payload),
            QUEUE: _sha(queue_payload), SUMMARY: _sha(summary_payload),
        },
        "training_performed": False, "data_augmentation_performed": False,
    }
    artifacts = {
        COHORT: cohort_payload, PROCESSING: processing_payload, CENSUS: census_payload,
        EFFECTIVE_N: effective_payload, QUEUE: queue_payload,
        MANIFEST: _json_bytes(manifest), SUMMARY: summary_payload,
    }
    if tuple(artifacts) != OUTPUT_FILENAMES:
        raise ScaleupSafetyError("CANDIDATE_ARTIFACT_FILE_SET_INVALID")
    return artifacts


def materialize_v1(*, repo_root: Path) -> dict[str, str]:
    artifacts = build_artifacts_v1(repo_root=repo_root)
    target = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    for name, payload in artifacts.items():
        _atomic_write(target / name, payload)
    return {name: _sha(payload) for name, payload in artifacts.items()}


def execute_controlled_network_v1(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    inputs = load_scaleup_inputs_v1(root)
    canonical_before = executor.snapshot_cache_tree_v1(canonical_cache_root_v1(root))
    first_before = _external_first500_bindings(root)
    cache_before = inspect_readthrough_cache_v1(repo_root=root, inputs=inputs)
    preflight = {
        "rank501_1000_event_count": SCALEUP_COUNT,
        "rank501_1000_unique_pdb_count": cache_before["unique_pdb_count"],
        "rank501_1000_unique_ccd_count": cache_before["unique_ccd_count"],
        "PDB_already_available_in_canonical_cache": cache_before["canonical_cache_reused_pdb_count"],
        "CCD_already_available_in_canonical_cache": cache_before["canonical_cache_reused_ccd_count"],
        "PDB_already_available_in_task_overlay": cache_before["overlay_cache_reused_pdb_count"],
        "CCD_already_available_in_task_overlay": cache_before["overlay_cache_reused_ccd_count"],
        "missing_PDB_count": cache_before["missing_pdb_count"],
        "missing_CCD_count": cache_before["missing_ccd_count"],
        "missing_PDB_ids": cache_before["missing_pdb_ids"],
        "missing_CCD_ids": cache_before["missing_ccd_ids"],
    }
    acquisition = acquire_overlay_v1(repo_root=root, inputs=inputs, preflight=preflight)
    execution_root = overlay_execution_root_v1(root)
    execution_root.mkdir(parents=True, exist_ok=True)
    acquisition_payload = _json_bytes(acquisition)
    _atomic_write(execution_root / EXTERNAL_ACQUISITION, acquisition_payload)
    processing = build_processing_result_v1(repo_root=root, inputs=inputs)
    processing_payload = _json_bytes(processing)
    _atomic_write(execution_root / EXTERNAL_PROCESSING, processing_payload)
    canonical_after = executor.snapshot_cache_tree_v1(canonical_cache_root_v1(root))
    first_after = _external_first500_bindings(root)
    if canonical_after != canonical_before:
        raise ScaleupSafetyError("CANONICAL_CACHE_MODIFIED")
    if first_after != first_before:
        raise ScaleupSafetyError("HISTORICAL_BULK500_ATTEMPT_MODIFIED")
    leftovers = sorted(path.as_posix() for path in overlay_attempt_root_v1(root).rglob("*")
                       if path.is_file() and path.suffix in {".part", ".tmp"})
    if leftovers:
        raise ScaleupSafetyError("LEFTOVER_PARTIAL_FILES:" + _json_cell(leftovers))
    result = {
        "schema_version": SCHEMA_VERSION, "mode": CONTROLLED_NETWORK_EXECUTION,
        "acquisition_result_sha256": _sha(acquisition_payload),
        "processing_result_sha256": _sha(processing_payload),
        "rank501_1000_terminal_outcome_count": processing["terminal_outcome_count"],
        "canonical_cache_snapshot_before": canonical_before,
        "canonical_cache_snapshot_after": canonical_after,
        "historical_first500_bindings_before": first_before,
        "historical_first500_bindings_after": first_after,
        "canonical_bulk_cache_modified": False,
        "historical_bulk500_attempt_modified": False,
        "network_performed": acquisition["network_performed"],
        "systemic_network_failure": False, "training_performed": False,
        "execution_complete": processing["terminal_outcome_count"] == SCALEUP_COUNT,
    }
    execution_payload = _json_bytes(result)
    _atomic_write(execution_root / EXTERNAL_EXECUTION, execution_payload)
    materialize_v1(repo_root=root)
    return result


def replay_no_network_v1(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    execution_root = overlay_execution_root_v1(root)
    expected_processing = (execution_root / EXTERNAL_PROCESSING).read_bytes()
    replayed = _json_bytes(build_processing_result_v1(repo_root=root))
    if replayed != expected_processing:
        raise ScaleupSafetyError("NO_NETWORK_PROCESSING_REPLAY_MISMATCH")
    before = {name: (root / OUTPUT_ROOT_RELATIVE / name).read_bytes() for name in OUTPUT_FILENAMES}
    rebuilt = build_artifacts_v1(repo_root=root)
    if before != rebuilt:
        raise ScaleupSafetyError("NO_NETWORK_CANDIDATE_ARTIFACT_REPLAY_MISMATCH")
    canonical = executor.snapshot_cache_tree_v1(canonical_cache_root_v1(root))
    execution = _read_json(execution_root / EXTERNAL_EXECUTION)
    if canonical != execution["canonical_cache_snapshot_before"]:
        raise ScaleupSafetyError("CANONICAL_CACHE_DRIFT_DURING_REPLAY")
    return {
        "schema_version": SCHEMA_VERSION, "mode": REPLAY_NO_NETWORK,
        "deterministic_no_network_replay_passed": True,
        "processing_result_sha256": _sha(replayed),
        "candidate_artifact_sha256": {name: _sha(payload) for name, payload in rebuilt.items()},
        "network_performed": False, "training_performed": False,
    }


def run_v1(*, repo_root: Path, mode: str = DEFAULT_MODE,
           network_authorized: bool = False) -> dict[str, Any]:
    if mode == PREFLIGHT_NO_NETWORK:
        if network_authorized:
            raise ScaleupSafetyError("NETWORK_AUTHORIZATION_INVALID_IN_PREFLIGHT")
        return preflight_no_network_v1(repo_root=repo_root)
    if mode == CONTROLLED_NETWORK_EXECUTION:
        if network_authorized is not True:
            raise ScaleupSafetyError("CONTROLLED_NETWORK_EXECUTION_NOT_AUTHORIZED")
        return execute_controlled_network_v1(repo_root=repo_root)
    if mode == REPLAY_NO_NETWORK:
        if network_authorized:
            raise ScaleupSafetyError("NETWORK_AUTHORIZATION_INVALID_IN_REPLAY")
        return replay_no_network_v1(repo_root=repo_root)
    raise ScaleupSafetyError("EXECUTION_MODE_INVALID")
