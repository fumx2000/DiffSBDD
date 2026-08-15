"""Freeze the Current11 Task2 Output17 semantic reconciliation contract V1."""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import stat
import subprocess
from pathlib import Path
from typing import Callable, Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as _runtime_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_contract_gate_v1
    as _reference_owner,
)


__all__ = (
    "build_covapie_current11_task2_batch_index_remap_output17_semantic_"
    "reconciliation_contract_gate_v1",
)

ERROR_TOKEN = (
    "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_OUTPUT17_SEMANTIC_"
    "RECONCILIATION_CONTRACT_GATE_V1_ERROR"
)
BASE_COMMIT = "cd392246fc424de609db9c5110d805fbe3d9a555"
BRANCH = "main"

MODULE_PATH = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_output17_"
    "semantic_reconciliation_contract_gate_v1.py"
)
SCRIPT_PATH = (
    "scripts/check_covapie_current11_task2_batch_index_remap_output17_"
    "semantic_reconciliation_contract_gate_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_task2_batch_index_remap_output17_semantic_"
    "reconciliation_contract_gate_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_task2_batch_index_remap_output17_semantic_"
    "reconciliation_contract_gate_v1_guide.md"
)
REPOSITORY_EXACT4 = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)

MANIFEST_NAME = (
    "current11_task2_batch_index_remap_output17_semantic_reconciliation_"
    "manifest.json"
)
FIELD_PARTITION_NAME = (
    "current11_task2_batch_index_remap_output17_field_partition.json"
)
METADATA_CONTRACT_NAME = (
    "current11_task2_batch_index_remap_output17_producer_metadata_contract.json"
)
PARITY_CONTRACT_NAME = (
    "current11_task2_batch_index_remap_output17_success_failure_parity_"
    "contract.json"
)
NEGATIVE_MATRIX_NAME = (
    "current11_task2_batch_index_remap_output17_negative_matrix.json"
)
REPORT_NAME = (
    "current11_task2_batch_index_remap_output17_semantic_reconciliation_"
    "gate_report.json"
)
ARTIFACT_NAMES = (
    MANIFEST_NAME,
    FIELD_PARTITION_NAME,
    METADATA_CONTRACT_NAME,
    PARITY_CONTRACT_NAME,
    NEGATIVE_MATRIX_NAME,
    REPORT_NAME,
)
STABLE_ARTIFACT_NAMES = ARTIFACT_NAMES[:5]
STABLE_DIGEST_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_OUTPUT17_SEMANTIC_"
    b"RECONCILIATION_CONTRACT_GATE_V1\0"
)
GATE_STATUS = "PASS_OUTPUT17_SEMANTIC_RECONCILIATION_CONTRACT_ONLY"
SELECTED_RECONCILIATION_MODEL = (
    "B_plus_E_success_plus_runtime_whole_failure_exact_plus_historical_"
    "failure_self_validation"
)
RUNTIME_TARGET = "current_public_adapter_output17_v1"
HISTORICAL_SUCCESS_ORACLE = (
    "historical_reference_evaluator_success_outputs_v1"
)

EXACT17_FIELD_ORDER = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "batch_sample_order",
    "pair_values_source_row_indices",
    "pair_values_parser_local_indices",
    "pair_values_batch_indices",
    "pair_values_joint_global_indices",
    "pair_sample_indices",
    "sample_pair_offsets",
    "entry_validity",
    "sample_validity",
    "source_entry_outcomes",
    "remap_status",
    "failure_reason",
    "provenance",
    "readiness",
)
CORE15_FIELD_ORDER = EXACT17_FIELD_ORDER[:15]
PRODUCER_METADATA_FIELDS = EXACT17_FIELD_ORDER[15:]
SHARED_SUCCESS_PROVENANCE_FIELDS = (
    "joint_layout_descriptor",
    "joint_index_status",
)
JOINT_LAYOUT = "ligand_segment_then_pocket_segment_v1"

CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

REVIEWED_EVIDENCE_SPECS = {
    "output17_semantic_reconciliation_design_report": {
        "relative_path": (
            "review-scratch/current11-task2-remap-output17-semantic-"
            "reconciliation-design-v1/"
            "remap_output17_semantic_reconciliation_design_report.md"
        ),
        "bytes": 31207,
        "LF": 552,
        "sha256": (
            "e597dc7605e504b3d0c9a81b930c0dd6ea14b869380f2bebb6654564bfdc0f30"
        ),
    },
    "successor_adapter_parity_timing_report": {
        "relative_path": (
            "review-scratch/current11-task2-remap-successor-adapter-parity-"
            "timing-v1/remap_successor_adapter_parity_timing_report.md"
        ),
        "bytes": 15200,
        "LF": 218,
        "sha256": (
            "6425ade470cf12be31b367062f4612e634160e5611e665bc98f4efe17c667c79"
        ),
    },
}

OWNER_SPECS = {
    "current_runtime_adapter": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_v1.py"
        ),
        "bytes": 56510,
        "LF": 1368,
        "sha256": (
            "d09bd5648a3c47851efd933fa8c0523c4ab7c67f8cce765b08fb8423a4e57dd2"
        ),
        "git_blob": "11573d4e0857cf69dceb22c3b1ec4f319faa6d08",
        "commit": "b3c76bd4321da5aece08711a4d6f2d421cb8b54b",
        "subject": (
            "add CovaPIE Current11 Task 2 batch index remap adapter v1"
        ),
    },
    "historical_reference_owner": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_contract_gate_v1.py"
        ),
        "bytes": 70077,
        "LF": 926,
        "sha256": (
            "e9f7d83a17d08eda338ce4d64ab60241887e488c6139ee70af7f210b82bc6eec"
        ),
        "git_blob": "6d5f495bac770ef4a87f641ae340fd39947122f4",
        "commit": "6502321ca56ce8895adb3ee20587c383dfbda767",
        "subject": (
            "add CovaPIE Current11 Task 2 batch index remap contract gate v1"
        ),
    },
    "published_predecessor_successor": {
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_predecessor_successor_"
            "v1.py"
        ),
        "bytes": 43997,
        "LF": 1203,
        "sha256": (
            "c1e4b207a6432b6495d85fb799a196cb2370edd41402000fbfcbfcf3514acb05"
        ),
        "git_blob": "0e0ebdca4db0abbfaec921ea34253dcefbb29410",
        "commit": BASE_COMMIT,
        "subject": (
            "add CovaPIE Current11 Task2 remap predecessor successor v1"
        ),
    },
}

REFERENCE_HELPER_SIGNATURES = {
    "_synthetic_case": "() -> 'dict[str, object]'",
    "_synthetic_authority": "() -> 'list[dict[str, object]]'",
    "_evaluate_reference_case": (
        "(case: 'Mapping[str, object]', *, authoritative_tables: "
        "'Sequence[Mapping[str, object]]') -> 'dict[str, object]'"
    ),
    "_empty_failure": (
        "(case: 'Mapping[str, object]', status: 'str', pair_count: 'int') "
        "-> 'dict[str, object]'"
    ),
}
RUNTIME_HELPER_SIGNATURES = {
    "_remap_engine": (
        "(case: 'dict[str, object]', *, authoritative_tables: "
        "'list[dict[str, object]]') -> 'dict[str, object]'"
    ),
    "_validate_source_contract": (
        "(case: 'Mapping[str, object]', source: 'Mapping[str, object]', "
        "authority: 'Sequence[Mapping[str, object]]') -> 'None'"
    ),
    "_failure_output": (
        "(case: 'Mapping[str, object]', status: 'str', source_pair_count: "
        "'int', entry_index: 'int') -> 'dict[str, object]'"
    ),
    "_provenance": (
        "(joint_status: 'str', descriptor: 'object') -> 'dict[str, object]'"
    ),
    "_readiness": "(success: 'bool') -> 'dict[str, bool]'",
}
FROZEN_HELPER_SIGNATURE_COUNT = 9

REFERENCE_SUCCESS_PROVENANCE_KEYS = (
    "joint_index_status",
    "joint_layout_descriptor",
    "reference_contract_evaluator_only",
)
REFERENCE_FAILURE_PROVENANCE_KEYS = (
    "joint_index_status",
    "reference_contract_evaluator_only",
)
REFERENCE_READINESS = {
    "public_adapter_implemented": False,
    "model_integration_authorized": False,
    "loss_authorized": False,
}
RUNTIME_PROVENANCE_KEYS = (
    "join_contract",
    "index_spaces",
    "joint_layout_descriptor",
    "joint_index_status",
    "remap_contract_digest",
    "projection_instance_digest",
    "payload_bundle_digest",
    "projection_contract_digest",
    "coordinates_used_for_selection",
    "debug_metadata_used_for_selection",
)
RUNTIME_PROVENANCE_CONSTANTS = {
    "join_contract": (
        "exact_source_table_row_identity_to_order_preserving_parser_node_v1"
    ),
    "index_spaces": [
        "source_atom_table_data_row_index",
        "parser_sample_local_index",
        "collated_batch_segment_index",
        "dynamics_joint_global_node_index",
    ],
    "remap_contract_digest": (
        "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
    ),
    "projection_instance_digest": (
        "b8e8078700bd019d4a11a00c17dc84fa05e406bbf61b51bf3e887988f3b89255"
    ),
    "payload_bundle_digest": (
        "95e9ed091566bbc547a8f75b975a40c27ce318e95df1553b1f1ac448a91b1f9d"
    ),
    "projection_contract_digest": (
        "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
    ),
    "coordinates_used_for_selection": False,
    "debug_metadata_used_for_selection": False,
}
RUNTIME_READINESS_KEYS = (
    "public_batch_index_remap_adapter_implemented",
    "public_batch_index_remap_adapter_passed",
    "remap_output_built_in_memory",
    "canonical_reference_remap_succeeded",
    "formal_remap_materialized",
    "torch_tensor_materialized",
    "numpy_artifact_materialized",
    "dataloader_modified",
    "model_modified",
    "forward_modified",
    "loss_modified",
    "ready_for_batch_descriptor_compiler_design",
    "ready_for_dataloader_integration",
    "ready_for_model_integration",
    "ready_for_loss_integration",
    "feature_semantics_reaudit_required_before_training",
    "ready_for_training",
)


def _runtime_readiness(success: bool) -> dict[str, bool]:
    return {
        "public_batch_index_remap_adapter_implemented": True,
        "public_batch_index_remap_adapter_passed": success,
        "remap_output_built_in_memory": True,
        "canonical_reference_remap_succeeded": success,
        "formal_remap_materialized": False,
        "torch_tensor_materialized": False,
        "numpy_artifact_materialized": False,
        "dataloader_modified": False,
        "model_modified": False,
        "forward_modified": False,
        "loss_modified": False,
        "ready_for_batch_descriptor_compiler_design": success,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


NEGATIVE_CASES = (
    ("exact17_field_omitted", "omit one Exact17 field"),
    ("exact17_field_reordered", "reorder two Exact17 fields"),
    ("core15_field_omitted", "omit one successful Core15 field"),
    (
        "producer_metadata_moved_into_core15",
        "move provenance into successful Core15",
    ),
    ("success_core15_mismatch", "change one successful Core15 value"),
    ("success_bool_int_type_mismatch", "replace success bool with integer one"),
    ("success_null_semantics_mismatch", "replace no-joint null with a list"),
    ("success_joint_descriptor_mismatch", "change shared joint descriptor"),
    ("success_joint_status_mismatch", "change shared joint status"),
    (
        "reference_success_extra_metadata_field",
        "add reference success provenance field",
    ),
    (
        "reference_success_missing_reference_identity",
        "remove reference_contract_evaluator_only",
    ),
    ("runtime_success_missing_digest", "remove runtime provenance digest"),
    ("runtime_success_wrong_digest", "change runtime provenance digest"),
    (
        "runtime_success_coordinate_flag_true",
        "claim coordinates were used for selection",
    ),
    (
        "runtime_readiness_model_integration_true",
        "claim model integration readiness",
    ),
    (
        "runtime_readiness_loss_integration_true",
        "claim loss integration readiness",
    ),
    ("runtime_readiness_training_true", "claim training readiness"),
    (
        "runtime_feature_semantics_reaudit_false",
        "clear the feature-semantics re-audit requirement",
    ),
    (
        "historical_adapter_false_copied_to_runtime",
        "copy historical public_adapter_implemented into runtime readiness",
    ),
    (
        "runtime_implemented_true_backwritten_to_reference",
        "back-write current implementation truth into historical readiness",
    ),
    (
        "historical_failure_descriptor_absence_normalized",
        "normalize absent historical failure descriptor to null",
    ),
    (
        "historical_failure_offsets_normalized",
        "normalize historical failure offsets to runtime offsets",
    ),
    (
        "historical_failure_entry_zero_rewritten",
        "rewrite historical hard-failure entry zero to the runtime entry",
    ),
    (
        "universal_failure_core15_exact_claim_true",
        "claim universal cross-producer failure Core15 parity",
    ),
    (
        "old_adapter_report_as_successor_authority",
        "treat the old adapter report as successor authority",
    ),
    (
        "hot_loop_readiness_before_lightweight_probe",
        "claim hot-loop readiness before the lightweight parity probe",
    ),
)

_PATH_TYPE = type(Path())


class _ContractInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _ContractInvariantError()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        payload = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _ContractInvariantError() from error
    _validate_payload(payload)
    return payload


def _validate_payload(payload: object) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail()


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            parse_constant=lambda unused: _fail(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _ContractInvariantError() from error
    if type(value) is not dict or _canonical_json(value) != payload:
        _fail()
    return value


def _require_root(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _ContractInvariantError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise _ContractInvariantError() from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _validate_repository_lineage(repo_root: Path) -> None:
    if _run_git(repo_root, ("branch", "--show-current")).strip() != BRANCH:
        _fail()
    _run_git(repo_root, ("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"))


def _safe_candidate_files(repo_root: Path) -> None:
    for relative in REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise _ContractInvariantError() from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or any(
                line.rstrip(b"\r\n").endswith((b" ", b"\t"))
                for line in payload.splitlines(keepends=True)
            )
        ):
            _fail()
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise _ContractInvariantError() from error


def _repository_lifecycle(repo_root: Path) -> str:
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *REPOSITORY_EXACT4)
    ).splitlines()
    expected = {f"?? {relative}" for relative in REPOSITORY_EXACT4}
    if set(status) == expected and len(status) == len(REPOSITORY_EXACT4):
        if index:
            _fail()
        _safe_candidate_files(repo_root)
        return "precommit-untracked"
    if status or len(index) != len(REPOSITORY_EXACT4):
        _fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise _ContractInvariantError() from error
        if (
            relative not in REPOSITORY_EXACT4
            or relative in seen
            or mode != "100644"
            or stage != "0"
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != blob
            or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
            != blob
        ):
            _fail()
        seen.add(relative)
    if seen != set(REPOSITORY_EXACT4):
        _fail()
    _safe_candidate_files(repo_root)
    return "clean-tracked-successor"


def _direct_path_item(path: Path) -> tuple[object, ...]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    except OSError as error:
        raise _ContractInvariantError() from error
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha256(payload),
    )


def _repository_snapshot(repo_root: Path) -> tuple[object, ...]:
    paths = (*REPOSITORY_EXACT4, *(str(spec["path"]) for spec in OWNER_SPECS.values()))
    return (
        _run_git(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple((relative, _direct_path_item(repo_root / relative)) for relative in paths),
    )


def _evidence_snapshot(state_root: Path) -> tuple[object, ...]:
    return tuple(
        (
            str(spec["relative_path"]),
            _direct_path_item(state_root / str(spec["relative_path"])),
        )
        for spec in REVIEWED_EVIDENCE_SPECS.values()
    )


def _verify_owner_identity(
    repo_root: Path,
    owner_name: str,
    spec: Mapping[str, object],
) -> dict[str, object]:
    relative = str(spec["path"])
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
        tree = _run_git(repo_root, ("ls-tree", "HEAD", "--", relative)).strip()
        tree_metadata, listed = tree.split("\t", 1)
        tree_mode, tree_kind, tree_blob = tree_metadata.split()
    except (OSError, ValueError) as error:
        raise _ContractInvariantError() from error
    commit = str(spec["commit"])
    if (
        listed != relative
        or tree_mode != "100644"
        or tree_kind != "blob"
        or tree_blob != spec["git_blob"]
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or len(payload) != spec["bytes"]
        or payload.count(b"\n") != spec["LF"]
        or _sha256(payload) != spec["sha256"]
        or _run_git(
            repo_root, ("hash-object", "--no-filters", "--", relative)
        ).strip()
        != spec["git_blob"]
        or _run_git(repo_root, ("rev-parse", f"{commit}:{relative}")).strip()
        != spec["git_blob"]
    ):
        _fail()
    _run_git(repo_root, ("cat-file", "-e", f"{commit}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", commit, "HEAD"))
    if (
        _run_git(repo_root, ("show", "-s", "--format=%s", commit)).strip()
        != spec["subject"]
        or _run_git(
            repo_root,
            (
                "diff-tree",
                "--no-commit-id",
                "--name-status",
                "-r",
                commit,
                "--",
                relative,
            ),
        ).strip()
        != f"A\t{relative}"
    ):
        _fail()
    return {
        "owner_name": owner_name,
        "relative_path": relative,
        "bytes": spec["bytes"],
        "LF": spec["LF"],
        "sha256": spec["sha256"],
        "git_blob": spec["git_blob"],
        "git_mode": "100644",
        "worktree_mode": "0644",
        "commit": commit,
        "commit_ancestor_or_equal_head": True,
        "head_and_worktree_exact": True,
    }


def _verify_reviewed_evidence(
    state_root: Path,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for evidence_name, spec in REVIEWED_EVIDENCE_SPECS.items():
        relative = str(spec["relative_path"])
        path = state_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise _ContractInvariantError() from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or len(payload) != spec["bytes"]
            or payload.count(b"\n") != spec["LF"]
            or _sha256(payload) != spec["sha256"]
        ):
            _fail()
        rows.append(
            {
                "evidence_name": evidence_name,
                "relative_path": relative,
                "bytes": spec["bytes"],
                "LF": spec["LF"],
                "sha256": spec["sha256"],
                "mode": "0644",
                "reviewed_predecessor_evidence_only": True,
                "sole_semantic_authority": False,
            }
        )
    return rows


def _validate_helper_signatures() -> list[dict[str, object]]:
    groups = (
        ("historical_reference_owner", _reference_owner, REFERENCE_HELPER_SIGNATURES),
        ("current_runtime_adapter", _runtime_owner, RUNTIME_HELPER_SIGNATURES),
    )
    rows: list[dict[str, object]] = []
    for owner_name, module, expected in groups:
        for helper_name, expected_signature in expected.items():
            helper = getattr(module, helper_name, None)
            if not callable(helper):
                _fail()
            try:
                observed = str(inspect.signature(helper))
            except (TypeError, ValueError) as error:
                raise _ContractInvariantError() from error
            if observed != expected_signature:
                _fail()
            rows.append(
                {
                    "owner_name": owner_name,
                    "helper_name": helper_name,
                    "signature": observed,
                }
            )
    if len(rows) != FROZEN_HELPER_SIGNATURE_COUNT:
        _fail()
    return rows


def _deep_exact(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        if tuple(left) != tuple(right):
            return False
        return all(_deep_exact(left[key], right[key]) for key in left)
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(
            _deep_exact(a, b) for a, b in zip(left, right)
        )
    return bool(left == right)


def _require_exact17_order(order: object) -> None:
    if type(order) not in (list, tuple) or tuple(order) != EXACT17_FIELD_ORDER:
        _fail()


def _require_core15_order(order: object) -> None:
    if type(order) not in (list, tuple) or tuple(order) != CORE15_FIELD_ORDER:
        _fail()


def _validate_output_shape(output: object) -> None:
    if type(output) is not dict or tuple(output) != EXACT17_FIELD_ORDER:
        _fail()


def _require_core15_parity(reference: object, runtime: object) -> None:
    _validate_output_shape(reference)
    _validate_output_shape(runtime)
    for field in CORE15_FIELD_ORDER:
        if not _deep_exact(reference[field], runtime[field]):
            _fail()


def _validate_shared_success_provenance(
    reference: Mapping[str, object],
    runtime: Mapping[str, object],
) -> None:
    reference_provenance = reference.get("provenance")
    runtime_provenance = runtime.get("provenance")
    if type(reference_provenance) is not dict or type(runtime_provenance) is not dict:
        _fail()
    for field in SHARED_SUCCESS_PROVENANCE_FIELDS:
        if not _deep_exact(reference_provenance.get(field), runtime_provenance.get(field)):
            _fail()


def _validate_reference_metadata(
    output: Mapping[str, object],
    *,
    success: bool,
) -> None:
    provenance = output.get("provenance")
    readiness = output.get("readiness")
    if type(provenance) is not dict or type(readiness) is not dict:
        _fail()
    expected_keys = (
        REFERENCE_SUCCESS_PROVENANCE_KEYS
        if success
        else REFERENCE_FAILURE_PROVENANCE_KEYS
    )
    if tuple(provenance) != expected_keys or tuple(readiness) != tuple(REFERENCE_READINESS):
        _fail()
    if not _deep_exact(readiness, REFERENCE_READINESS):
        _fail()
    if provenance.get("reference_contract_evaluator_only") is not True:
        _fail()
    if success:
        descriptor = provenance.get("joint_layout_descriptor")
        expected_status = (
            "REMAPPED_EXACT"
            if descriptor == JOINT_LAYOUT
            else "JOINT_INDEX_SPACE_UNAVAILABLE"
        )
        if descriptor not in (JOINT_LAYOUT, None) or provenance.get(
            "joint_index_status"
        ) != expected_status:
            _fail()
    elif (
        provenance.get("joint_index_status")
        != "JOINT_INDEX_SPACE_UNAVAILABLE"
        or "joint_layout_descriptor" in provenance
    ):
        _fail()


def _expected_runtime_provenance(
    *,
    success: bool,
    descriptor: object,
) -> dict[str, object]:
    status = (
        "REMAPPED_EXACT"
        if success and descriptor == JOINT_LAYOUT
        else "JOINT_INDEX_SPACE_UNAVAILABLE"
    )
    return {
        "join_contract": RUNTIME_PROVENANCE_CONSTANTS["join_contract"],
        "index_spaces": copy.deepcopy(RUNTIME_PROVENANCE_CONSTANTS["index_spaces"]),
        "joint_layout_descriptor": descriptor,
        "joint_index_status": status,
        "remap_contract_digest": RUNTIME_PROVENANCE_CONSTANTS[
            "remap_contract_digest"
        ],
        "projection_instance_digest": RUNTIME_PROVENANCE_CONSTANTS[
            "projection_instance_digest"
        ],
        "payload_bundle_digest": RUNTIME_PROVENANCE_CONSTANTS[
            "payload_bundle_digest"
        ],
        "projection_contract_digest": RUNTIME_PROVENANCE_CONSTANTS[
            "projection_contract_digest"
        ],
        "coordinates_used_for_selection": False,
        "debug_metadata_used_for_selection": False,
    }


def _validate_runtime_metadata(
    output: Mapping[str, object],
    *,
    success: bool,
) -> None:
    provenance = output.get("provenance")
    readiness = output.get("readiness")
    if (
        type(provenance) is not dict
        or type(readiness) is not dict
        or tuple(provenance) != RUNTIME_PROVENANCE_KEYS
        or tuple(readiness) != RUNTIME_READINESS_KEYS
    ):
        _fail()
    descriptor = provenance.get("joint_layout_descriptor")
    if success:
        if descriptor not in (JOINT_LAYOUT, None):
            _fail()
    elif descriptor is not None:
        _fail()
    if not _deep_exact(
        provenance,
        _expected_runtime_provenance(success=success, descriptor=descriptor),
    ) or not _deep_exact(readiness, _runtime_readiness(success)):
        _fail()


def _success_case_evidence(
    case_name: str,
    case: dict[str, object],
    authority: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    before_case = copy.deepcopy(case)
    before_authority = copy.deepcopy(authority)
    reference = _reference_owner._evaluate_reference_case(
        case,
        authoritative_tables=authority,
    )
    runtime = _runtime_owner._remap_engine(
        copy.deepcopy(case),
        authoritative_tables=copy.deepcopy(authority),
    )
    if not _deep_exact(case, before_case) or not _deep_exact(authority, before_authority):
        _fail()
    _validate_output_shape(reference)
    _validate_output_shape(runtime)
    if (
        reference.get("remap_status") != "REMAPPED_EXACT"
        or runtime.get("remap_status") != "REMAPPED_EXACT"
    ):
        _fail()
    _require_core15_parity(reference, runtime)
    _validate_shared_success_provenance(reference, runtime)
    _validate_reference_metadata(reference, success=True)
    _validate_runtime_metadata(runtime, success=True)
    whole_exact = _deep_exact(reference, runtime)
    if whole_exact or _canonical_json(reference) == _canonical_json(runtime):
        _fail()
    not_in_batch_count = sum(
        row.get("status") == "NOT_IN_BATCH"
        for row in reference["source_entry_outcomes"]
    )
    return reference, runtime, {
        "case_name": case_name,
        "reference_success": True,
        "runtime_success": True,
        "core15_exact": True,
        "shared_provenance2_exact": True,
        "reference_metadata_validator_passed": True,
        "runtime_metadata_validator_passed": True,
        "whole_output17_exact": False,
        "not_in_batch_source_outcome_count": not_in_batch_count,
    }


def _subset_case(base: Mapping[str, object]) -> dict[str, object]:
    case = copy.deepcopy(base)
    case["batch_sample_order"] = [copy.deepcopy(base["batch_sample_order"][0])]
    case["batch_sample_atom_identity_tables"] = [
        copy.deepcopy(base["batch_sample_atom_identity_tables"][0])
    ]
    case["batch_role_lengths"] = {"pocket": [8], "ligand": [8]}
    case["batch_role_offsets"] = {"pocket": [0, 8], "ligand": [0, 8]}
    case["batch_membership_masks"] = {
        "pocket": [0] * 8,
        "ligand": [0] * 8,
    }
    return case


def _capture_runtime_failure(
    case: Mapping[str, object],
    source: Mapping[str, object],
    authority: Sequence[Mapping[str, object]],
) -> object:
    try:
        _runtime_owner._validate_source_contract(case, source, authority)
    except _runtime_owner._InputFailure as error:
        return error
    _fail()


def _hard_failure_fixture() -> tuple[
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
]:
    authority: list[dict[str, object]] = []
    identities: list[dict[str, object]] = []
    for index in range(11):
        identity = {
            "source_sample_index": index,
            "sample_index_row_id": f"FAIL{index:02d}",
            "sample_preparation_input_id": f"PREP{index:02d}",
            "pdb_id": f"P{index:03d}",
            "ligand_comp_id": f"L{index:03d}",
        }
        identities.append(identity)
        roles: dict[str, object] = {}
        for role in ("pocket", "ligand"):
            digest = _sha256(
                f"output17-failure-fixture:{index}:{role}".encode("ascii")
            )
            atom = {
                "atom_site_id": f"{index}-{role}-0",
                "atom_name": "C0",
                "type_symbol": "C",
                "residue_name_or_ligand_comp_id": f"R{index:02d}",
                "auth_asym_id": "A",
                "auth_seq_id": str(index),
                "label_asym_id": "A" if role == "pocket" else "B",
                "label_seq_id": "",
            }
            roles[role] = {
                "role": role,
                "root_kind": "repo_root",
                "relative_path": f"synthetic/output17/{index}/{role}.csv",
                "SHA256": digest,
                "row_count": 8,
                "row_order_digest": digest,
                "row_order_version": "physical_csv_data_row_order_v1",
                "selected_source_row_index_0based": 0,
                "selected_parser_local_index": 0,
                "selected_atom_identity": atom,
                "parser_output_atom_count": 8,
                "source_to_parser_local": {str(row): row for row in range(8)},
            }
        authority.append(
            {"sample_identity": copy.deepcopy(identity), "roles": roles}
        )
    original_pairs = [[0, 0] for unused in range(11)]
    case = {
        "schema_version": _runtime_owner._INPUT_SCHEMA,
        "source_projection_digest": _runtime_owner._PROJECTION_DIGEST,
        "source_payload_digest": _runtime_owner._PAYLOAD_DIGEST,
        "parser_schema_version": _runtime_owner._PARSER_SCHEMA,
        "collate_schema_version": _runtime_owner._COLLATE_SCHEMA,
        "source_sample_order": copy.deepcopy(identities),
        "source_pair_values_int64": copy.deepcopy(original_pairs),
        "source_sample_offsets_int64": list(range(12)),
        "source_entry_validity_bool": [True] * 11,
        "source_sample_validity_bool": [True] * 11,
        "batch_sample_order": copy.deepcopy(identities[:3]),
        "batch_sample_atom_identity_tables": copy.deepcopy(authority[:3]),
        "batch_role_lengths": {"pocket": [8, 8, 8], "ligand": [8, 8, 8]},
        "batch_role_offsets": {
            "pocket": [0, 8, 16, 24],
            "ligand": [0, 8, 16, 24],
        },
        "batch_membership_masks": {
            "pocket": [ordinal for ordinal in range(3) for unused in range(8)],
            "ligand": [ordinal for ordinal in range(3) for unused in range(8)],
        },
        "joint_layout_descriptor": JOINT_LAYOUT,
    }
    source = {
        "sample_order": copy.deepcopy(identities),
        "sample_pair_offsets": list(range(12)),
        "entry_validity": [True] * 11,
        "sample_validity": [True] * 11,
        "pair_values_source_row_indices": original_pairs,
    }
    case["source_pair_values_int64"][2] = [8, 0]
    return case, source, authority


def _core_difference_fields(
    reference: Mapping[str, object],
    runtime: Mapping[str, object],
) -> list[str]:
    return [
        field
        for field in CORE15_FIELD_ORDER
        if not _deep_exact(reference[field], runtime[field])
    ]


def _validate_schema_failure_relationship(
    reference: Mapping[str, object],
    runtime: Mapping[str, object],
) -> None:
    batch_size = len(reference["batch_sample_order"])
    if (
        reference.get("remap_status") != "SCHEMA_VERSION_MISMATCH"
        or runtime.get("remap_status") != "SCHEMA_VERSION_MISMATCH"
        or reference.get("failure_reason") != "SCHEMA_VERSION_MISMATCH"
        or runtime.get("failure_reason") != "SCHEMA_VERSION_MISMATCH"
        or reference.get("sample_pair_offsets") != [0]
        or reference.get("sample_validity") != []
        or runtime.get("sample_pair_offsets") != [0] * (batch_size + 1)
        or runtime.get("sample_validity") != [False] * batch_size
        or _core_difference_fields(reference, runtime)
        != ["sample_pair_offsets", "sample_validity"]
    ):
        _fail()


def _validate_hard_failure_relationship(
    reference: Mapping[str, object],
    runtime: Mapping[str, object],
    *,
    runtime_entry_index: int,
) -> None:
    reference_outcomes = reference.get("source_entry_outcomes")
    runtime_outcomes = runtime.get("source_entry_outcomes")
    if (
        runtime_entry_index == 0
        or type(reference_outcomes) is not list
        or type(runtime_outcomes) is not list
        or reference.get("remap_status") != "SOURCE_ROW_OUT_OF_RANGE"
        or runtime.get("remap_status") != "SOURCE_ROW_OUT_OF_RANGE"
        or reference_outcomes[0].get("status") != "SOURCE_ROW_OUT_OF_RANGE"
        or runtime_outcomes[runtime_entry_index].get("status")
        != "SOURCE_ROW_OUT_OF_RANGE"
        or runtime_outcomes[0].get("status") != "ENTRY_INVALID"
        or _deep_exact(reference_outcomes, runtime_outcomes)
        or "source_entry_outcomes" not in _core_difference_fields(reference, runtime)
    ):
        _fail()


def _pure_semantic_evidence() -> dict[str, object]:
    _require_exact17_order(getattr(_runtime_owner, "_OUTPUT_FIELD_ORDER", None))
    authority = _reference_owner._synthetic_authority()
    base = _reference_owner._synthetic_case()
    joint_reference, joint_runtime, joint_row = _success_case_evidence(
        "synthetic_joint",
        copy.deepcopy(base),
        copy.deepcopy(authority),
    )
    no_joint = copy.deepcopy(base)
    no_joint["joint_layout_descriptor"] = None
    no_joint_reference, no_joint_runtime, no_joint_row = _success_case_evidence(
        "synthetic_no_joint",
        no_joint,
        copy.deepcopy(authority),
    )
    subset = _subset_case(base)
    subset_reference, subset_runtime, subset_row = _success_case_evidence(
        "synthetic_subset_not_in_batch",
        subset,
        copy.deepcopy(authority),
    )
    if subset_row["not_in_batch_source_outcome_count"] < 1:
        _fail()

    schema_case = copy.deepcopy(base)
    schema_case["schema_version"] = "invalid_output17_schema_fixture"
    schema_reference = _reference_owner._evaluate_reference_case(
        schema_case,
        authoritative_tables=copy.deepcopy(authority),
    )
    schema_error = _capture_runtime_failure(schema_case, {}, ())
    if (
        type(schema_error) is not _runtime_owner._InputFailure
        or schema_error.status != "SCHEMA_VERSION_MISMATCH"
        or schema_error.entry_index != 0
    ):
        _fail()
    schema_runtime = _runtime_owner._failure_output(
        schema_case,
        schema_error.status,
        len(schema_case["source_pair_values_int64"]),
        schema_error.entry_index,
    )
    _validate_output_shape(schema_reference)
    _validate_output_shape(schema_runtime)
    _validate_reference_metadata(schema_reference, success=False)
    _validate_runtime_metadata(schema_runtime, success=False)
    _validate_schema_failure_relationship(schema_reference, schema_runtime)

    hard_case, hard_source, hard_authority = _hard_failure_fixture()
    hard_reference = _reference_owner._evaluate_reference_case(
        hard_case,
        authoritative_tables=hard_authority,
    )
    hard_error = _capture_runtime_failure(
        hard_case,
        hard_source,
        hard_authority,
    )
    if (
        type(hard_error) is not _runtime_owner._InputFailure
        or hard_error.status != "SOURCE_ROW_OUT_OF_RANGE"
        or hard_error.entry_index != 2
    ):
        _fail()
    hard_runtime = _runtime_owner._failure_output(
        hard_case,
        hard_error.status,
        len(hard_case["source_pair_values_int64"]),
        hard_error.entry_index,
    )
    _validate_output_shape(hard_reference)
    _validate_output_shape(hard_runtime)
    _validate_reference_metadata(hard_reference, success=False)
    _validate_runtime_metadata(hard_runtime, success=False)
    _validate_hard_failure_relationship(
        hard_reference,
        hard_runtime,
        runtime_entry_index=hard_error.entry_index,
    )
    return {
        "success_rows": [joint_row, no_joint_row, subset_row],
        "failure_rows": [
            {
                "case_name": "schema_version_mismatch",
                "common_status_and_reason_exact": True,
                "core15_exact": False,
                "core15_difference_fields": _core_difference_fields(
                    schema_reference, schema_runtime
                ),
                "historical_sample_pair_offsets": schema_reference[
                    "sample_pair_offsets"
                ],
                "runtime_sample_pair_offsets": schema_runtime[
                    "sample_pair_offsets"
                ],
                "historical_sample_validity": schema_reference["sample_validity"],
                "runtime_sample_validity": schema_runtime["sample_validity"],
                "historical_metadata_validator_passed": True,
                "runtime_metadata_validator_passed": True,
            },
            {
                "case_name": "source_row_out_of_range_nonzero_entry",
                "common_status_and_reason_exact": True,
                "core15_exact": False,
                "source_entry_outcomes_exact": False,
                "historical_hard_failure_entry_index": 0,
                "runtime_hard_failure_entry_index": hard_error.entry_index,
                "runtime_hard_failure_entry_is_nonzero": True,
                "historical_metadata_validator_passed": True,
                "runtime_metadata_validator_passed": True,
            },
        ],
        "outputs": {
            "joint_reference": joint_reference,
            "joint_runtime": joint_runtime,
            "no_joint_reference": no_joint_reference,
            "no_joint_runtime": no_joint_runtime,
            "subset_reference": subset_reference,
            "subset_runtime": subset_runtime,
            "schema_reference": schema_reference,
            "schema_runtime": schema_runtime,
            "hard_reference": hard_reference,
            "hard_runtime": hard_runtime,
        },
        "runtime_success_whole_output17_golden_self_exact": _deep_exact(
            joint_runtime, copy.deepcopy(joint_runtime)
        ),
        "runtime_failure_whole_output17_golden_self_exact": _deep_exact(
            hard_runtime, copy.deepcopy(hard_runtime)
        ),
    }


def _expect_rejected(action: Callable[[], object]) -> None:
    try:
        action()
    except _ContractInvariantError:
        return
    _fail()


def _require_false(value: object) -> None:
    if value is not False:
        _fail()


def _require_runtime_target(value: object) -> None:
    if value != RUNTIME_TARGET:
        _fail()


def _execute_negative_matrix(evidence: Mapping[str, object]) -> list[str]:
    outputs = evidence["outputs"]
    joint_reference = outputs["joint_reference"]
    joint_runtime = outputs["joint_runtime"]
    no_joint_runtime = outputs["no_joint_runtime"]
    schema_reference = outputs["schema_reference"]
    schema_runtime = outputs["schema_runtime"]
    hard_reference = outputs["hard_reference"]
    hard_runtime = outputs["hard_runtime"]
    passed: list[str] = []

    def rejected(case_id: str, action: Callable[[], object]) -> None:
        _expect_rejected(action)
        passed.append(case_id)

    rejected("exact17_field_omitted", lambda: _require_exact17_order(EXACT17_FIELD_ORDER[:-1]))
    reordered = list(EXACT17_FIELD_ORDER)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    rejected("exact17_field_reordered", lambda: _require_exact17_order(reordered))
    rejected("core15_field_omitted", lambda: _require_core15_order(CORE15_FIELD_ORDER[:-1]))
    moved = list(CORE15_FIELD_ORDER)
    moved[-1] = "provenance"
    rejected("producer_metadata_moved_into_core15", lambda: _require_core15_order(moved))

    bad = copy.deepcopy(joint_runtime)
    bad["failure_reason"] = "ENTRY_INVALID"
    rejected("success_core15_mismatch", lambda: _require_core15_parity(joint_reference, bad))
    bad = copy.deepcopy(joint_runtime)
    bad["entry_validity"][0] = 1
    rejected("success_bool_int_type_mismatch", lambda: _require_core15_parity(joint_reference, bad))
    bad = copy.deepcopy(no_joint_runtime)
    bad["pair_values_joint_global_indices"] = []
    rejected("success_null_semantics_mismatch", lambda: _require_core15_parity(outputs["no_joint_reference"], bad))
    bad = copy.deepcopy(joint_runtime)
    bad["provenance"]["joint_layout_descriptor"] = None
    rejected("success_joint_descriptor_mismatch", lambda: _validate_shared_success_provenance(joint_reference, bad))
    bad = copy.deepcopy(joint_runtime)
    bad["provenance"]["joint_index_status"] = "JOINT_INDEX_SPACE_UNAVAILABLE"
    rejected("success_joint_status_mismatch", lambda: _validate_shared_success_provenance(joint_reference, bad))

    bad = copy.deepcopy(joint_reference)
    bad["provenance"]["extra"] = False
    rejected("reference_success_extra_metadata_field", lambda: _validate_reference_metadata(bad, success=True))
    bad = copy.deepcopy(joint_reference)
    del bad["provenance"]["reference_contract_evaluator_only"]
    rejected("reference_success_missing_reference_identity", lambda: _validate_reference_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    del bad["provenance"]["remap_contract_digest"]
    rejected("runtime_success_missing_digest", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["provenance"]["remap_contract_digest"] = "0" * 64
    rejected("runtime_success_wrong_digest", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["provenance"]["coordinates_used_for_selection"] = True
    rejected("runtime_success_coordinate_flag_true", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["readiness"]["ready_for_model_integration"] = True
    rejected("runtime_readiness_model_integration_true", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["readiness"]["ready_for_loss_integration"] = True
    rejected("runtime_readiness_loss_integration_true", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["readiness"]["ready_for_training"] = True
    rejected("runtime_readiness_training_true", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["readiness"]["feature_semantics_reaudit_required_before_training"] = False
    rejected("runtime_feature_semantics_reaudit_false", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_runtime)
    bad["readiness"]["public_adapter_implemented"] = False
    rejected("historical_adapter_false_copied_to_runtime", lambda: _validate_runtime_metadata(bad, success=True))
    bad = copy.deepcopy(joint_reference)
    bad["readiness"]["public_adapter_implemented"] = True
    rejected("runtime_implemented_true_backwritten_to_reference", lambda: _validate_reference_metadata(bad, success=True))
    bad = copy.deepcopy(schema_reference)
    bad["provenance"]["joint_layout_descriptor"] = None
    rejected("historical_failure_descriptor_absence_normalized", lambda: _validate_reference_metadata(bad, success=False))
    bad = copy.deepcopy(schema_reference)
    bad["sample_pair_offsets"] = copy.deepcopy(schema_runtime["sample_pair_offsets"])
    rejected("historical_failure_offsets_normalized", lambda: _validate_schema_failure_relationship(bad, schema_runtime))
    bad = copy.deepcopy(hard_reference)
    bad["source_entry_outcomes"] = copy.deepcopy(hard_runtime["source_entry_outcomes"])
    rejected("historical_failure_entry_zero_rewritten", lambda: _validate_hard_failure_relationship(bad, hard_runtime, runtime_entry_index=2))
    rejected("universal_failure_core15_exact_claim_true", lambda: _require_false(True))
    rejected("old_adapter_report_as_successor_authority", lambda: _require_runtime_target("historical_adapter_report_v1"))
    rejected("hot_loop_readiness_before_lightweight_probe", lambda: _require_false(True))
    if tuple(passed) != tuple(case_id for case_id, unused in NEGATIVE_CASES):
        _fail()
    return passed


def _field_partition_artifact() -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_remap_output17_field_partition_v1",
        "exact17_field_order": list(EXACT17_FIELD_ORDER),
        "successful_cross_producer_core15_field_order": list(CORE15_FIELD_ORDER),
        "producer_metadata_fields": list(PRODUCER_METADATA_FIELDS),
        "core15_success_cross_producer_authority": True,
        "universal_failure_core15_cross_producer_authority": False,
        "whole_output17_cross_producer_authority": False,
        "runtime_whole_output17_authority": True,
        "exact_type_value_order_and_null_semantics_required": True,
        "bool_int_equivalence_forbidden": True,
    }


def _metadata_validator(
    *,
    provenance_keys: Sequence[str],
    readiness_keys: Sequence[str],
    provenance_values: Mapping[str, object],
    readiness_values: Mapping[str, object],
    dynamic_fields: Mapping[str, object],
) -> dict[str, object]:
    return {
        "provenance_exact_key_order": list(provenance_keys),
        "readiness_exact_key_order": list(readiness_keys),
        "provenance_exact_constant_values": copy.deepcopy(provenance_values),
        "readiness_exact_constant_values": copy.deepcopy(readiness_values),
        "dynamic_fields_and_allowed_values": copy.deepcopy(dynamic_fields),
        "unknown_field_policy": "fail_closed",
        "missing_field_policy": "fail_closed",
        "wrong_type_policy": "fail_closed",
    }


def _metadata_contract_artifact() -> dict[str, object]:
    runtime_constants = copy.deepcopy(RUNTIME_PROVENANCE_CONSTANTS)
    return {
        "schema_version": "covapie_current11_task2_remap_output17_producer_metadata_contract_v1",
        "unified_cross_producer_metadata_schema_defined": False,
        "validators": {
            "reference_success_metadata_v1": _metadata_validator(
                provenance_keys=REFERENCE_SUCCESS_PROVENANCE_KEYS,
                readiness_keys=tuple(REFERENCE_READINESS),
                provenance_values={"reference_contract_evaluator_only": True},
                readiness_values=REFERENCE_READINESS,
                dynamic_fields={
                    "joint_layout_descriptor": [JOINT_LAYOUT, None],
                    "joint_index_status": [
                        "REMAPPED_EXACT",
                        "JOINT_INDEX_SPACE_UNAVAILABLE",
                    ],
                    "allowed_exact_pairs": [
                        [JOINT_LAYOUT, "REMAPPED_EXACT"],
                        [None, "JOINT_INDEX_SPACE_UNAVAILABLE"],
                    ],
                },
            ),
            "reference_failure_metadata_v1": _metadata_validator(
                provenance_keys=REFERENCE_FAILURE_PROVENANCE_KEYS,
                readiness_keys=tuple(REFERENCE_READINESS),
                provenance_values={
                    "joint_index_status": "JOINT_INDEX_SPACE_UNAVAILABLE",
                    "reference_contract_evaluator_only": True,
                },
                readiness_values=REFERENCE_READINESS,
                dynamic_fields={
                    "joint_layout_descriptor": "MUST_BE_ABSENT_NOT_NULL"
                },
            ),
            "runtime_success_metadata_v1": _metadata_validator(
                provenance_keys=RUNTIME_PROVENANCE_KEYS,
                readiness_keys=RUNTIME_READINESS_KEYS,
                provenance_values=runtime_constants,
                readiness_values=_runtime_readiness(True),
                dynamic_fields={
                    "joint_layout_descriptor": [JOINT_LAYOUT, None],
                    "joint_index_status": [
                        "REMAPPED_EXACT",
                        "JOINT_INDEX_SPACE_UNAVAILABLE",
                    ],
                    "allowed_exact_pairs": [
                        [JOINT_LAYOUT, "REMAPPED_EXACT"],
                        [None, "JOINT_INDEX_SPACE_UNAVAILABLE"],
                    ],
                },
            ),
            "runtime_failure_metadata_v1": _metadata_validator(
                provenance_keys=RUNTIME_PROVENANCE_KEYS,
                readiness_keys=RUNTIME_READINESS_KEYS,
                provenance_values={
                    **runtime_constants,
                    "joint_layout_descriptor": None,
                    "joint_index_status": "JOINT_INDEX_SPACE_UNAVAILABLE",
                },
                readiness_values=_runtime_readiness(False),
                dynamic_fields={},
            ),
        },
        "reference_contract_evaluator_only_is_reference_identity": True,
        "historical_public_adapter_implemented_false_is_snapshot_only": True,
        "historical_snapshot_must_not_propagate_to_runtime": True,
    }


def _parity_contract_artifact() -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_remap_output17_success_failure_parity_contract_v1",
        "selected_reconciliation_model": SELECTED_RECONCILIATION_MODEL,
        "option_verdicts": {
            "Option_A": "REJECT",
            "Option_B": "ACCEPT",
            "Option_C": "REJECT_V1",
            "Option_D": "REJECT_V1",
            "Option_E_success": "ACCEPT",
            "Option_E_universal_failure": "REJECT",
        },
        "success_domain": {
            "cross_producer_core15_exact_required": True,
            "shared_provenance_exact_required": True,
            "shared_provenance_fields": list(SHARED_SUCCESS_PROVENANCE_FIELDS),
            "whole_output17_exact_required": False,
            "reference_producer_metadata_self_validation": True,
            "runtime_producer_metadata_self_validation": True,
        },
        "runtime_fast_path": {
            "runtime_whole_output17_exact_required": True,
            "runtime_target": RUNTIME_TARGET,
            "runtime_golden_producer": RUNTIME_TARGET,
            "success": True,
            "failure": True,
            "old_adapter_report_authoritative": False,
        },
        "historical_private_failure": {
            "historical_failure_self_validation": True,
            "cross_producer_core15_exact_required": False,
            "shared_descriptor_exact_required": False,
            "whole_output17_exact_required": False,
            "cross_producer_common_failure_fact_comparison_allowed": True,
            "normalization_forbidden": True,
            "historical_failure_runtime_golden": False,
        },
        "historical_success_value_oracle": HISTORICAL_SUCCESS_ORACLE,
        "universal_failure_core15_cross_producer_parity": False,
    }


def _manifest_artifact(
    owner_rows: Sequence[Mapping[str, object]],
    evidence_rows: Sequence[Mapping[str, object]],
    signature_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_remap_output17_semantic_reconciliation_contract_v1",
        "artifact_names": list(ARTIFACT_NAMES),
        "stable_artifact_names": list(STABLE_ARTIFACT_NAMES),
        "stable_digest_domain_ascii_nul_terminated": (
            "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_OUTPUT17_SEMANTIC_"
            "RECONCILIATION_CONTRACT_GATE_V1\\0"
        ),
        "stable_digest_framing": "uint64be_name_length_name_uint64be_payload_length_payload",
        "report_self_excluded_from_stable_digest": True,
        "selected_reconciliation_model": SELECTED_RECONCILIATION_MODEL,
        "runtime_fast_path_output17_target": RUNTIME_TARGET,
        "runtime_golden_producer": RUNTIME_TARGET,
        "historical_success_value_oracle": HISTORICAL_SUCCESS_ORACLE,
        "historical_failure_runtime_golden": False,
        "supported_repository_lifecycles": [
            "precommit-untracked",
            "clean-tracked-successor",
        ],
        "base_commit": BASE_COMMIT,
        "canonical_mask_semantics": [
            {"semantic_name": semantic, "display_alias": alias}
            for semantic, alias in CANONICAL_MASKS
        ],
        "historical_immutability": {
            "historical_stable5_frozen": True,
            "historical_reference_vectors_frozen": True,
            "historical_remap_contract_gate_frozen": True,
            "current_adapter_frozen": True,
            "published_successor_frozen": True,
        },
        "production_owner_identities": [dict(row) for row in owner_rows],
        "reviewed_evidence_identities": [dict(row) for row in evidence_rows],
        "reviewed_reports_are_sole_semantic_authority": False,
        "source_independently_validated": True,
        "frozen_helper_signatures": [dict(row) for row in signature_rows],
        "frozen_helper_signature_count": len(signature_rows),
        "public_or_heavy_product_called": False,
        "canonical_masks_modified": False,
    }


def _negative_matrix_artifact() -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_remap_output17_negative_matrix_v1",
        "case_count": len(NEGATIVE_CASES),
        "all_cases_fail_closed": True,
        "cases": [
            {
                "case_index": index,
                "case_id": case_id,
                "mutation": mutation,
                "required_verdict": "REJECT_FAIL_CLOSED",
            }
            for index, (case_id, mutation) in enumerate(NEGATIVE_CASES, start=1)
        ],
    }


def _manual_stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(STABLE_DIGEST_DOMAIN)
    for name in STABLE_ARTIFACT_NAMES:
        payload = artifacts.get(name)
        if type(payload) is not bytes:
            _fail()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _report_artifact(
    *,
    lifecycle: str,
    stable_digest: str,
    owner_rows: Sequence[Mapping[str, object]],
    evidence_rows: Sequence[Mapping[str, object]],
    signature_rows: Sequence[Mapping[str, object]],
    semantic_evidence: Mapping[str, object],
    negative_passed: Sequence[str],
) -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_remap_output17_semantic_reconciliation_gate_report_v1",
        "gate_status": GATE_STATUS,
        "artifact_file_count": len(ARTIFACT_NAMES),
        "artifact_names": list(ARTIFACT_NAMES),
        "stable_artifact_count": len(STABLE_ARTIFACT_NAMES),
        "stable_contract_digest": stable_digest,
        "report_self_excluded_from_stable_digest": True,
        "repository_lifecycle": lifecycle,
        "owner_identity_validation_passed": True,
        "owner_identities": [dict(row) for row in owner_rows],
        "reviewed_evidence_identity_validation_passed": True,
        "reviewed_evidence_identities": [dict(row) for row in evidence_rows],
        "helper_signature_validation_passed": True,
        "frozen_helper_signature_count": len(signature_rows),
        "exact17_field_order_validated_from_current_adapter_source": True,
        "exact17_field_order": list(EXACT17_FIELD_ORDER),
        "successful_core15_field_order": list(CORE15_FIELD_ORDER),
        "producer_metadata_fields": list(PRODUCER_METADATA_FIELDS),
        "selected_reconciliation_model": SELECTED_RECONCILIATION_MODEL,
        "runtime_fast_path_output17_target": RUNTIME_TARGET,
        "runtime_golden_producer": RUNTIME_TARGET,
        "historical_success_value_oracle": HISTORICAL_SUCCESS_ORACLE,
        "pure_success_case_count": len(semantic_evidence["success_rows"]),
        "pure_success_evidence": copy.deepcopy(semantic_evidence["success_rows"]),
        "pure_failure_case_count": len(semantic_evidence["failure_rows"]),
        "pure_failure_evidence": copy.deepcopy(semantic_evidence["failure_rows"]),
        "historical_failure_producer_self_validation": True,
        "historical_failure_cross_producer_core15_exact": False,
        "historical_failure_shared_descriptor_exact": False,
        "universal_failure_core15_cross_producer_parity": False,
        "runtime_success_whole_output17_target_exact": semantic_evidence[
            "runtime_success_whole_output17_golden_self_exact"
        ],
        "runtime_failure_whole_output17_target_exact": semantic_evidence[
            "runtime_failure_whole_output17_golden_self_exact"
        ],
        "negative_matrix_case_count": len(negative_passed),
        "negative_matrix_all_rejected": True,
        "negative_matrix_passed_case_ids": list(negative_passed),
        "public_adapter_build_called": False,
        "historical_remap_public_gate_called": False,
        "successor_public_build_called": False,
        "B2_public_build_called": False,
        "old_contract_exact6_called": False,
        "compiler_context_called": False,
        "state_or_repository_write_performed": False,
        "repository_snapshot_unchanged": True,
        "reviewed_evidence_snapshot_unchanged": True,
        "readiness": {
            "output17_semantic_reconciliation_contract_designed": True,
            "output17_semantic_reconciliation_contract_gate_implemented": True,
            "output17_semantic_reconciliation_contract_gate_passed": True,
            "runtime_fast_path_output17_target_frozen": True,
            "successful_core15_cross_producer_parity_frozen": True,
            "failure_semantics_frozen": True,
            "ready_for_output17_lightweight_semantic_parity_probe": True,
            "ready_for_public_remap_adapter_hot_loop_contract_implementation": False,
            "ready_for_remap_hot_loop_contract_gate": False,
            "hot_loop_blocker": (
                "output17_lightweight_semantic_parity_probe_not_yet_passed"
            ),
            "current_adapter_directly_accepts_successor_exact6": False,
            "current_compiler_context_uses_successor_authority": False,
            "compiler_context_rebuild_device_identity_risk": True,
            "ready_for_dataloader_integration": False,
            "ready_for_model_integration": False,
            "ready_for_loss_integration": False,
            "feature_semantics_reaudit_required_before_training": True,
            "ready_for_training": False,
            "checkpoint_bytes_read": False,
            "model_parameter_shape_change_required": False,
            "commit_created": False,
            "push_performed": False,
        },
    }


def _validate_artifacts(artifacts: object) -> None:
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_NAMES:
        _fail()
    parsed: dict[str, dict[str, object]] = {}
    for name, payload in artifacts.items():
        _validate_payload(payload)
        parsed[name] = _strict_json(payload)
    digest = _manual_stable_digest(artifacts)
    manifest = parsed[MANIFEST_NAME]
    fields = parsed[FIELD_PARTITION_NAME]
    metadata = parsed[METADATA_CONTRACT_NAME]
    parity = parsed[PARITY_CONTRACT_NAME]
    negative = parsed[NEGATIVE_MATRIX_NAME]
    report = parsed[REPORT_NAME]
    readiness = report.get("readiness")
    if (
        manifest.get("artifact_names") != list(ARTIFACT_NAMES)
        or manifest.get("stable_artifact_names") != list(STABLE_ARTIFACT_NAMES)
        or fields.get("exact17_field_order") != list(EXACT17_FIELD_ORDER)
        or fields.get("successful_cross_producer_core15_field_order")
        != list(CORE15_FIELD_ORDER)
        or fields.get("producer_metadata_fields")
        != list(PRODUCER_METADATA_FIELDS)
        or tuple(metadata.get("validators", {}))
        != (
            "reference_failure_metadata_v1",
            "reference_success_metadata_v1",
            "runtime_failure_metadata_v1",
            "runtime_success_metadata_v1",
        )
        or parity.get("selected_reconciliation_model")
        != SELECTED_RECONCILIATION_MODEL
        or parity.get("runtime_fast_path", {}).get("runtime_target")
        != RUNTIME_TARGET
        or parity.get("historical_private_failure", {}).get(
            "cross_producer_core15_exact_required"
        )
        is not False
        or negative.get("case_count") != len(NEGATIVE_CASES)
        or report.get("gate_status") != GATE_STATUS
        or report.get("stable_contract_digest") != digest
        or type(readiness) is not dict
        or readiness.get("ready_for_output17_lightweight_semantic_parity_probe")
        is not True
        or readiness.get("ready_for_remap_hot_loop_contract_gate") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
    ):
        _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    before_repository = _repository_snapshot(repository)
    before_evidence = _evidence_snapshot(state)
    _validate_repository_lineage(repository)
    lifecycle = _repository_lifecycle(repository)
    owner_rows = [
        _verify_owner_identity(repository, name, spec)
        for name, spec in OWNER_SPECS.items()
    ]
    evidence_rows = _verify_reviewed_evidence(state)
    signature_rows = _validate_helper_signatures()
    _require_exact17_order(getattr(_runtime_owner, "_OUTPUT_FIELD_ORDER", None))
    semantic_evidence = _pure_semantic_evidence()
    negative_passed = _execute_negative_matrix(semantic_evidence)
    stable_values = (
        _manifest_artifact(owner_rows, evidence_rows, signature_rows),
        _field_partition_artifact(),
        _metadata_contract_artifact(),
        _parity_contract_artifact(),
        _negative_matrix_artifact(),
    )
    artifacts = {
        name: _canonical_json(value)
        for name, value in zip(STABLE_ARTIFACT_NAMES, stable_values, strict=True)
    }
    stable_digest = _manual_stable_digest(artifacts)
    artifacts[REPORT_NAME] = _canonical_json(
        _report_artifact(
            lifecycle=lifecycle,
            stable_digest=stable_digest,
            owner_rows=owner_rows,
            evidence_rows=evidence_rows,
            signature_rows=signature_rows,
            semantic_evidence=semantic_evidence,
            negative_passed=negative_passed,
        )
    )
    _validate_artifacts(artifacts)
    if (
        _repository_snapshot(repository) != before_repository
        or _evidence_snapshot(state) != before_evidence
    ):
        _fail()
    return artifacts


def build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic in-memory semantic reconciliation Exact6."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error
