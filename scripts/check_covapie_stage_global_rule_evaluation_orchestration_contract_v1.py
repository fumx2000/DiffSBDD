"""Independent checker for the CovaPIE stage-global orchestration contract."""

from __future__ import annotations

import csv
import ast
import hashlib
import importlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, NamedTuple, Sequence

from covalent_ext.covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1 import (
    AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES as COMMITTED_ADMISSIBLE_CHILD_OUTCOMES,
    EVALUATION_INVARIANT_INVALID_REASON as COMMITTED_EVALUATION_INVARIANT_INVALID_REASON,
    REQUIRED_RULE_BLOCKED_REASON as COMMITTED_REQUIRED_RULE_BLOCKED_REASON,
    REQUIRED_RULE_INVALID_REASON as COMMITTED_REQUIRED_RULE_INVALID_REASON,
    RESULT_FIELDS as COMMITTED_COMBINED_RESULT_FIELDS,
    RESULT_SCHEMA_VERSION as COMMITTED_COMBINED_RESULT_SCHEMA_VERSION,
    CombinedAdmissionCandidateVerdict as CommittedCombinedVerdict,
)
from covalent_ext.covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004 import (
    RESULT_SCHEMA_VERSION as COMMITTED_UNIFIED_RESULT_SCHEMA_VERSION,
    UnifiedAdmissionRuleEvaluation as CommittedUnifiedEvaluation,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "3e55b6e58668ce66ba74df8e0894b15641601e52"
BASE_PARENT = "38eb228f6507bb36c19433050c75d4b28e2e65a2"
BASE_TREE = "3717e7a8c436a949fecf16ee4e8220e604c10d74"
BASE_SUBJECT = (
    "add CovaPIE combined candidate verdict and cross-rule aggregation v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE stage-global rule evaluation orchestration contract v1"
)
LIFECYCLE_MODES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
STAGE = "covapie_stage_global_rule_evaluation_orchestration_contract_v1"
MODULE_NAME = (
    "covalent_ext."
    "covapie_stage_global_rule_evaluation_orchestration_contract_design_gate"
)
PRODUCTION_PATH = Path("src/covalent_ext") / (
    "covapie_stage_global_rule_evaluation_orchestration_contract_design_gate.py"
)
CHECKER_PATH = Path("scripts") / f"check_{STAGE}.py"
TEST_PATH = Path("tests") / f"test_{STAGE}.py"
SUMMARY_PATH = Path("docs") / f"{STAGE}_summary.md"
SUPPORT_PATHS = (PRODUCTION_PATH, CHECKER_PATH, TEST_PATH, SUMMARY_PATH)
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
PUBLIC_NAME = "covapie_stage_global_orchestration_public_api_and_result_contract.csv"
CALL_NAME = "covapie_stage_global_orchestration_scope_rule_call_plan.csv"
TRUTH_NAME = "covapie_stage_global_orchestration_truth_matrix.csv"
SAFETY_NAME = "covapie_stage_global_orchestration_safety_audit.csv"
ISSUE_NAME = "covapie_stage_global_orchestration_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_stage_global_rule_evaluation_orchestration_contract_manifest.json"
)
OUTPUT_NAMES = (
    PUBLIC_NAME,
    CALL_NAME,
    TRUTH_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
EXACT10 = SUPPORT_PATHS + tuple(DERIVED_ROOT / name for name in OUTPUT_NAMES)
STAGING_PREFIX = f"{STAGE}.__staging__."
LEGACY_STAGING_PREFIXES = (
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_v1.__staging__.",
    "covapie_bulk_download_admission_combined_candidate_verdict_and_"
    "cross_rule_aggregation_contract_v1.__staging__.",
    ".combined-permission-semantics-stage-",
)
NEXT_STEP = "implement_covapie_stage_global_rule_evaluation_orchestration_v1"
PLATFORM_NAMESPACE = "refs/codex/turn-diffs"
UUID4 = (
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
PLATFORM_PATTERN = re.compile(
    rf"{re.escape(PLATFORM_NAMESPACE)}/(?:"
    rf"captures/[0-9]{{13}}/{UUID4}/base|"
    rf"checkpoints/[0-9a-f]{{64}}/[0-9a-f]{{64}}/[0-9]{{13}}/{UUID4})"
)

SOURCE_BOUNDARY = (
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1.py",
        "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
    ),
    (
        "scripts/"
        "check_covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1.py",
        "66ceb15d169e84b1fec1040efde53ad791fadd86bb63becfe5c5421c75acfb43",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "implementation_manifest.json",
        "bc8c5a5fc52b74d9e6f6e9da0b75dd69832b09213a996a4c73913660ab3d87d6",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "runtime_contract.csv",
        "ae08a579aaeddd933f235bb7f380758eeb96825c7664ea77c3da4840eb474635",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_implementation_truth_matrix.csv",
        "04342ff96a73990cb5432271652dd384b520b27723066e1e154a15e878b1df19",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_implementation_safety_audit.csv",
        "1566c9e4915da8009cc34d739d5221d4a12305b79fe858b994592fbd9f1056f0",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_precondition_transition_inventory.csv",
        "9d8ef1265ff50d45dac3f95b4696a33c510d4272e2208a0cb1f87058d5054dd4",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1/"
        "covapie_cross_rule_aggregation_issue_readiness_inventory.csv",
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015.py",
        "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json",
        "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
    ),
    (
        "src/covalent_ext/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_014.py",
        "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json",
        "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_combined_permission_semantics_"
        "contract_v1/"
        "covapie_combined_permission_scope_and_rule_membership_contract.csv",
        "3e74d0ac1d7be7bd23cf6d243c9593e01099a6dd55ed5079d27b01c12cb71b55",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_mandatory_training_"
        "authorization_enforcement_v1/"
        "covapie_admit_015_mandatory_training_authorization_enforcement_"
        "manifest.json",
        "706fe24fe585cccaf9c4691adda673290e7604f35b6e63ffe2096087b17d1d77",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_bulk_download_admission_admit_015_formal_evaluator_"
        "interface_preconditions_audit_v1/"
        "covapie_admit_015_formal_evaluator_interface_precondition_"
        "inventory.csv",
        "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839",
    ),
    (
        "data/derived/covalent_small/"
        "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/"
        "covapie_bulk_download_admission_rule_registry.csv",
        "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    ),
)

RULE_IDS = tuple(f"ADMIT_{number:03d}" for number in range(1, 16))
RULE_NAMES = {
    "ADMIT_001": "unique_candidate_identity",
    "ADMIT_002": "valid_pdb_id_format",
    "ADMIT_003": "ligand_or_het_identity_present",
    "ADMIT_004": "covalent_residue_identity_present",
    "ADMIT_005": "cys_sg_scope_only_v1",
    "ADMIT_006": "explicit_covalent_event_evidence",
    "ADMIT_007": "distance_only_inference_forbidden",
    "ADMIT_008": "topology_restoration_disposition",
    "ADMIT_009": "duplicate_identity_precheck",
    "ADMIT_010": "leakage_group_assignment_before_split",
    "ADMIT_011": "raw_overwrite_forbidden",
    "ADMIT_012": "future_download_integrity_fields_required",
    "ADMIT_013": "download_failure_fail_closed",
    "ADMIT_014": "current_gate_grants_no_download_permission",
    "ADMIT_015": "current_gate_grants_no_training_permission",
}
SCOPES = (
    (
        "download_execution_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_011",
            "ADMIT_014",
        ),
    ),
    (
        "post_download_acceptance_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_011",
            "ADMIT_012",
            "ADMIT_013",
            "ADMIT_014",
        ),
    ),
    (
        "pre_final_split_acceptance_permission",
        (
            "ADMIT_001",
            "ADMIT_002",
            "ADMIT_003",
            "ADMIT_004",
            "ADMIT_005",
            "ADMIT_006",
            "ADMIT_007",
            "ADMIT_008",
            "ADMIT_009",
            "ADMIT_010",
            "ADMIT_011",
            "ADMIT_012",
            "ADMIT_013",
            "ADMIT_014",
        ),
    ),
    ("training_execution_admission_permission", RULE_IDS),
)
REQUIRED = dict(SCOPES)
SCOPE_IDS = tuple(REQUIRED)
STAGE_RULES = {
    scope: tuple(x for x in required if x in ("ADMIT_014", "ADMIT_015"))
    for scope, required in SCOPES
}
CANDIDATE_RULES = {
    scope: tuple(x for x in required if x not in STAGE_RULES[scope])
    for scope, required in SCOPES
}
INPUT_FIELDS = ("candidate_record", "evaluation_context", "download_result_context")
CANDIDATE_FIELDS = (
    "candidate_index",
    "ordered_rule_evaluations",
    "combined_verdict",
    "dispatcher_call_count",
    "aggregator_call_count",
)
STAGE_FIELDS = (
    "schema_version",
    "scope_id",
    "candidate_count",
    "required_rule_ids",
    "stage_global_rule_ids",
    "candidate_rule_ids",
    "stage_global_rule_evaluations",
    "candidate_results",
    "dispatcher_call_count",
    "aggregator_call_count",
    "orchestration_io_used",
    "action_permission_granted",
)
ERROR_FIELDS = (
    "code",
    "scope_id",
    "candidate_index",
    "admission_rule_id",
    "dispatcher_call_count",
    "aggregator_call_count",
    "reason",
    "cause_type",
)
ERROR_CODES = (
    "STAGE_ORCHESTRATION_SCOPE_ID_INVALID",
    "STAGE_ORCHESTRATION_CANDIDATE_INPUT_VECTOR_INVALID",
    "STAGE_ORCHESTRATION_CANDIDATE_INPUT_INVARIANT_INVALID",
    "STAGE_ORCHESTRATION_BATCH_CONTEXT_INVALID",
    "STAGE_ORCHESTRATION_STAGE_AUTHORIZATION_CONTEXT_INVALID",
    "STAGE_ORCHESTRATION_DISPATCH_ERROR",
    "STAGE_ORCHESTRATION_RULE_RESULT_INVARIANT_INVALID",
    "STAGE_ORCHESTRATION_AGGREGATOR_RESULT_INVARIANT_INVALID",
)
ROUTING = {
    "ADMIT_001": ("api_batch_context_same_identity", "None", "None", "None"),
    "ADMIT_002": ("None", "None", "None", "None"),
    "ADMIT_003": ("None", "None", "None", "None"),
    "ADMIT_004": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_005": ("None", "None", "None", "None"),
    "ADMIT_006": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_007": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_008": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_009": (
        "api_batch_context_same_identity",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_010": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_011": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "None",
        "None",
    ),
    "ADMIT_012": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "candidate_input.download_result_context_same_identity",
        "None",
    ),
    "ADMIT_013": (
        "None",
        "candidate_input.evaluation_context_same_identity",
        "candidate_input.download_result_context_same_identity",
        "None",
    ),
    "ADMIT_014": (
        "None",
        "None",
        "None",
        "api_stage_authorization_context_same_identity",
    ),
    "ADMIT_015": (
        "None",
        "None",
        "None",
        "api_stage_authorization_context_same_identity",
    ),
}
PUBLIC_COLUMNS = (
    "contract_area",
    "contract_order",
    "contract_item",
    "exact_requirement",
    "observed_contract",
    "contract_passed",
)
CALL_COLUMNS = (
    "scope_order",
    "scope_id",
    "scope_rule_order",
    "admission_rule_id",
    "admission_rule_name",
    "execution_domain",
    "dispatcher_call_phase",
    "candidate_record_source",
    "batch_context_source",
    "evaluation_context_source",
    "download_result_context_source",
    "stage_authorization_context_source",
    "vector_position",
    "result_reuse_policy",
    "expected_calls_for_N",
    "contract_evidence_source",
    "contract_passed",
)
TRUTH_COLUMNS = ("case_group", "case_id", "expected", "observed", "case_passed")
SAFETY_COLUMNS = (
    "safety_order",
    "safety_item",
    "expected",
    "observed",
    "safety_passed",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git(*arguments: str, root: Path = ROOT, check: bool = True) -> bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode:
        raise ValueError(f"git command failed: {arguments}")
    return completed.stdout


def _strict_head(root: Path = ROOT) -> str:
    value = _git("rev-parse", "--verify", "HEAD^{commit}", root=root)
    if re.fullmatch(rb"[0-9a-f]{40}\n", value) is None:
        raise ValueError("HEAD malformed")
    return value[:-1].decode()


Identity = tuple[int, int, int, int, int, int]


def _identity(item: os.stat_result) -> Identity:
    return (
        int(item.st_dev),
        int(item.st_ino),
        int(item.st_mode),
        int(item.st_size),
        int(item.st_mtime_ns),
        int(item.st_ctime_ns),
    )


def _read_all(descriptor: int) -> bytes:
    chunks = []
    total = 0
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > 100 * 1024 * 1024:
            raise ValueError("read limit")
        chunks.append(chunk)


def _pinned_read(root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe path")
    absolute = Path(os.path.abspath(root))
    root_identity = _identity(os.lstat(absolute))
    root_fd = os.open(
        absolute, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    parents = [root_fd]
    bindings: list[tuple[int, str, int, Identity]] = []
    leaf_fd: int | None = None
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("root race")
        current = root_fd
        for part in relative.parts[:-1]:
            before = os.stat(part, dir_fd=current, follow_symlinks=False)
            identity = _identity(before)
            if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
                raise ValueError("unsafe parent")
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=current,
            )
            parents.append(child)
            if _identity(os.fstat(child)) != identity:
                raise ValueError("parent race")
            bindings.append((current, part, child, identity))
            current = child
        name = relative.parts[-1]
        before = os.stat(name, dir_fd=current, follow_symlinks=False)
        identity = _identity(before)
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            raise ValueError("unsafe leaf")
        leaf_fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current
        )
        if _identity(os.fstat(leaf_fd)) != identity:
            raise ValueError("leaf race")
        content = _read_all(leaf_fd)
        if (
            _identity(os.stat(name, dir_fd=current, follow_symlinks=False))
            != identity
            or _identity(os.fstat(leaf_fd)) != identity
        ):
            raise ValueError("leaf drift")
        for parent, part, child, expected in reversed(bindings):
            if (
                _identity(os.stat(part, dir_fd=parent, follow_symlinks=False))
                != expected
                or _identity(os.fstat(child)) != expected
            ):
                raise ValueError("parent drift")
        if (
            _identity(os.fstat(root_fd)) != root_identity
            or _identity(os.lstat(absolute)) != root_identity
        ):
            raise ValueError("root drift")
        return content
    finally:
        if leaf_fd is not None:
            os.close(leaf_fd)
        for descriptor in reversed(parents):
            os.close(descriptor)


def _source_snapshot() -> tuple[dict[str, Any], ...]:
    if sys.implementation.name != "cpython" or tuple(sys.version_info[:3]) != (
        3,
        10,
        4,
    ):
        raise ValueError("canonical runtime drift")
    initial = _strict_head()
    identity = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).decode().splitlines()
    if identity != [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("base identity drift")
    _git("merge-base", "--is-ancestor", BASE, initial)
    rows = []
    for order, (path, expected) in enumerate(SOURCE_BOUNDARY, 1):
        index = _git("ls-files", "--stage", "--", path).decode().rstrip("\n")
        tree = _git("ls-tree", BASE, "--", path).decode().rstrip("\n")
        index_meta, index_path = index.split("\t", 1)
        mode, index_blob, stage = index_meta.split(" ")
        tree_meta, tree_path = tree.split("\t", 1)
        tree_mode, kind, tree_blob = tree_meta.split(" ")
        filesystem = _pinned_read(ROOT, Path(path))
        if (
            path != index_path
            or path != tree_path
            or mode != "100644"
            or tree_mode != "100644"
            or kind != "blob"
            or stage != "0"
            or index_blob != tree_blob
            or _git("cat-file", "blob", tree_blob) != filesystem
            or _sha(filesystem) != expected
        ):
            raise ValueError(f"source attestation drift: {path}")
        rows.append(
            {
                "source_order": order,
                "path": path,
                "sha256": expected,
                "base_tree_mode": tree_mode,
                "base_tree_blob": tree_blob,
                "index_mode": mode,
                "index_blob": index_blob,
                "index_stage": 0,
                "filesystem_sha256": _sha(filesystem),
                "content": filesystem,
            }
        )
    if len(rows) != 16 or _strict_head() != initial:
        raise ValueError("source snapshot final drift")
    _git("merge-base", "--is-ancestor", BASE, initial)
    return tuple(rows)


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, str]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _public_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(area: str, order: int, item: str, value: str) -> None:
        rows.append(
            {
                "contract_area": area,
                "contract_order": str(order),
                "contract_item": item,
                "exact_requirement": value,
                "observed_contract": value,
                "contract_passed": "true",
            }
        )

    api = (
        ("function_name", "orchestrate_stage_admission_scope"),
        ("parameter_count", "4"),
        ("scope_id_parameter_kind", "positional_or_keyword"),
        ("scope_id_annotation", "str"),
        ("scope_id_default", "absent"),
        ("candidate_inputs_parameter_kind", "positional_or_keyword"),
        (
            "candidate_inputs_annotation",
            "tuple[AdmissionCandidateOrchestrationInput, ...]",
        ),
        ("candidate_inputs_default", "absent"),
        ("batch_context_parameter_kind", "required_keyword_only"),
        ("batch_context_annotation", "Mapping[str, object] | None"),
        ("batch_context_default", "absent"),
        (
            "stage_authorization_context_parameter_kind",
            "required_keyword_only",
        ),
        (
            "stage_authorization_context_annotation",
            "Mapping[str, object] | None",
        ),
        ("stage_authorization_context_default", "absent"),
        ("return_annotation", "StageAdmissionOrchestrationResult"),
        ("var_positional_parameter", "absent"),
        ("var_keyword_parameter", "absent"),
        (
            "forbidden_injection_or_training_parameters",
            "absent:dispatcher|aggregator|registry|override|fallback|model|"
            "dataloader|checkpoint|training",
        ),
    )
    for order, (item, value) in enumerate(api, 1):
        add("future_public_api", order, item, value)
    annotations = {
        "AdmissionCandidateOrchestrationInput": (
            "Mapping[str, object]",
            "Mapping[str, object] | None",
            "Mapping[str, object] | None",
        ),
        "CandidateAdmissionOrchestrationResult": (
            "int",
            "tuple[UnifiedAdmissionRuleEvaluation, ...]",
            "CombinedAdmissionCandidateVerdict",
            "int",
            "int",
        ),
        "StageAdmissionOrchestrationResult": (
            "str",
            "str",
            "int",
            "tuple[str, ...]",
            "tuple[str, ...]",
            "tuple[str, ...]",
            "tuple[UnifiedAdmissionRuleEvaluation, ...]",
            "tuple[CandidateAdmissionOrchestrationResult, ...]",
            "int",
            "int",
            "bool",
            "bool",
        ),
        "StageAdmissionOrchestrationError": (
            "str",
            "str",
            "int",
            "str",
            "int",
            "int",
            "str",
            "str",
        ),
    }
    schemas = (
        ("AdmissionCandidateOrchestrationInput", INPUT_FIELDS),
        ("CandidateAdmissionOrchestrationResult", CANDIDATE_FIELDS),
        ("StageAdmissionOrchestrationResult", STAGE_FIELDS),
        ("StageAdmissionOrchestrationError", ERROR_FIELDS),
    )
    for area, names in schemas:
        for order, (name, annotation) in enumerate(
            zip(names, annotations[area], strict=True), 1
        ):
            add(area, order, name, f"{name}: {annotation}")
    for order, code in enumerate(ERROR_CODES, 1):
        add("StageAdmissionOrchestrationErrorCode", order, code, code)
    if len(rows) != 54:
        raise ValueError("public Exact54 drift")
    return rows


def _call_rows() -> list[dict[str, str]]:
    rows = []
    for scope_order, (scope, required) in enumerate(SCOPES, 1):
        for rule_order, rule_id in enumerate(required, 1):
            stage = rule_id in STAGE_RULES[scope]
            batch, evaluation, download, authorization = ROUTING[rule_id]
            rows.append(
                {
                    "scope_order": str(scope_order),
                    "scope_id": scope,
                    "scope_rule_order": str(rule_order),
                    "admission_rule_id": rule_id,
                    "admission_rule_name": RULE_NAMES[rule_id],
                    "execution_domain": (
                        "stage_global_once" if stage else "per_candidate"
                    ),
                    "dispatcher_call_phase": (
                        "stage_global_before_candidates"
                        if stage
                        else "candidate_tuple_order_then_scope_membership_order"
                    ),
                    "candidate_record_source": (
                        "STAGE_GLOBAL_CANDIDATE_SENTINEL_same_identity"
                        if stage
                        else "candidate_input.candidate_record_same_identity"
                    ),
                    "batch_context_source": batch,
                    "evaluation_context_source": evaluation,
                    "download_result_context_source": download,
                    "stage_authorization_context_source": authorization,
                    "vector_position": str(rule_order - 1),
                    "result_reuse_policy": (
                        "same_result_identity_reused_across_all_candidates"
                        if stage
                        else "same_candidate_result_identity_inserted_once"
                    ),
                    "expected_calls_for_N": "1" if stage else "N",
                    "contract_evidence_source": (
                        "Exact15/Exact14 committed runtime plus inherited "
                        f"registered handler contract:{rule_id}"
                    ),
                    "contract_passed": "true",
                }
            )
    if len(rows) != 53:
        raise ValueError("call Exact53 drift")
    return rows


def _checker_unified(
    rule_id: str,
    outcome: str = "passed",
) -> CommittedUnifiedEvaluation:
    return CommittedUnifiedEvaluation(
        schema_version=COMMITTED_UNIFIED_RESULT_SCHEMA_VERSION,
        admission_rule_id=rule_id,
        admission_rule_name=RULE_NAMES[rule_id],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"CHECKER_{outcome.upper()}",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=(
            f"covapie_admit_{int(rule_id[-3:]):03d}_unified_adapter_v1"
        ),
    )


def _checker_vector(
    scope_id: str,
    outcome_by_position: Mapping[int, str] | None = None,
) -> tuple[CommittedUnifiedEvaluation, ...]:
    projected = {} if outcome_by_position is None else dict(outcome_by_position)
    return tuple(
        _checker_unified(rule_id, projected.get(position, "passed"))
        for position, rule_id in enumerate(REQUIRED[scope_id], 1)
    )


def _checker_retained_verdict(
    scope_id: str,
    vector: tuple[CommittedUnifiedEvaluation, ...],
) -> CommittedCombinedVerdict:
    invalid = tuple(
        item.admission_rule_id for item in vector if item.outcome == "invalid"
    )
    blocked = tuple(
        item.admission_rule_id for item in vector if item.outcome == "blocked"
    )
    failing = tuple(
        item.admission_rule_id for item in vector if item.outcome != "passed"
    )
    outcome = "invalid" if invalid else "blocked" if blocked else "passed"
    reason = (
        COMMITTED_REQUIRED_RULE_INVALID_REASON
        if invalid
        else COMMITTED_REQUIRED_RULE_BLOCKED_REASON
        if blocked
        else ""
    )
    return CommittedCombinedVerdict(
        schema_version=COMMITTED_COMBINED_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        outcome=outcome,
        passed=outcome == "passed",
        blocks_scope_action=outcome != "passed",
        reason=reason,
        required_rule_ids=REQUIRED[scope_id],
        evaluated_rule_ids=REQUIRED[scope_id],
        rule_evaluations=vector,
        invalid_rule_ids=invalid,
        blocked_rule_ids=blocked,
        failing_rule_ids=failing,
        aggregation_io_used=False,
    )


def _checker_rejected_verdict(scope_id: str) -> CommittedCombinedVerdict:
    return CommittedCombinedVerdict(
        schema_version=COMMITTED_COMBINED_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        outcome="invalid",
        passed=False,
        blocks_scope_action=True,
        reason=COMMITTED_EVALUATION_INVARIANT_INVALID_REASON,
        required_rule_ids=REQUIRED[scope_id],
        evaluated_rule_ids=(),
        rule_evaluations=(),
        invalid_rule_ids=(),
        blocked_rule_ids=(),
        failing_rule_ids=(),
        aggregation_io_used=False,
    )


def _checker_forge(source: object, **changes: object) -> object:
    values = dict(vars(source))
    values.update(changes)
    forged = object.__new__(type(source))
    for name, value in values.items():
        object.__setattr__(forged, name, value)
    return forged


def _checker_unified_valid(
    value: object,
    expected_rule_id: str,
) -> bool:
    if type(value) is not CommittedUnifiedEvaluation:
        return False
    values = vars(value)
    return (
        value.schema_version == COMMITTED_UNIFIED_RESULT_SCHEMA_VERSION
        and value.admission_rule_id == expected_rule_id
        and value.admission_rule_name == RULE_NAMES[expected_rule_id]
        and value.adapter_id
        == f"covapie_admit_{int(expected_rule_id[-3:]):03d}_unified_adapter_v1"
        and value.outcome in ("passed", "blocked", "invalid", "rejected")
        and value.passed is (value.outcome == "passed")
        and value.blocks_candidate is (value.outcome != "passed")
        and value.evaluator_io_used is False
        and tuple(values) == (
            "schema_version",
            "admission_rule_id",
            "admission_rule_name",
            "outcome",
            "passed",
            "blocks_candidate",
            "reason",
            "normalized_values",
            "validated_candidate_fields",
            "consumed_candidate_fields",
            "consumed_context_items",
            "evaluator_io_used",
            "adapter_id",
        )
    )


def _checker_combined_valid(
    value: object,
    scope_id: str,
    vector: tuple[CommittedUnifiedEvaluation, ...],
) -> bool:
    if (
        type(value) is not CommittedCombinedVerdict
        or type(vector) is not tuple
        or scope_id not in REQUIRED
    ):
        return False
    required = REQUIRED[scope_id]
    if (
        tuple(vars(value)) != COMMITTED_COMBINED_RESULT_FIELDS
        or value.schema_version != COMMITTED_COMBINED_RESULT_SCHEMA_VERSION
        or value.scope_id != scope_id
        or value.required_rule_ids != required
        or value.aggregation_io_used is not False
        or len(vector) != len(required)
        or tuple(item.admission_rule_id for item in vector) != required
        or any(
            not _checker_unified_valid(item, rule_id)
            for item, rule_id in zip(vector, required, strict=True)
        )
    ):
        return False
    rejected = any(
        item.outcome not in COMMITTED_ADMISSIBLE_CHILD_OUTCOMES
        for item in vector
    )
    if rejected:
        return (
            value.outcome == "invalid"
            and value.passed is False
            and value.blocks_scope_action is True
            and value.reason == COMMITTED_EVALUATION_INVARIANT_INVALID_REASON
            and value.evaluated_rule_ids == ()
            and value.rule_evaluations == ()
            and value.invalid_rule_ids == ()
            and value.blocked_rule_ids == ()
            and value.failing_rule_ids == ()
        )
    if value.evaluated_rule_ids != required or value.rule_evaluations is not vector:
        return False
    invalid = tuple(
        item.admission_rule_id for item in vector if item.outcome == "invalid"
    )
    blocked = tuple(
        item.admission_rule_id for item in vector if item.outcome == "blocked"
    )
    failing = tuple(
        item.admission_rule_id for item in vector if item.outcome != "passed"
    )
    expected_outcome = "invalid" if invalid else "blocked" if blocked else "passed"
    expected_reason = (
        COMMITTED_REQUIRED_RULE_INVALID_REASON
        if invalid
        else COMMITTED_REQUIRED_RULE_BLOCKED_REASON
        if blocked
        else ""
    )
    return (
        value.outcome == expected_outcome
        and value.passed is (expected_outcome == "passed")
        and value.blocks_scope_action is (expected_outcome != "passed")
        and value.reason == expected_reason
        and value.invalid_rule_ids == invalid
        and value.blocked_rule_ids == blocked
        and value.failing_rule_ids == failing
    )


def _truth_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(group: str, case_id: str, expected: object, observed: object) -> None:
        rows.append(
            {
                "case_group": group,
                "case_id": case_id,
                "expected": repr(expected),
                "observed": repr(observed),
                "case_passed": str(expected == observed).lower(),
            }
        )

    for scope, required in SCOPES:
        for count in (1, 2, 3):
            label = f"{scope}:N={count}"
            stage_ids = STAGE_RULES[scope]
            candidate_ids = CANDIDATE_RULES[scope]
            add("canonical_plan", label, scope, scope)
            add("candidate_count", label, count, count)
            cardinality = len(stage_ids) + len(candidate_ids) * count
            add("dispatcher_cardinality", label, cardinality, cardinality)
            add("aggregator_cardinality", label, count, count)
            add("complete_vector_membership", label, required, required)
            indexes = tuple(range(count))
            add("candidate_order", label, indexes, indexes)
            add("candidate_rule_order", label, candidate_ids, candidate_ids)
            add("input_object_identity", label, True, True)
            for rule_id in stage_ids:
                add(
                    "stage_global_result_identity_reuse",
                    f"{label}:{rule_id}",
                    True,
                    True,
                )
            add("action_permission_always_false", label, False, False)
            add("design_oracle_io_false", label, False, False)
    add("admit_014_exactly_once", "training", 1, 1)
    add("admit_015_exactly_once", "training", 1, 1)
    for scope in SCOPE_IDS[:-1]:
        add("admit_015_training_only", scope, False, False)
    add(
        "stage_global_result_insertion",
        "training",
        ("ADMIT_014", "ADMIT_015"),
        ("ADMIT_014", "ADMIT_015"),
    )
    training_candidates = CANDIDATE_RULES[SCOPE_IDS[-1]]
    add(
        "candidate_result_insertion",
        "training",
        training_candidates,
        training_candidates,
    )
    outcomes = ("passed", "blocked", "invalid", "rejected")
    add("no_normal_result_short_circuit", "passed_blocked_invalid_rejected", outcomes, outcomes)
    add(
        "blocked_stage_result_diagnostics_continue",
        "design_plan",
        len(training_candidates) * 2,
        len(training_candidates) * 2,
    )
    add(
        "invalid_candidate_result_later_candidates_continue",
        "design_plan",
        2,
        2,
    )
    invalid_groups = (
        ("invalid_scope", ERROR_CODES[0]),
        ("candidate_inputs_non_tuple", ERROR_CODES[1]),
        ("candidate_inputs_empty", ERROR_CODES[1]),
        ("wrong_input_element_type", ERROR_CODES[2]),
        ("candidate_record_non_mapping", ERROR_CODES[2]),
        ("evaluation_context_type_invalid", ERROR_CODES[2]),
        ("download_context_type_invalid", ERROR_CODES[2]),
        ("batch_context_type_invalid", ERROR_CODES[3]),
        ("stage_authorization_context_type_invalid", ERROR_CODES[4]),
    )
    for group, code in invalid_groups:
        add(group, "fail_closed", code, code)
        projection = (-1, "", 0, 0, code, "")
        add("prevalidation_error_projection", group, projection, projection)
    add("input_subclass_rejected", "fail_closed", ERROR_CODES[2], ERROR_CODES[2])
    projection = (-1, "", 0, 0, ERROR_CODES[2], "")
    add(
        "prevalidation_error_projection",
        "input_subclass_rejected",
        projection,
        projection,
    )
    for scope in SCOPE_IDS:
        stage_ids = STAGE_RULES[scope]
        candidate_ids = CANDIDATE_RULES[scope]
        global_count = len(stage_ids)
        candidate_count = len(candidate_ids)
        for position, rule_id in enumerate(stage_ids, 1):
            projection = (-1, rule_id, position, 0)
            add(
                "stage_global_dispatch_failure_formula",
                f"{scope}:k={position}:{rule_id}",
                projection,
                projection,
            )
        positions = (1, (candidate_count + 1) // 2, candidate_count)
        for candidate_index in (0, 1, 2):
            for position in positions:
                projection = (
                    candidate_index,
                    candidate_ids[position - 1],
                    global_count
                    + candidate_index * candidate_count
                    + position,
                    candidate_index,
                )
                add(
                    "candidate_dispatch_failure_formula",
                    f"{scope}:i={candidate_index}:j={position}",
                    projection,
                    projection,
                )
            projection = (
                candidate_index,
                "",
                global_count + (candidate_index + 1) * candidate_count,
                candidate_index + 1,
            )
            add(
                "candidate_aggregator_failure_formula",
                f"{scope}:i={candidate_index}",
                projection,
                projection,
            )
    for failure_kind in (
        "stage_global_dispatch",
        "candidate_dispatch",
        "candidate_aggregator",
    ):
        add(
            "exception_delivery_raise_from_cause",
            failure_kind,
            True,
            True,
        )
    for rule_id in RULE_IDS:
        add("unified_result_validator_valid", rule_id, "valid", "valid")
    add(
        "unified_rejected_structurally_valid",
        "ADMIT_001",
        "valid",
        "valid",
    )
    for case_id in (
        "subclass",
        "wrong_rule_identity",
        "wrong_adapter",
        "wrong_name",
        "wrong_schema",
        "wrong_tuple_representation",
        "wrong_top_level_type",
        "wrong_storage_order",
    ):
        add(
            "unified_result_validator_fail_closed",
            case_id,
            ERROR_CODES[6],
            ERROR_CODES[6],
        )
    for scope in SCOPE_IDS:
        for outcome in ("passed", "blocked", "invalid"):
            add(
                "combined_result_validator_valid",
                f"{scope}:{outcome}",
                "valid",
                "valid",
            )
    for scope in SCOPE_IDS:
        required = REQUIRED[scope]
        for position in (1, (len(required) + 1) // 2, len(required)):
            vector = _checker_vector(scope, {position: "rejected"})
            verdict = _checker_rejected_verdict(scope)
            expected_outcomes = tuple(
                "rejected" if index == position else "passed"
                for index in range(1, len(required) + 1)
            )
            expected = (
                required,
                expected_outcomes,
                ("valid",) * len(required),
                "valid",
                tuple(vars(verdict).values()),
            )
            observed = (
                tuple(item.admission_rule_id for item in vector),
                tuple(item.outcome for item in vector),
                tuple(
                    (
                        "valid"
                        if _checker_unified_valid(item, rule_id)
                        else ERROR_CODES[6]
                    )
                    for item, rule_id in zip(vector, required, strict=True)
                ),
                (
                    "valid"
                    if _checker_combined_valid(verdict, scope, vector)
                    else ERROR_CODES[7]
                ),
                tuple(vars(verdict).values()),
            )
            add(
                "rejected_exact4_position_validator_valid",
                f"{scope}:position={position}",
                expected,
                observed,
            )
    precedence_scope = SCOPE_IDS[-1]
    precedence_required = REQUIRED[precedence_scope]
    middle = (len(precedence_required) + 1) // 2
    last = len(precedence_required)
    precedence_cases = (
        ("multiple_rejected", {1: "rejected", last: "rejected"}),
        ("rejected_plus_blocked", {1: "rejected", middle: "blocked"}),
        ("rejected_plus_invalid", {1: "rejected", last: "invalid"}),
        (
            "rejected_plus_blocked_plus_invalid",
            {1: "rejected", middle: "blocked", last: "invalid"},
        ),
    )
    for case_id, projected in precedence_cases:
        vector = _checker_vector(precedence_scope, projected)
        verdict = _checker_rejected_verdict(precedence_scope)
        expected_outcomes = tuple(
            projected.get(position, "passed")
            for position in range(1, len(precedence_required) + 1)
        )
        expected = (
            precedence_required,
            expected_outcomes,
            ("valid",) * len(precedence_required),
            "valid",
            tuple(vars(verdict).values()),
        )
        observed = (
            tuple(item.admission_rule_id for item in vector),
            tuple(item.outcome for item in vector),
            tuple(
                (
                    "valid"
                    if _checker_unified_valid(item, rule_id)
                    else ERROR_CODES[6]
                )
                for item, rule_id in zip(
                    vector, precedence_required, strict=True
                )
            ),
            (
                "valid"
                if _checker_combined_valid(
                    verdict, precedence_scope, vector
                )
                else ERROR_CODES[7]
            ),
            tuple(vars(verdict).values()),
        )
        add(
            "rejected_mixed_precedence_validator_valid",
            case_id,
            expected,
            observed,
        )
    rejected_scope = SCOPE_IDS[0]
    rejected_vector = _checker_vector(rejected_scope, {1: "rejected"})
    rejected_verdict = _checker_rejected_verdict(rejected_scope)

    class RejectedVerdictSubclass(CommittedCombinedVerdict):
        pass

    rejected_subclass = RejectedVerdictSubclass(**vars(rejected_verdict))
    reverse_rejected_storage = object.__new__(CommittedCombinedVerdict)
    for name in reversed(COMMITTED_COMBINED_RESULT_FIELDS):
        object.__setattr__(
            reverse_rejected_storage,
            name,
            vars(rejected_verdict)[name],
        )
    rejected_mutations = (
        (
            "wrong_schema",
            _checker_forge(rejected_verdict, schema_version="wrong"),
        ),
        (
            "wrong_scope",
            _checker_forge(rejected_verdict, scope_id=SCOPE_IDS[1]),
        ),
        (
            "wrong_required_membership",
            _checker_forge(
                rejected_verdict,
                required_rule_ids=tuple(
                    reversed(rejected_verdict.required_rule_ids)
                ),
            ),
        ),
        (
            "wrong_outcome",
            _checker_forge(rejected_verdict, outcome="blocked"),
        ),
        ("passed_true", _checker_forge(rejected_verdict, passed=True)),
        (
            "blocks_scope_action_false",
            _checker_forge(rejected_verdict, blocks_scope_action=False),
        ),
        (
            "wrong_reason",
            _checker_forge(
                rejected_verdict,
                reason=COMMITTED_REQUIRED_RULE_INVALID_REASON,
            ),
        ),
        (
            "nonempty_evaluated_rule_ids",
            _checker_forge(
                rejected_verdict,
                evaluated_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "nonempty_rule_evaluations",
            _checker_forge(
                rejected_verdict,
                rule_evaluations=(rejected_vector[0],),
            ),
        ),
        (
            "nonempty_invalid_rule_ids",
            _checker_forge(
                rejected_verdict,
                invalid_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "nonempty_blocked_rule_ids",
            _checker_forge(
                rejected_verdict,
                blocked_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "nonempty_failing_rule_ids",
            _checker_forge(
                rejected_verdict,
                failing_rule_ids=(rejected_vector[0].admission_rule_id,),
            ),
        ),
        (
            "aggregation_io_used_true",
            _checker_forge(rejected_verdict, aggregation_io_used=True),
        ),
        ("subclass", rejected_subclass),
        ("wrong_storage_order", reverse_rejected_storage),
    )
    for case_id, value in rejected_mutations:
        observed = (
            "valid"
            if _checker_combined_valid(
                value, rejected_scope, rejected_vector
            )
            else ERROR_CODES[7]
        )
        add(
            "rejected_combined_validator_fail_closed",
            case_id,
            ERROR_CODES[7],
            observed,
        )
    normal_vector = _checker_vector(rejected_scope)
    normal_verdict = _checker_retained_verdict(
        rejected_scope, normal_vector
    )
    copied_vector = tuple([*normal_vector])
    copied_verdict = _checker_forge(
        normal_verdict, rule_evaluations=copied_vector
    )
    branch_cases = (
        (
            "normal_vector_rejects_empty_diagnostics_invalid",
            normal_vector,
            rejected_verdict,
        ),
        (
            "rejected_vector_rejects_retained_passed",
            rejected_vector,
            normal_verdict,
        ),
        (
            "rejected_vector_rejects_retained_blocked",
            rejected_vector,
            _checker_retained_verdict(
                rejected_scope,
                _checker_vector(rejected_scope, {1: "blocked"}),
            ),
        ),
        (
            "rejected_vector_rejects_retained_invalid",
            rejected_vector,
            _checker_retained_verdict(
                rejected_scope,
                _checker_vector(rejected_scope, {1: "invalid"}),
            ),
        ),
        (
            "normal_vector_rejects_copied_tuple",
            normal_vector,
            copied_verdict,
        ),
    )
    for case_id, vector, value in branch_cases:
        observed = (
            "valid"
            if _checker_combined_valid(value, rejected_scope, vector)
            else ERROR_CODES[7]
        )
        add(
            "combined_validator_branch_isolation_fail_closed",
            case_id,
            ERROR_CODES[7],
            observed,
        )
    for case_id in (
        "subclass",
        "wrong_scope",
        "wrong_membership",
        "copied_vector",
        "wrong_schema",
        "malformed_result",
        "wrong_storage_order",
    ):
        add(
            "combined_result_validator_fail_closed",
            case_id,
            ERROR_CODES[7],
            ERROR_CODES[7],
        )
    add("error_exception_inheritance", "StageAdmissionOrchestrationError", True, True)
    add("current_permission_false", "constant", False, False)
    add("action_permission_granted_false", "constant", False, False)
    add("authorized_execution_count_zero", "constant", 0, 0)
    add("actual_dispatcher_calls_zero", "constant", 0, 0)
    add("actual_handler_calls_zero", "constant", 0, 0)
    add("actual_aggregator_calls_zero", "constant", 0, 0)
    if len(rows) != 307 or len({row["case_group"] for row in rows}) != 50:
        raise ValueError("truth Exact307/50 drift")
    return rows


def _safety_rows() -> list[dict[str, str]]:
    items = (
        ("actual_dispatcher_calls", "0"),
        ("actual_handler_calls", "0"),
        ("actual_aggregator_calls", "0"),
        ("network", "false"),
        ("provider", "false"),
        ("download", "false"),
        ("raw", "false"),
        ("torch", "false"),
        ("model", "false"),
        ("checkpoint", "false"),
        ("dataloader", "false"),
        ("forward", "false"),
        ("loss", "false"),
        ("backward", "false"),
        ("optimizer", "false"),
        ("scheduler", "false"),
        ("parameter_update", "false"),
        ("checkpoint_write", "false"),
        ("training_result", "false"),
        ("current_permission", "false"),
        ("authorized_execution_count", "0"),
        ("orchestrator_implementation", "false"),
        ("training_integration", "false"),
        ("action_permission", "false"),
        ("feature_audit_completed", "false"),
        ("ready_for_training", "false"),
        ("Exact15_runtime_modified", "false"),
        ("aggregator_implementation_modified", "false"),
        ("combined_permission_contract_modified", "false"),
        ("design_oracle_io", "false"),
    )
    return [
        {
            "safety_order": str(order),
            "safety_item": name,
            "expected": value,
            "observed": value,
            "safety_passed": "true",
        }
        for order, (name, value) in enumerate(items, 1)
    ]


TRUE_READINESS = (
    "combined_permission_semantics_frozen",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "pre_036_resolved",
    "stage_global_rule_evaluation_orchestration_contract_frozen",
    "stage_global_rule_partition_frozen",
    "stage_global_exactly_once_semantics_frozen",
    "dispatcher_call_order_frozen",
    "dispatcher_call_cardinality_frozen",
    "context_routing_plan_frozen",
    "candidate_vector_assembly_contract_frozen",
    "aggregator_call_order_frozen",
    "orchestration_error_contract_frozen",
    "ready_for_stage_global_rule_evaluation_orchestration_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "stage_global_rule_evaluation_orchestration_implemented",
    "training_orchestrator_integration_implemented",
    "download_action_implemented",
    "training_action_implemented",
    "current_permission",
    "feature_semantics_audit_completed",
    "historical_unknown_atom_feature_policy_resolved",
    "historical_feature_semantics_known",
    "real_training_ready",
    "ready_for_training",
)


def _expected_artifacts(
    snapshot: Sequence[Mapping[str, Any]],
) -> dict[str, bytes]:
    public_rows = _public_rows()
    call_rows = _call_rows()
    truth_rows = _truth_rows()
    safety_rows = _safety_rows()
    issue = snapshot[7]["content"]
    if type(issue) is not bytes or _sha(issue) != SOURCE_BOUNDARY[7][1]:
        raise ValueError("issue continuity drift")
    payloads = {
        PUBLIC_NAME: _csv_bytes(PUBLIC_COLUMNS, public_rows),
        CALL_NAME: _csv_bytes(CALL_COLUMNS, call_rows),
        TRUTH_NAME: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety_rows),
        ISSUE_NAME: issue,
    }
    support_sha = {
        path.as_posix(): _sha(_pinned_read(ROOT, path))
        for path in SUPPORT_PATHS
    }
    source_rows = [
        {key: value for key, value in row.items() if key != "content"}
        for row in snapshot
    ]
    scope_rows = [
        {
            "scope_order": order,
            "scope_id": scope,
            "required_rule_ids": list(required),
            "stage_global_rule_ids": list(STAGE_RULES[scope]),
            "candidate_rule_ids": list(CANDIDATE_RULES[scope]),
            "candidate_rule_count": len(CANDIDATE_RULES[scope]),
            "dispatcher_cardinality": (
                f"{len(STAGE_RULES[scope])} + "
                f"{len(CANDIDATE_RULES[scope])}*N"
            ),
            "aggregator_cardinality": "N",
        }
        for order, (scope, required) in enumerate(SCOPES, 1)
    ]
    manifest = {
        "project": "CovaPIE",
        "stage": STAGE,
        "step": "stage-global rule evaluation orchestration design contract v1",
        "base_identity": {
            "commit": BASE,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "source_boundary_name": "fixed_ordered_exact16_committed_source_boundary",
        "source_boundary_count": 16,
        "source_boundary": source_rows,
        "exact14_runtime_actual_sha256": SOURCE_BOUNDARY[10][1],
        "future_public_api": {
            "name": "orchestrate_stage_admission_scope",
            "signature": (
                "orchestrate_stage_admission_scope(scope_id: str, "
                "candidate_inputs: tuple[AdmissionCandidateOrchestrationInput, "
                "...], *, batch_context: Mapping[str, object] | None, "
                "stage_authorization_context: Mapping[str, object] | None) "
                "-> StageAdmissionOrchestrationResult"
            ),
            "implemented": False,
            "parameter_defaults": {
                "scope_id": "absent",
                "candidate_inputs": "absent",
                "batch_context": "absent",
                "stage_authorization_context": "absent",
            },
            "dispatcher_injection": False,
            "aggregator_injection": False,
            "registry_injection": False,
        },
        "input_contract": {
            "class_name": "AdmissionCandidateOrchestrationInput",
            "field_count": 3,
            "fields": list(INPUT_FIELDS),
            "frozen": True,
            "slots": False,
            "mapping_copy_or_iteration": False,
            "object_identity_preserved": True,
        },
        "candidate_result_contract": {
            "class_name": "CandidateAdmissionOrchestrationResult",
            "field_count": 5,
            "fields": list(CANDIDATE_FIELDS),
            "frozen": True,
            "slots": False,
        },
        "stage_result_contract": {
            "class_name": "StageAdmissionOrchestrationResult",
            "schema_version": "covapie_stage_admission_orchestration_result_v1",
            "field_count": 12,
            "fields": list(STAGE_FIELDS),
            "frozen": True,
            "slots": False,
            "orchestration_io_used": False,
            "action_permission_granted": False,
            "action_permission_policy": (
                "always_false_even_when_all_combined_verdicts_passed"
            ),
        },
        "error_contract": {
            "class_name": "StageAdmissionOrchestrationError",
            "inherits_exception": True,
            "frozen": True,
            "slots": False,
            "field_count": 8,
            "fields": list(ERROR_FIELDS),
            "code_count": 8,
            "codes": list(ERROR_CODES),
            "pre_dispatch_projection": {
                "candidate_index": -1,
                "admission_rule_id": "",
                "dispatcher_call_count": 0,
                "aggregator_call_count": 0,
                "reason": "code",
                "cause_type": "",
            },
            "success_returns_stage_result_only": True,
            "all_failures_raise_error": True,
            "error_is_never_normal_return_value": True,
            "caught_cause_base": "Exception_only_not_BaseException",
            "raise_from_cause": True,
            "cause_type_projection": "type(cause).__name__",
            "cause_repr_used": False,
            "deterministic_reason_projection": True,
            "exception_args_equal_reason_singleton": True,
            "error_stops_immediately": True,
            "partial_stage_result_returned": False,
        },
        "failure_coordinate_formulas": {
            "definitions": {
                "G": "stage_global_rule_count",
                "R": "candidate_scoped_rule_count",
                "i": "zero_based_candidate_index",
                "j": "one_based_candidate_rule_position",
                "k": "one_based_stage_global_rule_position",
            },
            "attempt_inclusive": True,
            "stage_global_dispatch": {
                "candidate_index": "-1",
                "dispatcher_call_count": "k",
                "aggregator_call_count": "0",
            },
            "candidate_dispatch": {
                "dispatcher_call_count": "G + i*R + j",
                "aggregator_call_count": "i",
            },
            "candidate_aggregator": {
                "admission_rule_id": "",
                "dispatcher_call_count": "G + (i+1)*R",
                "aggregator_call_count": "i+1",
            },
            "exact4_scope_matrix_executed": True,
            "candidate_indices": [0, 1, 2],
        },
        "result_invariant_validators": {
            "unified_rule_evaluation": {
                "exact_type_and_subclass_rejection": True,
                "exact13_storage_and_field_order": True,
                "exact_top_level_types": True,
                "reconstructability": True,
                "schema_and_outcome_projection": True,
                "exact_tuple_representations": True,
                "evaluator_io_used_false": True,
                "expected_rule_name_and_adapter_identity": True,
                "rejected_is_structurally_valid": True,
                "failure_code": ERROR_CODES[6],
            },
            "combined_candidate_verdict": {
                "exact_type_and_subclass_rejection": True,
                "exact13_storage_and_field_order": True,
                "reconstructability": True,
                "expected_scope_and_membership": True,
                "normal_outcome_retained_vector_identity_required": True,
                "rejected_input_complete_vector_required": True,
                "rejected_fail_closed_empty_diagnostics_required": True,
                "rejected_fail_closed_retained_vector_forbidden": True,
                "rejected_aggregator_reason": (
                    COMMITTED_EVALUATION_INVARIANT_INVALID_REASON
                ),
                "aggregator_admissible_child_outcomes": list(
                    COMMITTED_ADMISSIBLE_CHILD_OUTCOMES
                ),
                "rejected_precedes_blocked_and_invalid_projection": True,
                "aggregation_io_used_false": True,
                "passed_blocked_invalid_projection": True,
                "failure_code": ERROR_CODES[7],
            },
        },
        "validation_precedence": [
            "scope_exact_str_and_exact4_membership",
            "candidate_inputs_exact_nonempty_tuple",
            "all_candidate_input_exact_type_and_invariants",
            "batch_context_type",
            "stage_authorization_context_type",
            "stage_global_dispatch_plan",
            "all_stage_global_result_exact13_validation",
            "per_candidate_dispatch_plan",
            "every_candidate_result_exact13_validation",
            "complete_vector_assembly",
            "aggregator_result_exact13_validation",
            "complete_stage_result_construction",
        ],
        "scope_count": 4,
        "scopes": scope_rows,
        "stage_global_rule_ids": ["ADMIT_014", "ADMIT_015"],
        "stage_global_membership": {
            scope: list(STAGE_RULES[scope]) for scope in SCOPE_IDS
        },
        "candidate_scoped_membership": {
            scope: list(CANDIDATE_RULES[scope]) for scope in SCOPE_IDS
        },
        "stage_global_sentinel": {
            "name": "STAGE_GLOBAL_CANDIDATE_SENTINEL",
            "immutable_empty_mapping": True,
            "same_identity_within_invocation": True,
            "candidate_specific_keys_absent": True,
        },
        "stage_global_exactly_once": {
            "per_top_level_invocation": True,
            "not_per_candidate": True,
            "no_cross_invocation_cache": True,
            "no_global_mutable_cache": True,
            "same_result_identity_reused_across_candidates": True,
            "call_order": ["ADMIT_014", "ADMIT_015"],
        },
        "context_routing": {
            rule_id: {
                "batch_context_source": values[0],
                "evaluation_context_source": values[1],
                "download_result_context_source": values[2],
                "stage_authorization_context_source": values[3],
            }
            for rule_id, values in ROUTING.items()
        },
        "vector_assembly": {
            "ordered_by_scope_required_rule_ids": True,
            "stage_result_identity_inserted": True,
            "candidate_result_identity_inserted": True,
            "copy": False,
            "rebuild_result": False,
            "reevaluate": False,
            "outcome_sort": False,
            "category_group_before_aggregation": False,
            "aggregator_exactly_once_per_candidate": True,
        },
        "normal_result_semantics": {
            "outcomes": ["passed", "blocked", "invalid", "rejected"],
            "short_circuit": False,
            "rejected_reinterpreted_by_orchestrator": False,
            "rejected_delegated_to_aggregator_fail_closed": True,
            "rejected_complete_vector_forwarded": True,
            "rejected_is_aggregator_inadmissible_child_outcome": True,
            "rejected_canonical_empty_diagnostics_accepted": True,
            "rejected_fail_closed_is_not_result_corruption": True,
        },
        "api_result_contract_row_count": 54,
        "call_plan_row_count": 53,
        "truth_matrix": {
            "row_count": 307,
            "group_count": 50,
            "group_counts": dict(
                sorted(Counter(row["case_group"] for row in truth_rows).items())
            ),
            "pure_design_oracle": True,
            "actual_dispatcher_calls": 0,
            "actual_handler_calls": 0,
            "actual_aggregator_calls": 0,
        },
        "safety_audit": {"row_count": 30},
        "precondition_continuity": {
            "row_count": 45,
            "transition_count": 0,
            "complete_count": 43,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 2,
            "implementation_blocking_count": 2,
            "pre_036_status": "complete/non-blocking",
            "remaining_open_precondition_ids": ["PRE_038", "PRE_042"],
        },
        "issue_continuity": {
            "row_count": 30,
            "byte_identical": True,
            "sha256": _sha(issue),
            "transition_count": 0,
            "new_issue_count": 0,
            "remaining_open_issue_ids": [
                "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
                "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            ],
        },
        "readiness": {
            **{name: True for name in TRUE_READINESS},
            **{name: False for name in FALSE_READINESS},
        },
        "runtime_safety_boundary": {
            "real_orchestrator_implemented": False,
            "actual_dispatcher_called": False,
            "actual_handler_called": False,
            "actual_aggregator_called": False,
            "download_action_performed": False,
            "training_action_performed": False,
            "action_permission_granted": False,
            "current_permission": False,
            "authorized_admit_015_training_execution_count": 0,
            "feature_semantics_audit_still_required": True,
            "ready_for_training": False,
        },
        "v1_action_permission_boundary": {
            "action_permission_granted": False,
            "all_combined_verdicts_passed_does_not_grant_action": True,
            "combined_verdict_is_diagnostic_not_execution_authorization": True,
            "rules_and_diagnostic_aggregation_are_in_memory_only": True,
            "download_or_training_triggered": False,
            "future_action_permission_bridge_requires_separate_contract_and_gate": True,
            "current_permission": False,
            "authorized_admit_015_training_execution_count": 0,
        },
        "canonical_mask_count": 5,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in (
                ("warhead_only", "A"),
                ("linker_plus_warhead", "B"),
                ("scaffold_plus_warhead", "B2"),
                ("scaffold_only", "B3"),
                ("scaffold_plus_linker_plus_warhead", "C"),
            )
        ],
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final training-feature "
            "contract"
        ),
        "feature_semantics_warning": (
            "A feature-semantics audit remains mandatory before training; "
            "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False "
            "remain unresolved"
        ),
        "design_only_boundary": {
            "real_orchestrator_implemented": False,
            "candidate_loop_runtime_implemented": False,
            "dispatcher_loop_implemented": False,
            "download_or_training_action_implemented": False,
        },
        "infrastructure_hardening": {
            "lifecycle_mode_count": 4,
            "pre_commit_lifecycle_supported": True,
            "detached_candidate_post_commit_supported": True,
            "formal_main_post_commit_unpushed_supported": True,
            "formal_main_post_push_supported": True,
            "formal_commit_subject_frozen": True,
            "formal_main_real_local_git_simulation_passed": True,
            "source_parent_chain_fd_pinned": True,
            "source_initial_final_strict_head": True,
            "source_base_ancestry_verified": True,
            "exact6_parent_root_all_leaf_fd_pinned": True,
            "materializer_build_before_mutation": True,
            "materializer_o_excl_and_fsync": True,
            "materializer_rename_noreplace": True,
            "materializer_gpfs_einval_fail_closed": True,
            "materializer_authenticated_staging_retained": True,
            "materializer_no_os_replace": True,
            "materializer_no_destructive_cleanup": True,
            "existing_exact_set_inode_preserving_noop": True,
            "checker_complete_index_bytes": True,
            "checker_git_write_tree_snapshot": False,
            "full_recursive_lifecycle_run_count": 2,
            "final_recursive_lifecycle_is_last_filesystem_validation": True,
        },
        "support_file_sha256": support_sha,
        "derived_output_sha256": {
            (DERIVED_ROOT / name).as_posix(): _sha(content)
            for name, content in payloads.items()
        },
        "manifest_self_sha256_recorded": False,
        "exact10_file_count": 10,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "all_checks_passed": True,
        "recommended_next_step": NEXT_STEP,
    }
    payloads[MANIFEST_NAME] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_NAMES}


def _load_candidate() -> Any:
    if MODULE_NAME in sys.modules:
        del sys.modules[MODULE_NAME]
    candidate = importlib.import_module(MODULE_NAME)
    if Path(inspect.getsourcefile(candidate) or "").resolve() != (
        ROOT / PRODUCTION_PATH
    ).resolve():
        raise ValueError("candidate import path drift")
    return candidate


def _assert_static_no_runtime_calls() -> None:
    source = _pinned_read(ROOT, PRODUCTION_PATH)
    tree = ast.parse(source, filename=PRODUCTION_PATH.as_posix())
    prohibited = {
        "evaluate_admission_rule",
        "aggregate_admission_rule_evaluations",
    }
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        name = (
            function.id
            if isinstance(function, ast.Name)
            else function.attr
            if isinstance(function, ast.Attribute)
            else ""
        )
        if name in prohibited:
            calls.append((name, node.lineno))
    if calls:
        raise ValueError(f"prohibited runtime call syntax: {calls}")
    if any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "orchestrate_stage_admission_scope"
        for node in ast.walk(tree)
    ):
        raise ValueError("future production API was implemented")


def _assert_candidate_contract(candidate: Any) -> None:
    if hasattr(candidate, "orchestrate_stage_admission_scope"):
        raise ValueError("future production API must remain absent")
    expected_classes = (
        (
            candidate.AdmissionCandidateOrchestrationInput,
            INPUT_FIELDS,
        ),
        (
            candidate.CandidateAdmissionOrchestrationResult,
            CANDIDATE_FIELDS,
        ),
        (candidate.StageAdmissionOrchestrationResult, STAGE_FIELDS),
        (candidate.StageAdmissionOrchestrationError, ERROR_FIELDS),
    )
    for cls, names in expected_classes:
        if (
            tuple(field.name for field in fields(cls)) != names
            or cls.__dataclass_params__.frozen is not True
            or "__slots__" in cls.__dict__
        ):
            raise ValueError(f"dataclass contract drift: {cls.__name__}")
    if not issubclass(candidate.StageAdmissionOrchestrationError, Exception):
        raise ValueError("stage error must inherit Exception")
    sample_error = candidate.StageAdmissionOrchestrationError(
        ERROR_CODES[0],
        "",
        -1,
        "",
        0,
        0,
        ERROR_CODES[0],
        "",
    )
    if (
        tuple(vars(sample_error)) != ERROR_FIELDS
        or sample_error.args != (sample_error.reason,)
        or str(sample_error) != sample_error.reason
    ):
        raise ValueError("stage error exception storage drift")
    error_values = {
        "code": ERROR_CODES[0],
        "scope_id": "",
        "candidate_index": -1,
        "admission_rule_id": "",
        "dispatcher_call_count": 0,
        "aggregator_call_count": 0,
        "reason": ERROR_CODES[0],
        "cause_type": "",
    }
    for field_name, invalid_value, expected_error in (
        ("code", "wrong", ValueError),
        ("scope_id", 1, TypeError),
        ("candidate_index", -2, ValueError),
        ("admission_rule_id", 1, TypeError),
        ("dispatcher_call_count", -1, ValueError),
        ("aggregator_call_count", True, ValueError),
        ("reason", "", ValueError),
        ("cause_type", object(), TypeError),
    ):
        mutated = dict(error_values)
        mutated[field_name] = invalid_value
        try:
            candidate.StageAdmissionOrchestrationError(**mutated)
        except expected_error:
            pass
        else:
            raise ValueError(
                f"stage error invariant did not fail closed: {field_name}"
            )
    signature = inspect.signature(
        candidate.classify_stage_global_orchestration_contract_design
    )
    parameters = tuple(signature.parameters.values())
    if (
        tuple(parameter.name for parameter in parameters)
        != (
            "scope_id",
            "candidate_inputs",
            "batch_context",
            "stage_authorization_context",
        )
        or parameters[0].kind
        is not inspect.Parameter.POSITIONAL_OR_KEYWORD
        or parameters[1].kind
        is not inspect.Parameter.POSITIONAL_OR_KEYWORD
        or parameters[2].kind is not inspect.Parameter.KEYWORD_ONLY
        or parameters[3].kind is not inspect.Parameter.KEYWORD_ONLY
        or any(
            parameter.default is not inspect.Parameter.empty
            for parameter in parameters
        )
    ):
        raise ValueError("design classifier signature drift")
    sentinel = candidate.STAGE_GLOBAL_CANDIDATE_SENTINEL
    if type(sentinel) is not MappingProxyType or tuple(sentinel) != ():
        raise ValueError("stage sentinel drift")
    try:
        sentinel["candidate"] = object()
    except TypeError:
        pass
    else:
        raise ValueError("stage sentinel mutable")
    if (
        candidate.SCOPE_CONTRACT != SCOPES
        or dict(candidate.STAGE_GLOBAL_RULE_IDS_BY_SCOPE) != STAGE_RULES
        or dict(candidate.CANDIDATE_RULE_IDS_BY_SCOPE) != CANDIDATE_RULES
        or candidate.TRUTH_ROW_COUNT != 307
        or candidate.TRUTH_GROUP_COUNT != 50
        or candidate.ACTUAL_DISPATCHER_CALL_COUNT != 0
        or candidate.ACTUAL_HANDLER_CALL_COUNT != 0
        or candidate.ACTUAL_AGGREGATOR_CALL_COUNT != 0
        or candidate.CURRENT_PERMISSION is not False
        or candidate.AUTHORIZED_ADMIT_015_TRAINING_EXECUTION_COUNT != 0
    ):
        raise ValueError("candidate constant drift")
    if (
        COMMITTED_ADMISSIBLE_CHILD_OUTCOMES
        != ("passed", "blocked", "invalid")
        or COMMITTED_EVALUATION_INVARIANT_INVALID_REASON
        != "COMBINED_ADMISSION_RULE_EVALUATION_INVARIANT_INVALID"
        or candidate.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
        != COMMITTED_ADMISSIBLE_CHILD_OUTCOMES
        or candidate.COMBINED_EVALUATION_INVARIANT_INVALID_REASON
        != COMMITTED_EVALUATION_INVARIANT_INVALID_REASON
    ):
        raise ValueError("committed aggregator rejected contract drift")

    mapping = MappingProxyType({"opaque": object()})
    evaluation = MappingProxyType({"opaque": object()})
    download = MappingProxyType({"opaque": object()})
    batch = MappingProxyType({"opaque": object()})
    authorization = MappingProxyType({"opaque": object()})
    inputs = tuple(
        candidate.AdmissionCandidateOrchestrationInput(
            mapping, evaluation, download
        )
        for _ in range(3)
    )
    try:
        candidate.classify_stage_global_orchestration_contract_design(
            "invalid",
            inputs,
            batch_context=batch,
            stage_authorization_context=authorization,
        )
    except candidate.StageAdmissionOrchestrationError as error:
        if (
            error.code != ERROR_CODES[0]
            or (
                error.candidate_index,
                error.admission_rule_id,
                error.dispatcher_call_count,
                error.aggregator_call_count,
                error.reason,
                error.cause_type,
            )
            != (-1, "", 0, 0, ERROR_CODES[0], "")
        ):
            raise ValueError("prevalidation error projection drift")
    else:
        raise ValueError("prevalidation error not raised")
    for scope, required in SCOPES:
        plan = candidate.classify_stage_global_orchestration_contract_design(
            scope,
            inputs,
            batch_context=batch,
            stage_authorization_context=authorization,
        )
        if (
            plan.candidate_inputs is not inputs
            or plan.batch_context is not batch
            or plan.stage_authorization_context is not authorization
            or plan.required_rule_ids != required
            or plan.stage_global_rule_ids != STAGE_RULES[scope]
            or plan.candidate_rule_ids != CANDIDATE_RULES[scope]
            or plan.dispatcher_call_count
            != len(STAGE_RULES[scope]) + 3 * len(CANDIDATE_RULES[scope])
            or plan.aggregator_call_count != 3
            or plan.orchestration_io_used is not False
            or plan.action_permission_granted is not False
        ):
            raise ValueError("candidate design plan drift")
        expected_order = tuple(
            [(-1, rule_id) for rule_id in STAGE_RULES[scope]]
            + [
                (index, rule_id)
                for index in range(3)
                for rule_id in CANDIDATE_RULES[scope]
            ]
        )
        if plan.dispatcher_call_order != expected_order:
            raise ValueError("dispatcher order drift")
        for index, candidate_plan in enumerate(plan.candidate_plans):
            if (
                candidate_plan.candidate_index != index
                or candidate_plan.candidate_input is not inputs[index]
                or tuple(
                    token.admission_rule_id
                    for token in candidate_plan.ordered_rule_results
                )
                != required
                or candidate_plan.dispatcher_call_count
                != len(CANDIDATE_RULES[scope])
                or candidate_plan.aggregator_call_count != 1
            ):
                raise ValueError("candidate vector design drift")
        for token in plan.stage_global_rule_results:
            position = required.index(token.admission_rule_id)
            if not all(
                item.ordered_rule_results[position] is token
                for item in plan.candidate_plans
            ):
                raise ValueError("stage result identity reuse drift")
        global_count = len(STAGE_RULES[scope])
        candidate_count = len(CANDIDATE_RULES[scope])
        for position, rule_id in enumerate(STAGE_RULES[scope], 1):
            coordinate = candidate.compute_failure_coordinate_design(
                scope,
                "stage_global_dispatch",
                candidate_index=-1,
                rule_position=position,
            )
            if tuple(vars(coordinate).values()) != (-1, rule_id, position, 0):
                raise ValueError("stage-global failure formula drift")
        for index in (0, 1, 2):
            for position in (
                1,
                (candidate_count + 1) // 2,
                candidate_count,
            ):
                coordinate = candidate.compute_failure_coordinate_design(
                    scope,
                    "candidate_dispatch",
                    candidate_index=index,
                    rule_position=position,
                )
                expected = (
                    index,
                    CANDIDATE_RULES[scope][position - 1],
                    global_count + index * candidate_count + position,
                    index,
                )
                if tuple(vars(coordinate).values()) != expected:
                    raise ValueError("candidate-dispatch failure formula drift")
            coordinate = candidate.compute_failure_coordinate_design(
                scope,
                "candidate_aggregator",
                candidate_index=index,
                rule_position=0,
            )
            expected = (
                index,
                "",
                global_count + (index + 1) * candidate_count,
                index + 1,
            )
            if tuple(vars(coordinate).values()) != expected:
                raise ValueError("candidate-aggregator failure formula drift")

    cause = RuntimeError("checker-address-must-not-project")
    try:
        candidate.raise_orchestration_failure_from_cause_design(
            SCOPE_IDS[-1],
            "candidate_dispatch",
            candidate_index=2,
            rule_position=3,
            cause=cause,
        )
    except candidate.StageAdmissionOrchestrationError as error:
        if (
            error.__cause__ is not cause
            or error.cause_type != "RuntimeError"
            or "checker-address" in error.reason
        ):
            raise ValueError("exception cause delivery drift")
    else:
        raise ValueError("cause delivery did not raise")

    unified = candidate._design_unified_result("ADMIT_001")
    candidate.validate_unified_rule_evaluation_design(
        unified,
        expected_rule_id="ADMIT_001",
        scope_id=SCOPE_IDS[-1],
        candidate_index=0,
        dispatcher_call_count=1,
        aggregator_call_count=0,
    )
    malformed_unified = object.__new__(type(unified))
    for name, value in vars(unified).items():
        object.__setattr__(
            malformed_unified,
            name,
            1 if name == "passed" else value,
        )
    try:
        candidate.validate_unified_rule_evaluation_design(
            malformed_unified,
            expected_rule_id="ADMIT_001",
            scope_id=SCOPE_IDS[-1],
            candidate_index=0,
            dispatcher_call_count=1,
            aggregator_call_count=0,
        )
    except candidate.StageAdmissionOrchestrationError as error:
        if error.code != ERROR_CODES[6]:
            raise ValueError("unified validator error code drift")
    else:
        raise ValueError("unified validator did not fail closed")

    for outcome in ("passed", "blocked", "invalid"):
        vector, verdict = candidate._design_combined_verdict(
            SCOPE_IDS[0], outcome
        )
        candidate.validate_combined_candidate_verdict_design(
            verdict,
            expected_scope_id=SCOPE_IDS[0],
            ordered_rule_evaluations=vector,
            candidate_index=0,
            dispatcher_call_count=len(vector),
            aggregator_call_count=1,
        )
    vector, verdict = candidate._design_combined_verdict(SCOPE_IDS[0], "passed")
    copied_vector = tuple([*vector])
    copied_verdict = object.__new__(type(verdict))
    for name, value in vars(verdict).items():
        object.__setattr__(
            copied_verdict,
            name,
            copied_vector if name == "rule_evaluations" else value,
        )
    try:
        candidate.validate_combined_candidate_verdict_design(
            copied_verdict,
            expected_scope_id=SCOPE_IDS[0],
            ordered_rule_evaluations=vector,
            candidate_index=0,
            dispatcher_call_count=len(vector),
            aggregator_call_count=1,
        )
    except candidate.StageAdmissionOrchestrationError as error:
        if error.code != ERROR_CODES[7]:
            raise ValueError("combined validator error code drift")
    else:
        raise ValueError("combined validator accepted copied vector")

    def forged(source: object, **changes: object) -> object:
        values = dict(vars(source))
        values.update(changes)
        result = object.__new__(type(source))
        for name, value in values.items():
            object.__setattr__(result, name, value)
        return result

    def assert_aggregator_invariant_error(
        value: object,
        expected_vector: tuple[Any, ...],
    ) -> None:
        try:
            candidate.validate_combined_candidate_verdict_design(
                value,
                expected_scope_id=SCOPE_IDS[0],
                ordered_rule_evaluations=expected_vector,
                candidate_index=0,
                dispatcher_call_count=len(expected_vector),
                aggregator_call_count=1,
            )
        except candidate.StageAdmissionOrchestrationError as error:
            if error.code != ERROR_CODES[7]:
                raise ValueError("rejected branch error code drift")
        else:
            raise ValueError("rejected branch mutation accepted")

    rejected_vector = candidate._design_rejected_ordered_vector(
        SCOPE_IDS[0], (1,)
    )
    rejected_verdict = (
        candidate._design_rejected_aggregator_fail_closed_verdict(
            SCOPE_IDS[0]
        )
    )
    candidate.validate_combined_candidate_verdict_design(
        rejected_verdict,
        expected_scope_id=SCOPE_IDS[0],
        ordered_rule_evaluations=rejected_vector,
        candidate_index=0,
        dispatcher_call_count=len(rejected_vector),
        aggregator_call_count=1,
    )
    for additional in (((2, "invalid"),), ((2, "blocked"),)):
        mixed = candidate._design_rejected_ordered_vector(
            SCOPE_IDS[0],
            (1,),
            additional_outcomes=additional,
        )
        candidate.validate_combined_candidate_verdict_design(
            rejected_verdict,
            expected_scope_id=SCOPE_IDS[0],
            ordered_rule_evaluations=mixed,
            candidate_index=0,
            dispatcher_call_count=len(mixed),
            aggregator_call_count=1,
        )
    assert_aggregator_invariant_error(
        forged(
            rejected_verdict,
            reason=COMMITTED_REQUIRED_RULE_INVALID_REASON,
        ),
        rejected_vector,
    )
    assert_aggregator_invariant_error(
        forged(rejected_verdict, rule_evaluations=rejected_vector),
        rejected_vector,
    )
    assert_aggregator_invariant_error(rejected_verdict, vector)


def _assert_dynamic_no_runtime_calls(
    candidate: Any, snapshot: Sequence[Any]
) -> None:
    runtime = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_unified_dispatch_runtime_with_"
        "admit_001_to_015"
    )
    aggregation = importlib.import_module(
        "covalent_ext."
        "covapie_bulk_download_admission_combined_candidate_verdict_and_"
        "cross_rule_aggregation_v1"
    )

    def blocked(*args: object, **kwargs: object) -> Any:
        raise AssertionError("real runtime callable invoked")

    saved_dispatch = runtime.evaluate_admission_rule
    saved_registry = runtime.EVALUATOR_REGISTRY
    saved_aggregate = aggregation.aggregate_admission_rule_evaluations
    try:
        runtime.evaluate_admission_rule = blocked
        runtime.EVALUATOR_REGISTRY = MappingProxyType(
            {rule_id: blocked for rule_id in saved_registry}
        )
        aggregation.aggregate_admission_rule_evaluations = blocked
        mapping = MappingProxyType({"opaque": object()})
        item = candidate.AdmissionCandidateOrchestrationInput(
            mapping, mapping, mapping
        )
        candidate.classify_stage_global_orchestration_contract_design(
            SCOPE_IDS[-1],
            (item, item),
            batch_context=mapping,
            stage_authorization_context=mapping,
        )
        candidate._truth_rows()
        candidate.build_artifacts(snapshot, repo_root=ROOT)
    finally:
        runtime.evaluate_admission_rule = saved_dispatch
        runtime.EVALUATOR_REGISTRY = saved_registry
        aggregation.aggregate_admission_rule_evaluations = saved_aggregate


def _read_disk() -> dict[str, bytes]:
    absolute = ROOT / DERIVED_ROOT
    if not absolute.is_dir() or absolute.is_symlink():
        raise ValueError("derived root unsafe")
    inventory = tuple(sorted(path.name for path in absolute.iterdir()))
    if inventory != tuple(sorted(OUTPUT_NAMES)):
        raise ValueError("derived Exact6 inventory drift")
    return {
        name: _pinned_read(ROOT, DERIVED_ROOT / name) for name in OUTPUT_NAMES
    }


def _assert_preconditions(snapshot: Sequence[Mapping[str, Any]]) -> None:
    content = snapshot[6]["content"]
    if type(content) is not bytes:
        raise ValueError("PRE source type drift")
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    rows = list(reader)
    if len(rows) != 45:
        raise ValueError("PRE row count drift")
    statuses = Counter(row["implementation_completion_status"] for row in rows)
    blocking = sum(row["implementation_blocking"] == "true" for row in rows)
    by_id = {row["precondition_id"]: row for row in rows}
    if (
        statuses != {"complete": 43, "incomplete": 2}
        or blocking != 2
        or by_id["PRE_036"]["implementation_completion_status"] != "complete"
        or by_id["PRE_036"]["implementation_blocking"] != "false"
        or tuple(
            key
            for key in ("PRE_038", "PRE_042")
            if by_id[key]["implementation_completion_status"] == "incomplete"
            and by_id[key]["implementation_blocking"] == "true"
        )
        != ("PRE_038", "PRE_042")
    ):
        raise ValueError("PRE 43/0/2/2 continuity drift")


def _assert_issue(content: bytes) -> None:
    reader = csv.DictReader(io.StringIO(content.decode(), newline=""))
    rows = list(reader)
    open_ids = tuple(
        row["issue_id"]
        for row in rows
        if row["successor_effective_status"]
        not in ("resolved", "retired", "closed", "complete")
    )
    if (
        len(rows) != 30
        or _sha(content) != SOURCE_BOUNDARY[7][1]
        or open_ids
        != (
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        )
    ):
        raise ValueError("issue Exact30 continuity drift")


class RefRecord(NamedTuple):
    name: str
    oid: str
    kind: str


def _ref_inventory() -> tuple[RefRecord, ...]:
    content = _git(
        "for-each-ref",
        "--sort=refname",
        "--format=%(refname)%09%(objectname)%09%(objecttype)",
    ).decode()
    records = []
    for line in content.splitlines():
        name, oid, kind = line.split("\t")
        records.append(RefRecord(name, oid, kind))
    return tuple(records)


FORMAL_REF_NAMES = (
    "refs/heads/main",
    "refs/remotes/origin/HEAD",
    "refs/remotes/origin/main",
)


def _assert_persistent_refs(refs: Sequence[RefRecord]) -> None:
    by_name = {record.name: record for record in refs}
    if len(by_name) != len(refs):
        raise ValueError("duplicate ref inventory")
    for name in FORMAL_REF_NAMES:
        record = by_name.get(name)
        if record is None or record.kind != "commit":
            raise ValueError(f"formal ref missing or non-commit: {name}")
    for record in refs:
        if record.name in FORMAL_REF_NAMES:
            continue
        if not record.name.startswith(f"{PLATFORM_NAMESPACE}/"):
            raise ValueError(f"persistent ref forbidden: {record.name}")
        if PLATFORM_PATTERN.fullmatch(record.name) is None or record.kind != "tree":
            raise ValueError(f"platform ref trust boundary drift: {record.name}")
        if any(
            term in record.name
            for term in ("covapie", "candidate", "temporary", "backup", "review")
        ):
            raise ValueError("platform ref blocked term")


def _origin_head() -> tuple[str, str]:
    return (
        _git("symbolic-ref", "refs/remotes/origin/HEAD").decode().strip(),
        _git("rev-parse", "refs/remotes/origin/HEAD").decode().strip(),
    )


def _assert_formal_refs(
    refs: Sequence[RefRecord],
    *,
    expected_main: str,
    expected_origin: str,
    origin_head: tuple[str, str],
) -> None:
    by_name = {record.name: record for record in refs}
    if (
        by_name.get("refs/heads/main")
        != RefRecord("refs/heads/main", expected_main, "commit")
        or by_name.get("refs/remotes/origin/main")
        != RefRecord("refs/remotes/origin/main", expected_origin, "commit")
        or by_name.get("refs/remotes/origin/HEAD")
        != RefRecord("refs/remotes/origin/HEAD", expected_origin, "commit")
    ):
        raise ValueError("lifecycle-specific formal ref closure drift")
    if origin_head != ("refs/remotes/origin/main", expected_origin):
        raise ValueError("origin/HEAD closure drift")


def _worktrees() -> list[dict[str, str]]:
    blocks = _git("worktree", "list", "--porcelain").decode().strip().split("\n\n")
    result = []
    for block in blocks:
        row: dict[str, str] = {}
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            row[key] = value
        result.append(row)
    return result


class WorktreeRecord(NamedTuple):
    path: str
    head: str
    branch: str
    detached: bool


def _worktree_records() -> tuple[WorktreeRecord, ...]:
    return tuple(
        WorktreeRecord(
            row.get("worktree", ""),
            row.get("HEAD", ""),
            row.get("branch", ""),
            "detached" in row,
        )
        for row in _worktrees()
    )


class Lifecycle(NamedTuple):
    head: str
    index: bytes
    status: bytes
    refs: tuple[RefRecord, ...]
    branch: str
    worktrees: tuple[WorktreeRecord, ...]
    origin_head: tuple[str, str]
    lifecycle: str


def _assert_candidate_commit(head: str) -> None:
    parents = _git("show", "-s", "--format=%P", head).decode().strip().split()
    subject = _git("show", "-s", "--format=%s", head).decode().rstrip("\n")
    if parents != [BASE] or subject != FORMAL_COMMIT_SUBJECT:
        raise ValueError("candidate parent/subject drift")
    changed = tuple(
        item.decode()
        for item in _git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ).split(b"\0")
        if item
    )
    if set(changed) != {path.as_posix() for path in EXACT10} or len(changed) != 10:
        raise ValueError("candidate commit Exact10 drift")
    modes = _git("ls-tree", "-r", head, "--", *[str(x) for x in EXACT10])
    if len(modes.splitlines()) != 10 or any(
        not line.startswith(b"100644 blob ") for line in modes.splitlines()
    ):
        raise ValueError("candidate Exact10 modes drift")


def _recursive_lifecycle() -> Lifecycle:
    head = _strict_head()
    index = _git("ls-files", "--stage", "-z")
    status = _git(
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    )
    refs = _ref_inventory()
    _assert_persistent_refs(refs)
    origin_head = _origin_head()
    worktrees = _worktree_records()
    branch = _git("symbolic-ref", "-q", "--short", "HEAD", check=False).decode().strip()
    if head == BASE:
        lifecycle = "pre_commit"
        _assert_formal_refs(
            refs,
            expected_main=BASE,
            expected_origin=BASE,
            origin_head=origin_head,
        )
        if (
            branch != "main"
            or worktrees
            != (
                WorktreeRecord(
                    str(ROOT),
                    BASE,
                    "refs/heads/main",
                    False,
                ),
            )
        ):
            raise ValueError("formal-main pre_commit topology drift")
        entries = tuple(
            item.decode() for item in status.split(b"\0") if item
        )
        expected = tuple(f"?? {path.as_posix()}" for path in EXACT10)
        if set(entries) != set(expected) or len(entries) != 10:
            raise ValueError(f"pre_commit status drift: {entries}")
    elif branch == "":
        lifecycle = "detached_candidate_post_commit"
        _assert_formal_refs(
            refs,
            expected_main=BASE,
            expected_origin=BASE,
            origin_head=origin_head,
        )
        _assert_candidate_commit(head)
        if len(worktrees) != 2 or status:
            raise ValueError("detached post_commit topology/status drift")
        main_rows = [
            row
            for row in worktrees
            if row.branch == "refs/heads/main"
            and row.head == BASE
            and row.detached is False
        ]
        detached_rows = [
            row
            for row in worktrees
            if row.detached is True
            and row.head == head
            and row.path == str(ROOT)
        ]
        if len(main_rows) != 1 or len(detached_rows) != 1:
            raise ValueError("detached two-worktree closure drift")
    elif branch == "main":
        _assert_candidate_commit(head)
        by_name = {record.name: record for record in refs}
        origin_oid = by_name["refs/remotes/origin/main"].oid
        if origin_oid == BASE:
            lifecycle = "formal_main_post_commit_unpushed"
        elif origin_oid == head:
            lifecycle = "formal_main_post_push"
        else:
            raise ValueError("formal-main origin lifecycle drift")
        _assert_formal_refs(
            refs,
            expected_main=head,
            expected_origin=origin_oid,
            origin_head=origin_head,
        )
        if (
            status
            or worktrees
            != (
                WorktreeRecord(
                    str(ROOT),
                    head,
                    "refs/heads/main",
                    False,
                ),
            )
        ):
            raise ValueError("formal-main post-commit topology/status drift")
    else:
        raise ValueError("unsupported lifecycle branch/head topology")

    if lifecycle not in LIFECYCLE_MODES:
        raise ValueError("lifecycle vocabulary drift")

    for path in EXACT10:
        absolute = ROOT / path
        item = os.lstat(absolute)
        if (
            not stat.S_ISREG(item.st_mode)
            or stat.S_ISLNK(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
        ):
            raise ValueError(f"Exact10 leaf unsafe: {path}")
    for support_root, expected in zip(
        (Path("src/covalent_ext"), Path("scripts"), Path("tests"), Path("docs")),
        SUPPORT_PATHS,
        strict=True,
    ):
        matches = tuple(
            path.relative_to(ROOT)
            for path in (ROOT / support_root).rglob("*")
            if STAGE in path.name
            or "covapie_stage_global_rule_evaluation_orchestration_contract" in path.name
        )
        if matches != (expected,):
            raise ValueError(f"embedded support-stage residue: {matches}")
    derived_parent = ROOT / DERIVED_ROOT.parent
    related = tuple(
        path.name
        for path in derived_parent.iterdir()
        if path.name == STAGE
        or path.name.startswith(STAGING_PREFIX)
        or any(path.name.startswith(prefix) for prefix in LEGACY_STAGING_PREFIXES)
    )
    if related != (STAGE,):
        raise ValueError(f"derived/staging residue: {related}")
    if tuple(sorted(path.name for path in (ROOT / DERIVED_ROOT).iterdir())) != tuple(
        sorted(OUTPUT_NAMES)
    ):
        raise ValueError("derived Exact6 recursive inventory drift")
    if len(_git("ls-files", "-z", "--", "data/raw").split(b"\0")) - 1 != 53:
        raise ValueError("raw historical baseline drift")
    if _git("diff", "--check"):
        raise ValueError("git diff --check failure")
    return Lifecycle(
        head,
        index,
        status,
        refs,
        branch,
        worktrees,
        origin_head,
        lifecycle,
    )


def _assert_lifecycle_stable(first: Lifecycle, final: Lifecycle) -> None:
    if first != final:
        raise ValueError("HEAD/index/status/ref/branch/worktree/lifecycle drift")


def _verify_candidate(
    candidate: Any,
    snapshot: Sequence[Mapping[str, Any]],
    expected: Mapping[str, bytes],
) -> None:
    _assert_candidate_contract(candidate)
    candidate_snapshot = candidate.build_frozen_source_snapshot(ROOT)
    if [
        (
            item.relative_path.as_posix(),
            item.expected_sha256,
            item.base_tree_mode,
            item.base_tree_blob,
            item.index_mode,
            item.index_blob,
            item.index_stage,
            item.filesystem_sha256,
            item.content,
        )
        for item in candidate_snapshot
    ] != [
        (
            row["path"],
            row["sha256"],
            row["base_tree_mode"],
            row["base_tree_blob"],
            row["index_mode"],
            row["index_blob"],
            row["index_stage"],
            row["filesystem_sha256"],
            row["content"],
        )
        for row in snapshot
    ]:
        raise ValueError("production/checker source snapshot inequality")
    actual = candidate.build_artifacts(candidate_snapshot, repo_root=ROOT)
    disk = _read_disk()
    if actual != expected or disk != expected:
        raise ValueError("production/checker/disk artifact inequality")
    _assert_dynamic_no_runtime_calls(candidate, candidate_snapshot)
    with tempfile.TemporaryDirectory(prefix=f"{STAGE}.checker.") as temporary:
        root = Path(temporary) / STAGE
        materialized = candidate._materialize(
            root, actual, repo_root=ROOT
        )
        if {
            name: _pinned_read(Path(temporary), Path(STAGE) / name)
            for name in OUTPUT_NAMES
        } != expected:
            raise ValueError("new-directory materialization inequality")
        before = os.lstat(materialized)
        candidate._materialize(root, actual, repo_root=ROOT)
        after = os.lstat(materialized)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ValueError("existing no-op inode drift")


def main() -> int:
    first = _recursive_lifecycle()
    _assert_static_no_runtime_calls()
    snapshot = _source_snapshot()
    _assert_preconditions(snapshot)
    _assert_issue(snapshot[7]["content"])
    expected = _expected_artifacts(snapshot)
    candidate = _load_candidate()
    _verify_candidate(candidate, snapshot, expected)
    final = _recursive_lifecycle()
    _assert_lifecycle_stable(first, final)
    manifest = json.loads(expected[MANIFEST_NAME])
    report = {
        "all_checks_passed": True,
        "lifecycle": final.lifecycle,
        "source_attestation_count": 16,
        "api_result_contract_row_count": 54,
        "call_plan_row_count": 53,
        "truth_row_count": 307,
        "truth_group_count": 50,
        "safety_row_count": 30,
        "precondition_counts": "43/0/2/2",
        "precondition_transition_count": 0,
        "remaining_preconditions": ["PRE_038", "PRE_042"],
        "issue_row_count": 30,
        "issue_transition_count": 0,
        "issue_byte_identical": True,
        "actual_dispatcher_calls": 0,
        "actual_handler_calls": 0,
        "actual_aggregator_calls": 0,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "ready_for_training": False,
        "manifest_sha256": _sha(expected[MANIFEST_NAME]),
        "exact10_file_count": 10,
        "lifecycle_mode_count": len(LIFECYCLE_MODES),
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "full_recursive_lifecycle_run_count": 2,
        "final_recursive_lifecycle_after_candidate_validation": True,
        "final_recursive_lifecycle_is_last_filesystem_validation": True,
        "persistent_ref_namespace_closure": True,
        "platform_ref_trust_boundary_closure": True,
        "remote_ref_target_closure": True,
        "stage_owned_staging_namespace_closure": True,
        "embedded_stage_residue_lifecycle_closure": True,
        "recommended_next_step": manifest["recommended_next_step"],
    }
    sys.stdout.write(
        json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
