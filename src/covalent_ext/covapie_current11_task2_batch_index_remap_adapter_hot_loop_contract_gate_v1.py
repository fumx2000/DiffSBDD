"""Freeze the Current11 Task2 remap adapter hot-loop contract V1."""

from __future__ import annotations

import hashlib
import inspect
import json
import stat
import subprocess
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as _adapter_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
    as _reconciliation_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_predecessor_successor_v1
    as _successor_owner,
)


__all__ = (
    "build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
    "contract_gate_v1",
)

ERROR_TOKEN = (
    "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_HOT_LOOP_"
    "CONTRACT_GATE_V1_ERROR"
)
GATE_STATUS = "PASS_REMAP_ADAPTER_HOT_LOOP_CONTRACT_ONLY"
BASE_COMMIT = "03e9a238d0c910257e4f43a78c69998dc62dd162"
BRANCH = "main"

MODULE_PATH = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_"
    "hot_loop_contract_gate_v1.py"
)
SCRIPT_PATH = (
    "scripts/check_covapie_current11_task2_batch_index_remap_adapter_"
    "hot_loop_contract_gate_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
    "contract_gate_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
    "contract_gate_v1_guide.md"
)
REPOSITORY_EXACT4 = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)

MANIFEST_NAME = (
    "current11_task2_batch_index_remap_adapter_hot_loop_manifest.json"
)
CONTEXT_CONTRACT_NAME = (
    "current11_task2_batch_index_remap_adapter_hot_loop_context_contract.json"
)
RUNTIME_CONTRACT_NAME = (
    "current11_task2_batch_index_remap_adapter_hot_loop_runtime_contract.json"
)
AUTHORITY_CONTRACT_NAME = (
    "current11_task2_batch_index_remap_adapter_hot_loop_authority_and_"
    "freshness_contract.json"
)
NEGATIVE_MATRIX_NAME = (
    "current11_task2_batch_index_remap_adapter_hot_loop_negative_matrix.json"
)
REPORT_NAME = (
    "current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_"
    "report.json"
)
ARTIFACT_NAMES = (
    MANIFEST_NAME,
    CONTEXT_CONTRACT_NAME,
    RUNTIME_CONTRACT_NAME,
    AUTHORITY_CONTRACT_NAME,
    NEGATIVE_MATRIX_NAME,
    REPORT_NAME,
)
STABLE_ARTIFACT_NAMES = ARTIFACT_NAMES[:5]
STABLE_DIGEST_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_HOT_LOOP_"
    b"CONTRACT_GATE_V1\0"
)

ARCHITECTURE_NAME = (
    "explicit_successor_authority_context_plus_output17_only_no_io_"
    "fast_path_v1"
)
RUNTIME_TARGET = "current_public_adapter_output17_v1"
SELECTED_RECONCILIATION_MODEL = (
    "B_plus_E_success_plus_runtime_whole_failure_exact_plus_historical_"
    "failure_self_validation"
)
RECONCILIATION_STABLE_DIGEST = (
    "9250ff7948d353222f7a2c5b34fdfceee92ae03b73be802af80a214db004203f"
)
SUCCESSOR_STABLE5_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)
CONTEXT_FRESHNESS_MODEL = "explicit_rebuild_by_owner"
CONTEXT_BUILD_FREQUENCY = (
    "once_per_process_or_ddp_rank_per_authority_snapshot"
)

CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

FUTURE_PUBLIC_APIS = (
    {
        "name": (
            "build_covapie_current11_task2_batch_index_remap_adapter_"
            "context_v1"
        ),
        "signature": "(*, repo_root: Path, state_root: Path) -> object",
        "keyword_only": True,
        "return_contract": "opaque_context_object",
    },
    {
        "name": (
            "remap_covapie_current11_task2_batch_index_with_context_v1"
        ),
        "signature": (
            "(*, context: object, adapter_input: dict[str, object]) -> "
            "dict[str, object]"
        ),
        "keyword_only": True,
        "return_contract": "built_in_output17_dict_only",
    },
)

FUTURE_CONTEXT_PRODUCT_EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_"
    "context_v1.py",
    "scripts/check_covapie_current11_task2_batch_index_remap_adapter_"
    "context_v1.py",
    "tests/test_covapie_current11_task2_batch_index_remap_adapter_context_"
    "v1.py",
    "docs/covapie_current11_task2_batch_index_remap_adapter_context_v1_"
    "guide.md",
)

LOGICAL_CONTEXT_FIELD_ORDER = (
    "context_schema_version",
    "context_contract_version",
    "runtime_output17_target",
    "reconciliation_contract_digest",
    "successor_stable5_digest",
    "remap_contract_digest",
    "projection_instance_digest",
    "payload_bundle_digest",
    "projection_contract_digest",
    "join_contract",
    "index_space_order",
    "input_field_order",
    "input_required_fields",
    "input_optional_fields",
    "output17_field_order",
    "source_contract",
    "authority_tables",
    "formal_authority_identity",
    "context_freshness_model",
    "construction_seal",
)

INPUT_FIELD_ORDER = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "parser_schema_version",
    "collate_schema_version",
    "source_sample_order",
    "source_pair_values_int64",
    "source_sample_offsets_int64",
    "source_entry_validity_bool",
    "source_sample_validity_bool",
    "batch_sample_order",
    "batch_sample_atom_identity_tables",
    "batch_role_lengths",
    "batch_role_offsets",
    "batch_membership_masks",
    "joint_layout_descriptor",
    "debug_coordinates",
    "debug_rank_metadata",
)
INPUT_REQUIRED_FIELDS = INPUT_FIELD_ORDER[:15]
INPUT_OPTIONAL_FIELDS = INPUT_FIELD_ORDER[15:]
LEGACY_INPUT_ALIASES = (
    "source_entry_validity",
    "source_pair_values",
    "source_sample_offsets",
    "source_sample_validity",
)
OUTPUT17_FIELD_ORDER = (
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

ADAPTER_PURE_HELPER_SIGNATURES = {
    "_validate_source_contract": (
        "(case: 'Mapping[str, object]', source: 'Mapping[str, object]', "
        "authority: 'Sequence[Mapping[str, object]]') -> 'None'"
    ),
    "_remap_engine": (
        "(case: 'dict[str, object]', *, authoritative_tables: "
        "'list[dict[str, object]]') -> 'dict[str, object]'"
    ),
    "_failure_output": (
        "(case: 'Mapping[str, object]', status: 'str', source_pair_count: "
        "'int', entry_index: 'int') -> 'dict[str, object]'"
    ),
    "_validate_output": "(output: 'dict[str, object]') -> 'None'",
    "_provenance": (
        "(joint_status: 'str', descriptor: 'object') -> 'dict[str, object]'"
    ),
    "_readiness": "(success: 'bool') -> 'dict[str, bool]'",
}
SUCCESSOR_PARSE_HELPER_SIGNATURES = {
    "_strict_json": "(payload: 'bytes') -> 'dict[str, object]'",
    "_csv_rows": (
        "(payload: 'bytes') -> "
        "'tuple[tuple[str, ...], list[dict[str, str]]]'"
    ),
    "_derive_role_authority": (
        "(role: 'Mapping[str, object]') -> 'dict[str, object]'"
    ),
    "_identity_complete": "(identity: 'object') -> 'bool'",
    "_identity_key": (
        "(identity: 'Mapping[str, object]') -> 'tuple[object, ...]'"
    ),
}

FORMAL_AUTHORITY_IDENTITY = {
    "canonical_relative_path": (
        "formal-sidecars/current11-dataset-partial-supervision-routing-"
        "sidecar-v1"
    ),
    "canonical_readlink": (
        ".current11-dataset-partial-supervision-routing-sidecar-v2.object-"
        "sha256-24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
        "1fd8cf5823427e941b11c7b2560a336f"
    ),
    "formal_aggregate_sha256": (
        "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
    ),
    "formal_snapshot_sha256": (
        "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
    ),
    "formal_exact4_sha256": {
        "current11_dataset_partial_supervision_routing_manifest.json": (
            "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d"
        ),
        "current11_dataset_partial_supervision_routing_records.csv": (
            "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03"
        ),
        "current11_dataset_partial_supervision_sample_coverage.csv": (
            "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e"
        ),
        "current11_dataset_partial_supervision_task_coverage.csv": (
            "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7"
        ),
    },
}

OWNER_SPECS = {
    "published_output17_reconciliation_gate": {
        "path": (
            "src/covalent_ext/covapie_current11_task2_batch_index_remap_"
            "output17_semantic_reconciliation_contract_gate_v1.py"
        ),
        "bytes": 67867,
        "LF": 1793,
        "sha256": (
            "15f639ef955a975cbfbeebce9bde452ee65d4acdf67b2feec56871786603e1de"
        ),
        "git_blob": "edac625388b8c58539c3c29a5dd470d6ccec6e6e",
        "commit": BASE_COMMIT,
        "subject": (
            "add CovaPIE Current11 Task2 Output17 semantic reconciliation "
            "contract v1"
        ),
    },
    "published_remap_predecessor_successor": {
        "path": (
            "src/covalent_ext/covapie_current11_task2_batch_index_remap_"
            "predecessor_successor_v1.py"
        ),
        "bytes": 43997,
        "LF": 1203,
        "sha256": (
            "c1e4b207a6432b6495d85fb799a196cb2370edd41402000fbfcbfcf3514acb05"
        ),
        "git_blob": "0e0ebdca4db0abbfaec921ea34253dcefbb29410",
        "commit": "cd392246fc424de609db9c5110d805fbe3d9a555",
        "subject": (
            "add CovaPIE Current11 Task2 remap predecessor successor v1"
        ),
    },
    "current_public_runtime_adapter": {
        "path": (
            "src/covalent_ext/covapie_current11_task2_batch_index_remap_"
            "adapter_v1.py"
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
    "historical_remap_contract_reference_owner": {
        "path": (
            "src/covalent_ext/covapie_current11_task2_batch_index_remap_"
            "contract_gate_v1.py"
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
}

REVIEWED_EVIDENCE_SPECS = {
    "output17_lightweight_semantic_parity_probe": {
        "relative_path": (
            "review-scratch/current11-task2-remap-output17-lightweight-"
            "semantic-parity-v1/remap_output17_lightweight_semantic_parity_"
            "probe_report.md"
        ),
        "bytes": 8454,
        "LF": 139,
        "sha256": (
            "ea108ff4f501a1d7b0f4053399a2c8e73364948c0d101955dc5a1939d12c51cc"
        ),
        "required_markers": (
            "output17_lightweight_semantic_parity_probe_passed: true",
            "ready_for_remap_hot_loop_contract_gate: true",
            f"stable_contract_digest: `{RECONCILIATION_STABLE_DIGEST}`",
            f"runtime_target: `{RUNTIME_TARGET}`",
            "| synthetic joint | true | true | false |",
            "| synthetic no-joint | true | true | false |",
            "| synthetic subset | true | true | false |",
            "schema mismatch exact Core15 difference fields:",
            "runtime hard-failure entry index: 2",
            "failure_normalization_performed: false",
        ),
    },
    "successor_adapter_parity_timing_probe": {
        "relative_path": (
            "review-scratch/current11-task2-remap-successor-adapter-parity-"
            "timing-v1/remap_successor_adapter_parity_timing_report.md"
        ),
        "bytes": 15200,
        "LF": 218,
        "sha256": (
            "6425ade470cf12be31b367062f4612e634160e5611e665bc98f4efe17c667c79"
        ),
        "required_markers": (
            f"Historical stable5 framed digest: `{SUCCESSOR_STABLE5_DIGEST}`",
            "`cached_formal_output_parity_passed=true`",
            "`C_D_Output17_byte_identical=true`",
            "`C_D_Output17_deep_equal=true`",
            "`old_adapter_report_authoritative_for_successor_probe=false`",
            "C: cached successor + real formal",
            "D: cached successor + cached formal",
        ),
    },
    "output17_semantic_reconciliation_design": {
        "relative_path": (
            "review-scratch/current11-task2-remap-output17-semantic-"
            "reconciliation-design-v1/remap_output17_semantic_"
            "reconciliation_design_report.md"
        ),
        "bytes": 31207,
        "LF": 552,
        "sha256": (
            "e597dc7605e504b3d0c9a81b930c0dd6ea14b869380f2bebb6654564bfdc0f30"
        ),
        "required_markers": (
            f"runtime_fast_path_output17_target = {RUNTIME_TARGET}",
            "B + E_success + runtime_whole_failure_exact + "
            "historical_failure_self_validation",
            "must whole-Output17 exact-match current public adapter failure",
            "The fast path must not depend on or emit the old adapter report.",
        ),
    },
}

NEGATIVE_CASES = (
    ("context_api_positional_expansion", "future context API accepts positional arguments"),
    ("fast_api_positional_expansion", "future fast API accepts positional arguments"),
    ("third_public_function_added", "future product exports a third public function"),
    ("public_context_class_exposed", "future product exposes its context class"),
    ("current_adapter_source_modified", "frozen current adapter source identity changes"),
    ("current_adapter_public_api_modified", "frozen current adapter public API changes"),
    ("old_adapter_exact2_semantics_modified", "current slow adapter Exact2 semantics change"),
    ("full_remap_algorithm_copied", "future module copies the full remap algorithm"),
    ("second_status_precedence", "future module defines another status precedence"),
    ("global_cache_added", "module-global context cache is added"),
    ("lru_cache_added", "LRU caching is added"),
    ("singleton_context_added", "hidden singleton context is added"),
    ("pickle_contract_claimed", "V1 claims a pickle contract"),
    ("context_seal_missing", "context construction seal is absent"),
    ("context_version_mismatch", "fast call accepts a context version mismatch"),
    ("context_authority_digest_mismatch", "fast call accepts an authority digest mismatch"),
    ("successor_stable5_digest_mismatch", "successor stable5 digest differs"),
    ("reconciliation_digest_mismatch", "reconciliation digest differs"),
    ("runtime_target_mismatch", "runtime Output17 target differs"),
    ("source_or_authority_tamper", "source contract or authority tables are altered"),
    ("context_mutation_silently_accepted", "caller-visible context mutation is accepted"),
    ("fast_calls_successor", "fast call invokes successor acquisition"),
    ("fast_calls_reconciliation", "fast call invokes reconciliation acquisition"),
    ("fast_calls_b2", "fast call invokes B2 transition authority"),
    ("fast_calls_contract_exact6", "fast call invokes adapter _contract_exact6"),
    ("fast_calls_old_parse_contract", "fast call invokes adapter _parse_contract"),
    ("fast_calls_validate_formal", "fast call invokes adapter _validate_formal"),
    ("fast_filesystem_read", "fast call reads the filesystem"),
    ("fast_git_or_subprocess", "fast call invokes Git or subprocess"),
    ("fast_report_returned", "fast call returns the old adapter report or a new report"),
    ("fast_artifact_write", "fast call writes an artifact"),
    ("output17_field_reorder", "fast output changes Exact17 field order"),
    ("fast_success_differs", "fast success differs from current adapter Output17"),
    ("fast_failure_differs", "fast failure differs from current adapter Output17"),
    ("historical_failure_runtime_golden", "historical private failure becomes runtime golden"),
    ("failure_normalization", "failure offsets, validity, placement, absent, or null are normalized"),
    ("historical_metadata_copied_to_runtime", "reference-only metadata enters runtime output"),
    ("caller_input_mutated", "fast call mutates adapter_input"),
    ("context_auto_refresh", "fast call silently refreshes or rebuilds context"),
    ("per_batch_freshness_filesystem", "per-batch freshness filesystem polling is added"),
    ("stale_context_currentness_claim", "stale context claims current filesystem validation"),
    ("absolute_latency_sla", "an absolute millisecond SLA is imposed"),
    ("dataloader_ready_true", "DataLoader integration readiness becomes true"),
    ("model_ready_true", "model integration readiness becomes true"),
    ("loss_ready_true", "loss integration readiness becomes true"),
    ("feature_reaudit_false", "feature-semantics re-audit requirement becomes false"),
    ("training_ready_true", "training readiness becomes true"),
    ("canonical_mask_contract_changed", "a sixth mask is added or scaffold_only/B3 is omitted"),
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


def _safe_exact4(repo_root: Path) -> None:
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
        _safe_exact4(repo_root)
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
    _safe_exact4(repo_root)
    return "clean-tracked-successor"


def _path_item(path: Path) -> tuple[object, ...]:
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
    paths = (
        *REPOSITORY_EXACT4,
        *(str(spec["path"]) for spec in OWNER_SPECS.values()),
    )
    return (
        _run_git(
            repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
        ),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple((relative, _path_item(repo_root / relative)) for relative in paths),
    )


def _evidence_snapshot(state_root: Path) -> tuple[object, ...]:
    return tuple(
        (
            str(spec["relative_path"]),
            _path_item(state_root / str(spec["relative_path"])),
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


def _verify_reviewed_evidence(state_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for evidence_name, spec in REVIEWED_EVIDENCE_SPECS.items():
        relative = str(spec["relative_path"])
        path = state_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
            text = payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise _ContractInvariantError() from error
        markers = tuple(str(marker) for marker in spec["required_markers"])
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or len(payload) != spec["bytes"]
            or payload.count(b"\n") != spec["LF"]
            or _sha256(payload) != spec["sha256"]
            or any(marker not in text for marker in markers)
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
                "required_marker_count": len(markers),
                "all_required_markers_present": True,
                "reviewed_evidence_only": True,
                "sole_semantic_authority": False,
            }
        )
    return rows


def _signature_rows(
    expected: Mapping[str, str],
    *,
    purpose: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for helper_name, expected_signature in expected.items():
        helper = getattr(_adapter_owner, helper_name, None)
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
                "helper_name": helper_name,
                "signature": observed,
                "purpose": purpose,
                "owner": "current_public_runtime_adapter",
            }
        )
    return rows


def _validate_adapter_contract() -> dict[str, object]:
    pure_rows = _signature_rows(
        ADAPTER_PURE_HELPER_SIGNATURES,
        purpose="future_fast_path_pure_helper_reuse",
    )
    parser_rows = _signature_rows(
        SUCCESSOR_PARSE_HELPER_SIGNATURES,
        purpose="future_context_successor_stable5_parser_reuse",
    )
    try:
        reconciliation_signature = str(
            inspect.signature(
                _reconciliation_owner.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
            )
        )
        successor_signature = str(
            inspect.signature(
                _successor_owner.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1
            )
        )
    except (TypeError, ValueError) as error:
        raise _ContractInvariantError() from error
    expected_public_signature = (
        "(*, repo_root: 'Path', state_root: 'Path') -> 'dict[str, bytes]'"
    )
    formal = {
        "canonical_relative_path": getattr(_adapter_owner, "_FORMAL_RELATIVE", None),
        "canonical_readlink": getattr(_adapter_owner, "_FORMAL_READLINK", None),
        "formal_aggregate_sha256": getattr(_adapter_owner, "_FORMAL_AGGREGATE", None),
        "formal_snapshot_sha256": getattr(
            _adapter_owner, "_FORMAL_SNAPSHOT_SHA256", None
        ),
        "formal_exact4_sha256": getattr(_adapter_owner, "_FORMAL_FILES", None),
    }
    if (
        reconciliation_signature != expected_public_signature
        or successor_signature != expected_public_signature
        or getattr(_reconciliation_owner, "RUNTIME_TARGET", None)
        != RUNTIME_TARGET
        or getattr(_reconciliation_owner, "SELECTED_RECONCILIATION_MODEL", None)
        != SELECTED_RECONCILIATION_MODEL
        or tuple(getattr(_reconciliation_owner, "EXACT17_FIELD_ORDER", ()))
        != OUTPUT17_FIELD_ORDER
        or getattr(_successor_owner, "REMAP_STABLE5_DIGEST", None)
        != SUCCESSOR_STABLE5_DIGEST
        or tuple(getattr(_adapter_owner, "_INPUT_FIELD_ORDER", ()))
        != INPUT_FIELD_ORDER
        or frozenset(getattr(_adapter_owner, "_INPUT_REQUIRED", ()))
        != frozenset(INPUT_REQUIRED_FIELDS)
        or frozenset(getattr(_adapter_owner, "_INPUT_OPTIONAL", ()))
        != frozenset(INPUT_OPTIONAL_FIELDS)
        or tuple(sorted(getattr(_adapter_owner, "_LEGACY_ALIASES", ())))
        != LEGACY_INPUT_ALIASES
        or tuple(getattr(_adapter_owner, "_OUTPUT_FIELD_ORDER", ()))
        != OUTPUT17_FIELD_ORDER
        or formal != FORMAL_AUTHORITY_IDENTITY
    ):
        _fail()
    return {
        "pure_helper_rows": pure_rows,
        "successor_parser_helper_rows": parser_rows,
        "reconciliation_public_signature": reconciliation_signature,
        "successor_public_signature": successor_signature,
        "input_field_order": list(INPUT_FIELD_ORDER),
        "input_required_fields": list(INPUT_REQUIRED_FIELDS),
        "input_optional_fields": list(INPUT_OPTIONAL_FIELDS),
        "legacy_input_aliases": list(LEGACY_INPUT_ALIASES),
        "output17_field_order": list(OUTPUT17_FIELD_ORDER),
        "adapter_error_token": getattr(_adapter_owner, "_ERROR", None),
        "input_failure_exception": "_InputFailure",
        "status_precedence_owner": "current_public_runtime_adapter._STATUS_ORDER",
        "formal_authority_identity": FORMAL_AUTHORITY_IDENTITY,
    }


def _manifest_artifact(
    owner_rows: Sequence[Mapping[str, object]],
    evidence_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "contract_v1"
        ),
        "artifact_names": list(ARTIFACT_NAMES),
        "stable_artifact_names": list(STABLE_ARTIFACT_NAMES),
        "stable_digest_domain_ascii_nul_terminated": (
            "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_HOT_LOOP_"
            "CONTRACT_GATE_V1\\0"
        ),
        "stable_digest_framing": (
            "uint64be_name_length_name_uint64be_payload_length_payload"
        ),
        "report_self_excluded_from_stable_digest": True,
        "architecture_name": ARCHITECTURE_NAME,
        "base_commit": BASE_COMMIT,
        "runtime_target": RUNTIME_TARGET,
        "reconciliation_lineage": {
            "stable_digest": RECONCILIATION_STABLE_DIGEST,
            "selected_model": SELECTED_RECONCILIATION_MODEL,
            "runtime_target": RUNTIME_TARGET,
        },
        "successor_lineage": {
            "stable5_digest": SUCCESSOR_STABLE5_DIGEST,
            "historical_report_required": False,
            "successor_report_required": True,
        },
        "production_owner_identities": [dict(row) for row in owner_rows],
        "reviewed_evidence_identities": [dict(row) for row in evidence_rows],
        "reviewed_evidence_is_sole_semantic_authority": False,
        "canonical_mask_semantics": [
            {"semantic_name": semantic, "display_alias": alias}
            for semantic, alias in CANONICAL_MASKS
        ],
        "canonical_mask_count": len(CANONICAL_MASKS),
        "canonical_masks_modified": False,
        "existing_slow_public_adapter_source_unchanged": True,
        "existing_slow_public_adapter_api_unchanged": True,
        "existing_slow_public_adapter_exact2_semantics_unchanged": True,
        "adapter_source_refactor_required": False,
        "shared_kernel_refactor_required": False,
        "full_remap_algorithm_copy_forbidden": True,
        "fast_path_reuses_frozen_adapter_private_pure_helpers": True,
        "global_cache_forbidden": True,
        "lru_cache_forbidden": True,
        "hidden_singleton_context_forbidden": True,
        "pickle_contract_defined": False,
        "context_build_frequency": CONTEXT_BUILD_FREQUENCY,
        "context_freshness_model": CONTEXT_FRESHNESS_MODEL,
        "per_batch_freshness_filesystem_check": False,
        "supported_repository_lifecycles": [
            "precommit-untracked",
            "clean-tracked-successor",
        ],
        "contract_gate_only": True,
        "future_context_or_runtime_product_implemented": False,
        "public_or_heavy_predecessor_product_called": False,
    }


def _context_contract_artifact(
    adapter_contract: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "context_contract_v1"
        ),
        "future_product_public_api_exact2": [dict(row) for row in FUTURE_PUBLIC_APIS],
        "future_product_public_api_count": len(FUTURE_PUBLIC_APIS),
        "future_product___all___exact2": [row["name"] for row in FUTURE_PUBLIC_APIS],
        "public_context_class_allowed": False,
        "future_context_product_exact4": list(FUTURE_CONTEXT_PRODUCT_EXACT4),
        "future_context_product_path_count": len(FUTURE_CONTEXT_PRODUCT_EXACT4),
        "logical_context_field_order": list(LOGICAL_CONTEXT_FIELD_ORDER),
        "logical_context_field_count": len(LOGICAL_CONTEXT_FIELD_ORDER),
        "logical_fields_need_not_be_public_python_attributes": True,
        "context_semantics": {
            "opaque": True,
            "caller_not_inspect_for_contract": True,
            "tamper_evident": True,
            "semantically_immutable": True,
            "deep_immutable_representation_required": True,
            "public_writable_mutation_interface": False,
            "caller_semantic_mutation_allowed": False,
            "fast_validates_type_version_and_seal": True,
            "altered_or_corrupted_context_fails_closed": True,
            "construction_seal_covers_all_semantic_payload": True,
        },
        "clean_tracked_successor_authority_acquisition": {
            "reconciliation_public_build_count": 1,
            "successor_public_build_count": 1,
            "successor_internal_B2_public_build_count": 1,
            "context_builder_direct_B2_public_build_count": 0,
            "adapter_contract_exact6_count": 0,
            "historical_remap_public_gate_count": 0,
            "historical_payload_builder_count": 0,
            "historical_instance_builder_count": 0,
            "reconciliation_stable_digest_required": RECONCILIATION_STABLE_DIGEST,
            "successor_stable5_digest_required": SUCCESSOR_STABLE5_DIGEST,
            "runtime_target_required": RUNTIME_TARGET,
            "selected_reconciliation_model_required": SELECTED_RECONCILIATION_MODEL,
            "synthetic_historical_report_created": False,
        },
        "formal_build_time_validation": {
            "adapter_validate_formal_before_count": 1,
            "adapter_validate_formal_after_count": 1,
            "formal_before_must_equal_formal_after": True,
            "formal_identity": adapter_contract["formal_authority_identity"],
            "mount_id_is_semantic_identity": False,
            "parent_mount_id_is_semantic_identity": False,
            "mtime_is_semantic_identity": False,
            "pid_is_semantic_identity": False,
        },
        "successor_stable5_parser": {
            "owned_by_future_context_module": True,
            "adapter_old_parse_contract_called": False,
            "historical_old_report_required": False,
            "synthetic_old_report_created": False,
            "successor_report_independently_validated": True,
            "reused_low_level_helpers": [
                dict(row)
                for row in adapter_contract["successor_parser_helper_rows"]
            ],
            "validation_coverage": [
                "schemas_and_field_order",
                "required_and_optional_input_fields",
                "status_header_order_codes_and_hard_failures",
                "join_contract_and_four_index_spaces",
                "placeholder_semantics",
                "projection_payload_and_projection_contract_digests",
                "formal_snapshot_sha_and_formal_aggregate",
                "source_pairs_offsets_and_validity",
                "exact11_sample_order",
                "exact22_authority_roles",
                "selected_atom_identities",
            ],
        },
        "repository_lifecycle_contract": {
            "precommit_untracked": {
                "real_public_context_builder_required_to_succeed": False,
                "test_harness_exact_predecessor_artifact_injection_allowed": True,
                "fixture_unit_and_candidate_only_validation": True,
                "production_monkeypatch_allowed": False,
                "production_git_status_hiding_allowed": False,
                "predecessor_modification_allowed": False,
            },
            "clean_tracked_successor": {
                "real_reconciliation_public_build_once_required": True,
                "real_successor_public_build_once_required": True,
                "real_context_public_build_live_proof_required": True,
            },
        },
        "cache_and_lifetime": {
            "global_registry_allowed": False,
            "global_cache_allowed": False,
            "lru_cache_allowed": False,
            "hidden_mutable_cache_allowed": False,
            "hidden_singleton_context_allowed": False,
            "cross_process_shared_cache_allowed": False,
            "context_build_frequency": CONTEXT_BUILD_FREQUENCY,
            "context_freshness_model": CONTEXT_FRESHNESS_MODEL,
            "context_auto_refresh": False,
            "pickle_contract_defined": False,
        },
    }


def _runtime_contract_artifact(
    adapter_contract: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "runtime_contract_v1"
        ),
        "future_fast_public_api": dict(FUTURE_PUBLIC_APIS[1]),
        "fast_return_contract": {
            "built_in_output17_dict_only": True,
            "logical_output_object_count": 1,
            "adapter_report_returned": False,
            "successor_report_returned": False,
            "contract_report_returned": False,
            "exact2_bytes_bundle_returned": False,
            "new_fast_report_defined": False,
        },
        "runtime_target": RUNTIME_TARGET,
        "output17_field_order": list(OUTPUT17_FIELD_ORDER),
        "output17_field_count": len(OUTPUT17_FIELD_ORDER),
        "same_exact_input_success_whole_output17_canonical_bytes_exact": True,
        "same_exact_input_failure_whole_output17_canonical_bytes_exact": True,
        "provenance_readiness_offsets_validity_null_and_bool_int_exact": True,
        "historical_private_failure_runtime_golden": False,
        "failure_normalization_forbidden": True,
        "old_adapter_report_returned_by_fast_path": False,
        "old_adapter_report_authoritative_for_fast_path": False,
        "input_contract": {
            "field_order": adapter_contract["input_field_order"],
            "required_fields": adapter_contract["input_required_fields"],
            "optional_fields": adapter_contract["input_optional_fields"],
            "legacy_aliases_forbidden": adapter_contract["legacy_input_aliases"],
            "invalid_adapter_input_type_fails_closed": True,
            "exact_schema_precheck_uses_frozen_adapter_field_sets": True,
            "caller_input_preserved": True,
        },
        "context_contract": {
            "validate_type_version_and_seal_first": True,
            "context_mutation_forbidden": True,
            "context_rebuild_or_refresh_during_fast_call": False,
        },
        "orchestration": {
            "frozen_adapter_private_pure_helper_rows": [
                dict(row) for row in adapter_contract["pure_helper_rows"]
            ],
            "frozen_adapter_private_pure_helper_count": len(
                adapter_contract["pure_helper_rows"]
            ),
            "full_remap_algorithm_copy_forbidden": True,
            "second_status_precedence_implementation_forbidden": True,
            "adapter_input_failure_exception": adapter_contract[
                "input_failure_exception"
            ],
            "adapter_error_token": adapter_contract["adapter_error_token"],
            "status_precedence_owner": adapter_contract[
                "status_precedence_owner"
            ],
        },
        "fast_per_batch_structural_acceptance_counts": {
            "reconciliation_public_build_count": 0,
            "successor_public_build_count": 0,
            "B2_public_build_count": 0,
            "historical_contract_public_gate_count": 0,
            "adapter_contract_exact6_count": 0,
            "adapter_parse_contract_count": 0,
            "adapter_validate_formal_count": 0,
            "formal_filesystem_read_count": 0,
            "other_filesystem_read_count": 0,
            "git_call_count": 0,
            "subprocess_call_count": 0,
            "report_generation_count": 0,
            "artifact_write_count": 0,
            "global_cache_lookup_count": 0,
            "context_rebuild_count": 0,
        },
        "performance_boundary": {
            "absolute_latency_SLA_defined": False,
            "benchmark_loop_required": False,
            "one_shot_ms_threshold_forbidden": True,
            "acceptance_is_structural_not_millisecond_threshold": True,
            "reviewed_timing_is_directional_evidence_only": True,
        },
    }


def _authority_contract_artifact(
    adapter_contract: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "authority_and_freshness_contract_v1"
        ),
        "reconciliation_contract_digest": RECONCILIATION_STABLE_DIGEST,
        "successor_stable5_digest": SUCCESSOR_STABLE5_DIGEST,
        "runtime_output17_target": RUNTIME_TARGET,
        "selected_reconciliation_model": SELECTED_RECONCILIATION_MODEL,
        "formal_authority_identity": adapter_contract["formal_authority_identity"],
        "formal_identity_excludes": [
            "mount_id",
            "parent_mount_id",
            "mtime",
            "pid",
        ],
        "source_contract_and_authority_tables_derive_from_successor_stable5": True,
        "historical_old_report_present_in_context": False,
        "successor_report_independently_validated": True,
        "device_transition_authority_owned_by_successor_B2_chain": True,
        "context_does_not_reinvent_device_policy": True,
        "context_freshness_model": CONTEXT_FRESHNESS_MODEL,
        "context_build_frequency": CONTEXT_BUILD_FREQUENCY,
        "context_build_does_not_auto_refresh": True,
        "fast_path_silent_rebuild_or_refresh": False,
        "per_batch_freshness_filesystem_check": False,
        "stale_context_semantics": (
            "context remains bound to its construction authority snapshot; "
            "the owner must explicitly rebuild it and fast calls make no "
            "current-filesystem or current-successor revalidation claim"
        ),
        "context_provenance_scope": "context_construction_authority_snapshot",
        "one_context_per_process_or_ddp_rank_per_authority_snapshot": True,
        "current_adapter_directly_accepts_successor_exact6": False,
        "current_compiler_context_uses_successor_authority": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "compiler_context_integration_performed": False,
    }


def _negative_matrix_artifact() -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "negative_matrix_v1"
        ),
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


def _readiness(lifecycle: str) -> dict[str, object]:
    if lifecycle not in (
        "precommit-untracked",
        "clean-tracked-successor",
    ):
        _fail()
    published = lifecycle == "clean-tracked-successor"
    return {
        "remap_adapter_hot_loop_contract_designed": True,
        "remap_adapter_hot_loop_contract_gate_implemented": True,
        "remap_adapter_hot_loop_contract_gate_passed": True,
        "architecture_frozen": True,
        "future_context_api_frozen": True,
        "future_fast_output17_target_frozen": True,
        "fast_no_io_structural_contract_frozen": True,
        "context_freshness_contract_frozen": True,
        "ready_for_remap_adapter_hot_loop_contract_gate_commit_review": True,
        "ready_for_remap_adapter_context_runtime_implementation": published,
        "context_runtime_blocker": (
            "NONE" if published else "hot_loop_contract_gate_not_published"
        ),
        "ready_for_public_remap_adapter_hot_loop_contract_implementation": False,
        "current_adapter_directly_accepts_successor_exact6": False,
        "current_compiler_context_uses_successor_authority": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "step12d_smoke_is_final_training_feature_contract": False,
        "ready_for_training": False,
        "checkpoint_bytes_read": False,
        "model_parameter_shape_change_required": False,
        "commit_created": False,
        "push_performed": False,
    }


def _report_artifact(
    *,
    lifecycle: str,
    stable_digest: str,
    owner_rows: Sequence[Mapping[str, object]],
    evidence_rows: Sequence[Mapping[str, object]],
    adapter_contract: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "contract_gate_report_v1"
        ),
        "gate_status": GATE_STATUS,
        "artifact_file_count": len(ARTIFACT_NAMES),
        "artifact_names": list(ARTIFACT_NAMES),
        "stable_artifact_count": len(STABLE_ARTIFACT_NAMES),
        "stable_contract_digest": stable_digest,
        "report_self_excluded_from_stable_digest": True,
        "repository_lifecycle": lifecycle,
        "architecture_name": ARCHITECTURE_NAME,
        "owner_identity_validation_passed": True,
        "owner_identities": [dict(row) for row in owner_rows],
        "reviewed_evidence_identity_validation_passed": True,
        "reviewed_evidence_identities": [dict(row) for row in evidence_rows],
        "reconciliation_stable_digest_evidence_validated": True,
        "successor_stable5_digest_evidence_validated": True,
        "runtime_target_validated": RUNTIME_TARGET,
        "selected_reconciliation_model_validated": SELECTED_RECONCILIATION_MODEL,
        "lightweight_success_case_count": 3,
        "lightweight_failure_case_count": 2,
        "lightweight_semantic_parity_probe_passed": True,
        "one_heavy_cached_authority_C_and_D_ran": True,
        "one_heavy_formal_caching_output17_unchanged": True,
        "one_heavy_old_report_authoritative": False,
        "frozen_adapter_private_pure_helper_count": len(
            adapter_contract["pure_helper_rows"]
        ),
        "frozen_adapter_private_pure_helper_rows": [
            dict(row) for row in adapter_contract["pure_helper_rows"]
        ],
        "successor_parser_low_level_helper_count": len(
            adapter_contract["successor_parser_helper_rows"]
        ),
        "exact17_field_order_validated": True,
        "negative_matrix_case_count": len(NEGATIVE_CASES),
        "negative_matrix_all_fail_closed": True,
        "current_adapter_source_unchanged": True,
        "reconciliation_source_unchanged": True,
        "successor_source_unchanged": True,
        "historical_remap_owner_unchanged": True,
        "reconciliation_public_build_count": 0,
        "successor_public_build_count": 0,
        "B2_public_build_count": 0,
        "current_adapter_public_build_count": 0,
        "historical_remap_public_gate_count": 0,
        "adapter_contract_exact6_count": 0,
        "one_heavy_probe_rerun": False,
        "lightweight_probe_rerun": False,
        "benchmark_or_timing_performed": False,
        "compiler_context_called": False,
        "state_or_repository_write_performed_by_gate": False,
        "repository_snapshot_unchanged": True,
        "reviewed_evidence_snapshot_unchanged": True,
        "readiness": _readiness(lifecycle),
    }


def _validate_artifacts(artifacts: object) -> None:
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_NAMES:
        _fail()
    parsed: dict[str, dict[str, object]] = {}
    for name, payload in artifacts.items():
        _validate_payload(payload)
        parsed[name] = _strict_json(payload)
    manifest = parsed[MANIFEST_NAME]
    context = parsed[CONTEXT_CONTRACT_NAME]
    runtime = parsed[RUNTIME_CONTRACT_NAME]
    authority = parsed[AUTHORITY_CONTRACT_NAME]
    negative = parsed[NEGATIVE_MATRIX_NAME]
    report = parsed[REPORT_NAME]
    readiness = report.get("readiness")
    counts = runtime.get("fast_per_batch_structural_acceptance_counts")
    lifecycle = report.get("repository_lifecycle")
    if lifecycle == "precommit-untracked":
        expected_context_runtime_ready = False
        expected_context_runtime_blocker = "hot_loop_contract_gate_not_published"
    elif lifecycle == "clean-tracked-successor":
        expected_context_runtime_ready = True
        expected_context_runtime_blocker = "NONE"
    else:
        _fail()
    if (
        manifest.get("artifact_names") != list(ARTIFACT_NAMES)
        or manifest.get("stable_artifact_names")
        != list(STABLE_ARTIFACT_NAMES)
        or manifest.get("architecture_name") != ARCHITECTURE_NAME
        or manifest.get("existing_slow_public_adapter_source_unchanged")
        is not True
        or manifest.get("adapter_source_refactor_required") is not False
        or context.get("future_product_public_api_exact2")
        != [dict(row) for row in FUTURE_PUBLIC_APIS]
        or context.get("logical_context_field_order")
        != list(LOGICAL_CONTEXT_FIELD_ORDER)
        or context.get("logical_context_field_count") != 20
        or runtime.get("runtime_target") != RUNTIME_TARGET
        or runtime.get("output17_field_order") != list(OUTPUT17_FIELD_ORDER)
        or runtime.get("same_exact_input_success_whole_output17_canonical_bytes_exact")
        is not True
        or runtime.get("same_exact_input_failure_whole_output17_canonical_bytes_exact")
        is not True
        or type(counts) is not dict
        or set(counts.values()) != {0}
        or authority.get("successor_stable5_digest")
        != SUCCESSOR_STABLE5_DIGEST
        or authority.get("reconciliation_contract_digest")
        != RECONCILIATION_STABLE_DIGEST
        or authority.get("context_freshness_model")
        != CONTEXT_FRESHNESS_MODEL
        or negative.get("case_count") != len(NEGATIVE_CASES)
        or negative.get("all_cases_fail_closed") is not True
        or [row.get("case_id") for row in negative.get("cases", [])]
        != [case_id for case_id, unused in NEGATIVE_CASES]
        or any(
            row.get("required_verdict") != "REJECT_FAIL_CLOSED"
            for row in negative.get("cases", [])
        )
        or report.get("gate_status") != GATE_STATUS
        or report.get("stable_contract_digest")
        != _manual_stable_digest(artifacts)
        or type(readiness) is not dict
        or readiness.get(
            "ready_for_remap_adapter_hot_loop_contract_gate_commit_review"
        )
        is not True
        or readiness.get("ready_for_remap_adapter_context_runtime_implementation")
        is not expected_context_runtime_ready
        or readiness.get("context_runtime_blocker")
        != expected_context_runtime_blocker
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
    adapter_contract = _validate_adapter_contract()
    stable_values = (
        _manifest_artifact(owner_rows, evidence_rows),
        _context_contract_artifact(adapter_contract),
        _runtime_contract_artifact(adapter_contract),
        _authority_contract_artifact(adapter_contract),
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
            adapter_contract=adapter_contract,
        )
    )
    _validate_artifacts(artifacts)
    if (
        _repository_snapshot(repository) != before_repository
        or _evidence_snapshot(state) != before_evidence
    ):
        _fail()
    return artifacts


def build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic in-memory hot-loop contract Exact6."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error
