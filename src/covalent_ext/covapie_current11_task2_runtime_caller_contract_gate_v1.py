"""Build the Current11 Task 2 runtime-caller contract gate V1."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
import subprocess
from pathlib import Path
from typing import Mapping, NoReturn, Sequence


__all__ = (
    "build_covapie_current11_task2_runtime_caller_contract_gate_v1",
)

_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1_ERROR"
_CALLER_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR"
_BASE_COMMIT = "1e0b338c63d8bfa6c131994b476dcc7a0ed3cb97"
_BASE_SUBJECT = "add CovaPIE Current11 Task2 compiler context from remap context v1"
_BRANCH = "main"
_ARCHITECTURE = (
    "additive_stateless_runtime_caller_with_explicit_rank_local_remap_and_"
    "compiler_contexts_v1"
)
_INSERTION_POINT = "on_before_batch_transfer"
_INSERTION_CLAIM = (
    "selected_cpu_safe_insertion_point_for_audited_single_device_and_DDP_runtime"
)

_MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_task2_runtime_caller_contract_gate_v1.py"
)
_SCRIPT_PATH = (
    "scripts/check_covapie_current11_task2_runtime_caller_contract_gate_v1.py"
)
_TEST_PATH = (
    "tests/test_covapie_current11_task2_runtime_caller_contract_gate_v1.py"
)
_GUIDE_PATH = (
    "docs/covapie_current11_task2_runtime_caller_contract_gate_v1_guide.md"
)
_REPOSITORY_EXACT4 = (_MODULE_PATH, _SCRIPT_PATH, _TEST_PATH, _GUIDE_PATH)

_MANIFEST = "current11_task2_runtime_caller_contract_manifest.json"
_FRAMEWORK = "current11_task2_runtime_caller_framework_authority.json"
_RESULT_SCHEMA = "current11_task2_runtime_caller_result_schema.json"
_ROUTING = "current11_task2_runtime_caller_terminal_routing.json"
_LIFECYCLE = "current11_task2_runtime_caller_lifecycle_and_io.json"
_ACCEPTANCE = "current11_task2_runtime_caller_acceptance_matrix.json"
_REPORT = "current11_task2_runtime_caller_contract_gate_report.json"
_ARTIFACT_NAMES = (
    _MANIFEST,
    _FRAMEWORK,
    _RESULT_SCHEMA,
    _ROUTING,
    _LIFECYCLE,
    _ACCEPTANCE,
    _REPORT,
)
_STABLE_NAMES = _ARTIFACT_NAMES[:-1]
_STABLE_DOMAIN = b"COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1\0"

_DESIGN_REPORT_RELATIVE = (
    "review-scratch/current11-task2-runtime-caller-dataloader-integration-"
    "design-v1/runtime_caller_dataloader_integration_design_report.md"
)
_DESIGN_REPORT_IDENTITY = {
    "mode": "0644",
    "bytes": 51854,
    "LF": 762,
    "sha256": "929a71adbd44ee0b6909ad5e163c69c9cc7f30ffe9b9fd465dcdb23d8a10ce59",
}

_OWNER_SPECS = (
    {
        "owner": "repository_declared_environment",
        "path": "environment.yaml",
        "last_change_commit": "5d0d38d16c8932a0339fd2ce3f67ade98bbdff27",
        "mode": "0644",
        "bytes": 505,
        "LF": 29,
        "sha256": "a63682607def274b362787a2bd9250a9192a1b898b13632285725901401ea156",
        "git_blob": "9af8f3507cb691a0271bff36ba5341025c3a8bda",
    },
    {
        "owner": "frozen_dataset_transport",
        "path": "dataset.py",
        "last_change_commit": "8a8e03c901029b0e826ac4973d341e7204287d0e",
        "mode": "0644",
        "bytes": 2693,
        "LF": 70,
        "sha256": "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
        "git_blob": "5cd1531e9beeca2f53c17b705949676bf457a967",
    },
    {
        "owner": "frozen_lightning_module",
        "path": "lightning_modules.py",
        "last_change_commit": "2c504ff2eac0864c146129f4011d902fae5bef69",
        "mode": "0644",
        "bytes": 50939,
        "LF": 1250,
        "sha256": "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
        "git_blob": "d19f18ec2841a9a3163d099f4df451d97ce795d4",
    },
    {
        "owner": "runtime_batch_observation_extractor_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_runtime_batch_observation_extractor_v1.py"
        ),
        "last_change_commit": "463c481b65a68442f19b9f1b417ce2325434785f",
        "mode": "0644",
        "bytes": 9229,
        "LF": 287,
        "sha256": "aa129304b350e1089411803c90890c638526e6e3db79bd55a9460b7a1960c5b9",
        "git_blob": "1f7b978eaa111c7cdd296d256c8cfc6d18242802",
    },
    {
        "owner": "compiler_context_from_remap_context_v1",
        "path": (
            "src/covalent_ext/covapie_current11_task2_batch_descriptor_"
            "compiler_context_from_remap_context_v1.py"
        ),
        "last_change_commit": _BASE_COMMIT,
        "mode": "0644",
        "bytes": 22556,
        "LF": 683,
        "sha256": "af9c80a1b46839872b64d2be4005e855b91fa26e761c0cd2c1f146a8e8177b35",
        "git_blob": "0ac10bf21db93273a1e9b0cd49b5b23e33261b44",
    },
    {
        "owner": "remap_adapter_context_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
        ),
        "last_change_commit": "e9a650dd6ee1f53916d412c1540f0c896188083f",
        "mode": "0644",
        "bytes": 43578,
        "LF": 1211,
        "sha256": "1eb764aa4425ad857d59daa625e610a5e015a0a272594f332254998bed8191e6",
        "git_blob": "b4a68ff8193666a3d22f777b111c3ae01178ef8d",
    },
    {
        "owner": "remap_adapter_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_v1.py"
        ),
        "last_change_commit": "b3c76bd4321da5aece08711a4d6f2d421cb8b54b",
        "mode": "0644",
        "bytes": 56510,
        "LF": 1368,
        "sha256": "d09bd5648a3c47851efd933fa8c0523c4ab7c67f8cce765b08fb8423a4e57dd2",
        "git_blob": "11573d4e0857cf69dceb22c3b1ec4f319faa6d08",
    },
    {
        "owner": "batch_descriptor_compiler_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_descriptor_compiler_v1.py"
        ),
        "last_change_commit": "ac22f9cdb8438cf97e3da6e4668e9b124d484f95",
        "mode": "0644",
        "bytes": 31298,
        "LF": 687,
        "sha256": "a7a232a4f344e5cbac152ae8cc51921f4d9bf07deaaab0d55f1ce950e67b524a",
        "git_blob": "26037347244a7b33d23b475d32f565e4580eb7fe",
    },
)

_RESULT_SCHEMA_VERSION = "covapie_current11_task2_runtime_caller_result_v1"
_RESULT_FIELDS = (
    "schema_version",
    "runtime_status",
    "failure_stage",
    "failure_reason",
    "compiler_status",
    "remap_status",
    "batch_sample_keys_or_none",
    "compiler_failure_output10_or_none",
    "remap_output17_or_none",
    "provenance",
    "readiness",
)
_TERMINAL_CLASSES = (
    "programming_error",
    "extractor_failure",
    "compiler_failure",
    "remap_failure",
    "full_success",
)
_EXTRACTOR_REASONS = (
    "missing_names",
    "invalid_sample_key_scalar",
    "invalid_role_length",
    "invalid_membership",
    "unsupported_empty_batch",
    "virtual_nodes_not_supported",
    "buffer_length_mismatch",
    "unsupported_runtime_type",
)
_EXTRACTOR_ERROR = (
    "COVAPIE_CURRENT11_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_V1_ERROR"
)
_COMPILER_OVERALL_SUCCESS_STATUS = "COMPILED_EXACT"
_COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES = (
    "JOINT_LAYOUT_UNAVAILABLE",
)
_COMPILER_STRUCTURED_FAILURE_STATUSES = (
    "BATCH_OBSERVATION_SCHEMA_MISMATCH",
    "BATCH_SAMPLE_KEY_INVALID",
    "BATCH_SAMPLE_KEY_DUPLICATED",
    "BATCH_SAMPLE_KEY_UNKNOWN",
    "BATCH_SAMPLE_KEY_AMBIGUOUS",
    "SOURCE_CONTRACT_MISMATCH",
    "IDENTITY_PROVIDER_MISSING",
    "IDENTITY_PROVIDER_MISMATCH",
    "ROLE_TABLE_AUTHORITY_MISSING",
    "ROLE_LENGTH_MISMATCH",
    "MEMBERSHIP_MASK_MISMATCH",
    "VIRTUAL_NODE_POLICY_MISMATCH",
    "NON_SOURCE_SAMPLE_NOT_ADMISSIBLE_IN_CURRENT11_COMPILER_V1",
)
_REMAP_OVERALL_SUCCESS_STATUS = "REMAPPED_EXACT"
_REMAP_NON_OVERALL_STATUSES = (
    "NOT_IN_BATCH",
    "JOINT_INDEX_SPACE_UNAVAILABLE",
)
_REMAP_STRUCTURED_FAILURE_STATUSES = (
    "SOURCE_SAMPLE_DUPLICATED",
    "BATCH_SAMPLE_IDENTITY_UNKNOWN",
    "BATCH_SAMPLE_DUPLICATED",
    "SCHEMA_VERSION_MISMATCH",
    "SOURCE_TABLE_IDENTITY_MISMATCH",
    "SOURCE_ROW_OUT_OF_RANGE",
    "SOURCE_ATOM_IDENTITY_MISMATCH",
    "ROLE_MISMATCH",
    "PARSER_ATOM_NOT_FOUND",
    "PARSER_ATOM_NOT_UNIQUE",
    "PARSER_COUNT_MISMATCH",
    "COLLATE_OFFSET_MISSING",
    "COLLATE_LENGTH_MISMATCH",
    "BATCH_INDEX_OUT_OF_RANGE",
    "ENTRY_INVALID",
)
_COMPILER_OUTPUT_FIELDS = (
    "schema_version",
    "compiler_status",
    "failure_reason",
    "adapter_input_exact18",
    "batch_sample_key_outcomes",
    "source_contract_digest",
    "identity_provider_digest",
    "runtime_schema_binding",
    "provenance",
    "readiness",
)
_EXACT14_FIELDS = (
    "schema_version",
    "runtime_batch_schema_version",
    "sample_key_schema_version",
    "batch_sample_keys",
    "ligand_lengths",
    "pocket_lengths",
    "ligand_membership",
    "pocket_membership",
    "joint_layout_descriptor",
    "virtual_node_policy",
    "receptors",
    "consistency_buffer_lengths",
    "debug_coordinates",
    "debug_rank_metadata",
)
_EXACT18_FIELDS = (
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
_REMAP_OUTPUT_FIELDS = (
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

_CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
_READINESS = {
    "runtime_caller_contract_gate_implemented": True,
    "runtime_caller_contract_gate_passed": True,
    "ready_for_runtime_caller_implementation": True,
    "ready_for_dataloader_integration": False,
    "ready_for_model_integration": False,
    "ready_for_loss_integration": False,
    "feature_semantics_reaudit_required_before_training": True,
    "step12d_smoke_is_final_training_feature_contract": False,
    "ready_for_training": False,
}

_PL_1_8_4_SOURCES = (
    (
        "loops/fit_loop.py",
        15972,
        353,
        "5ca279d7452b4f594661281cac87eb5f9eb04cb7da0c3ace49d353d44d5ad529",
        (259, 260, 261, 265),
    ),
    (
        "loops/dataloader/evaluation_loop.py",
        17802,
        410,
        "623af52bfc34cf2adb88c281249bed9686d20645a5315e826aa17010467b0dfc",
        (140, 141, 142, 146),
    ),
    (
        "utilities/fetching.py",
        15031,
        402,
        "26e3bc65c42e0fb3416d1a26778a04d38976871bf9781b23e3b19bbd65a10a7a",
        (223, 228, 275, 294),
    ),
    (
        "strategies/strategy.py",
        21570,
        554,
        "e3baffedd5d93555f6c0a12c3a53dd1b100abcf0abead748475a19ac85b6a123",
        (259, 273),
    ),
    (
        "core/module.py",
        86976,
        2022,
        "6a88f8f0e4312e5aa697ff12438559cb0ff49b29c73a393f9b7e519d7347603e",
        (288, 291, 295, 296),
    ),
    (
        "core/hooks.py",
        28885,
        746,
        "e700512e9c4d6cededc95b6941e8a12165681fa0f5d0c1ce7efa9ab5b01a3a4a",
        (575, 596, 643, 665, 674),
    ),
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error
    if b"\0" in payload or b"\r" in payload or payload.endswith(b"\n\n"):
        _fail()
    return payload


def _compact_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(_STABLE_DOMAIN)
    for name in _STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _require_root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
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
        raise ValueError(_ERROR) from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _file_identity(path: Path) -> dict[str, object]:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(_ERROR) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail()
    return {
        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
        "bytes": len(payload),
        "LF": payload.count(b"\n"),
        "sha256": _sha256(payload),
    }


def _safe_text_file(path: Path) -> dict[str, object]:
    identity = _file_identity(path)
    try:
        payload = path.read_bytes()
        payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(_ERROR) from error
    if (
        identity["mode"] != "0644"
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
    return identity


def _repository_lifecycle(repo_root: Path) -> tuple[str, dict[str, object]]:
    branch = _run_git(repo_root, ("branch", "--show-current")).strip()
    head = _run_git(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _run_git(repo_root, ("rev-parse", "origin/main")).strip()
    relation = _run_git(
        repo_root, ("rev-list", "--left-right", "--count", "HEAD...origin/main")
    ).strip()
    subject = _run_git(repo_root, ("log", "-1", "--format=%s", "HEAD")).strip()
    if branch != _BRANCH or relation.count("\t") != 1:
        _fail()
    ahead_text, behind_text = relation.split("\t")
    if not ahead_text.isdigit() or not behind_text.isdigit():
        _fail()
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *_REPOSITORY_EXACT4)
    ).splitlines()
    expected_untracked = {f"?? {name}" for name in _REPOSITORY_EXACT4}
    if set(status) == expected_untracked and len(status) == len(_REPOSITORY_EXACT4):
        if (
            index
            or head != _BASE_COMMIT
            or origin != _BASE_COMMIT
            or ahead_text != "0"
            or behind_text != "0"
            or subject != _BASE_SUBJECT
        ):
            _fail()
        lifecycle = "precommit-untracked"
    elif not status and len(index) == len(_REPOSITORY_EXACT4):
        if (
            head != origin
            or ahead_text != "0"
            or behind_text != "0"
        ):
            _fail()
        _run_git(repo_root, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))
        seen: set[str] = set()
        for row in index:
            try:
                metadata, relative = row.split("\t", 1)
                mode, blob, stage = metadata.split()
            except ValueError as error:
                raise ValueError(_ERROR) from error
            if (
                relative not in _REPOSITORY_EXACT4
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
        if seen != set(_REPOSITORY_EXACT4):
            _fail()
        lifecycle = "clean-tracked-successor"
    else:
        _fail()
    return lifecycle, {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "head_subject": subject,
    }


def _validate_owner_sources(repo_root: Path) -> list[dict[str, object]]:
    identities: list[dict[str, object]] = []
    for spec in _OWNER_SPECS:
        path = repo_root / str(spec["path"])
        observed = _file_identity(path)
        expected = {
            key: spec[key] for key in ("mode", "bytes", "LF", "sha256")
        }
        if observed != expected:
            _fail()
        blob = _run_git(repo_root, ("hash-object", "--no-filters", "--", str(spec["path"]))).strip()
        head_blob = _run_git(repo_root, ("rev-parse", f"HEAD:{spec['path']}")).strip()
        last = _run_git(repo_root, ("log", "-1", "--format=%H", "--", str(spec["path"]))).strip()
        if blob != spec["git_blob"] or head_blob != blob or last != spec["last_change_commit"]:
            _fail()
        identities.append({"owner": spec["owner"], **spec})
    return identities


def _literal_assignment(path: Path, name: str) -> object:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    matches = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    ]
    if len(matches) != 1:
        _fail()
    try:
        return ast.literal_eval(matches[0])
    except (ValueError, TypeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error


def _validate_product_contracts(repo_root: Path) -> None:
    extractor = repo_root / str(_OWNER_SPECS[3]["path"])
    bridge = repo_root / str(_OWNER_SPECS[4]["path"])
    remap_context = repo_root / str(_OWNER_SPECS[5]["path"])
    remap = repo_root / str(_OWNER_SPECS[6]["path"])
    compiler = repo_root / str(_OWNER_SPECS[7]["path"])
    if (
        _literal_assignment(extractor, "__all__")
        != ("extract_covapie_current11_runtime_batch_observation_v1",)
        or _literal_assignment(extractor, "_FIELDS") != _EXACT14_FIELDS
        or _literal_assignment(bridge, "__all__")
        != (
            "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
            "compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1",
        )
        or _literal_assignment(remap_context, "__all__")
        != (
            "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
            "remap_covapie_current11_task2_batch_index_with_context_v1",
        )
        or _literal_assignment(compiler, "_INPUT_FIELDS") != _EXACT14_FIELDS
        or _literal_assignment(compiler, "_OUTPUT_FIELDS") != _COMPILER_OUTPUT_FIELDS
        or _literal_assignment(compiler, "_EXACT18_FIELDS") != _EXACT18_FIELDS
        or _literal_assignment(compiler, "_STATUS_ORDER")
        != (
            _COMPILER_OVERALL_SUCCESS_STATUS,
            *_COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES,
            *_COMPILER_STRUCTURED_FAILURE_STATUSES,
        )
        or _literal_assignment(remap, "_INPUT_FIELD_ORDER") != _EXACT18_FIELDS
        or _literal_assignment(remap, "_OUTPUT_FIELD_ORDER") != _REMAP_OUTPUT_FIELDS
        or _literal_assignment(remap, "_STATUS_ORDER")
        != (
            _REMAP_OVERALL_SUCCESS_STATUS,
            _REMAP_NON_OVERALL_STATUSES[0],
            *_REMAP_STRUCTURED_FAILURE_STATUSES[:-1],
            _REMAP_NON_OVERALL_STATUSES[1],
            _REMAP_STRUCTURED_FAILURE_STATUSES[-1],
        )
    ):
        _fail()


def _validate_environment(repo_root: Path) -> None:
    try:
        text = (repo_root / "environment.yaml").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(_ERROR) from error
    required = (
        "  - python=3.10.4\n",
        "  - pytorch=2.0.1=*cuda11.8*\n",
        "  - cudatoolkit=11.8\n",
        "  - pytorch-lightning=1.8.4\n",
    )
    if any(text.count(line) != 1 for line in required):
        _fail()


def _manifest_artifact(owners: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_runtime_caller_contract_manifest_v1",
        "base_commit": _BASE_COMMIT,
        "selected_architecture": _ARCHITECTURE,
        "future_caller_input_order": ["raw_batch", "remap_context", "compiler_context"],
        "stage_order": [
            "runtime_observation_extractor_v1",
            "compiler_bridge_fast_api_v1",
            "remap_context_fast_api_v1",
        ],
        "repository_exact4": list(_REPOSITORY_EXACT4),
        "repository_lifecycle_contract": {
            "lifecycle_types": ["precommit-untracked", "clean-tracked-successor"],
            "clean_tracked_successor_requires_HEAD_equals_origin_main": True,
            "clean_tracked_successor_requires_ahead_zero": True,
            "clean_tracked_successor_requires_behind_zero": True,
            "committed_unpushed_successor_rejected": True,
        },
        "in_memory_artifact_names": list(_ARTIFACT_NAMES),
        "owner_source_identities": owners,
        "design_report_identity": dict(_DESIGN_REPORT_IDENTITY),
        "caller_implementation_created": False,
        "lightning_hook_created": False,
        "sidecar_envelope_created": False,
    }


def _framework_artifact() -> dict[str, object]:
    sources = []
    base = "https://raw.githubusercontent.com/Lightning-AI/lightning/1.8.4/src/pytorch_lightning/"
    for relative, size, lf, digest, anchors in _PL_1_8_4_SOURCES:
        sources.append(
            {
                "relative_path": relative,
                "official_source_url": base + relative,
                "bytes": size,
                "LF": lf,
                "sha256": digest,
                "semantic_anchor_lines": list(anchors),
            }
        )
    return {
        "schema_version": "covapie_current11_task2_runtime_caller_framework_authority_v1",
        "repository_declared_environment": {
            "python": "3.10.4",
            "pytorch": "2.0.1=*cuda11.8*",
            "cudatoolkit": "11.8",
            "pytorch_lightning": "1.8.4",
            "environment_yaml_identity": {
                key: _OWNER_SPECS[0][key]
                for key in ("mode", "bytes", "LF", "sha256", "git_blob")
            },
            "authority_role": "primary_reproducible_compatibility_baseline",
        },
        "corroborating_engineering_environment_snapshot": {
            "python_executable": "/usr/bin/python",
            "python": "3.12.0",
            "pytorch": "2.5.1+cu124",
            "pytorch_lightning": "2.6.5",
            "snapshot_scope": "design_audit_observation_only",
            "dependency_authority": False,
            "runtime_execution_environment_requirement": False,
            "checker_current_environment_claim": False,
        },
        "official_pytorch_lightning_1_8_4_source_evidence": sources,
        "audited_order": [
            "DataLoader_output",
            "on_before_batch_transfer",
            "transfer_batch_to_device",
            "on_after_batch_transfer",
            "training_validation_test_step",
        ],
        "corroborating_2_6_5_order_supports_declared_baseline": True,
        "current_environment_exact_version_required": False,
        "current_environment_not_required": True,
        "selected_lightning_insertion_point": _INSERTION_POINT,
        "selected_insertion_point_claim": _INSERTION_CLAIM,
        "on_before_hook_receives_pre_device_batch": True,
        "default_dict_list_tensor_transfer_occurs_after_selected_hook": True,
        "single_device_supported_scope": True,
        "DDP_supported_scope": True,
        "DataParallel_not_supported_by_this_v1": True,
        "rank_main_process_hook_not_dataloader_worker": True,
        "worker_context_required": False,
        "worker_context_pickle_required": False,
        "hook_mechanism_is_predict_extensible": True,
        "current_predict_integration_proven": False,
        "arbitrary_lightning_version_or_strategy_claimed": False,
    }


def _result_schema_artifact() -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_runtime_caller_result_schema_contract_v1",
        "runtime_result_schema_version": _RESULT_SCHEMA_VERSION,
        "container_type": "exact_builtin_dict",
        "exact_field_count": 11,
        "field_order": list(_RESULT_FIELDS),
        "terminal_classes": list(_TERMINAL_CLASSES),
        "success_output10_retained": False,
        "success_exact18_retained": False,
        "success_exact18_lifecycle": "transient_compiler_to_remap_handoff_only",
        "compiler_failure_output10_retention": "whole_exact_output10",
        "remap_output17_retention": "whole_exact_output17_when_remap_called",
        "exact14_to_compiler_conversion_count": 0,
        "compiler_exact18_to_remap_conversion_count": 0,
        "rename_cast_repair_reorder_or_reconstruction_allowed": False,
    }


def _routing_artifact() -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_runtime_caller_terminal_routing_v1",
        "caller_programming_error_token": _CALLER_ERROR,
        "compiler_overall_success_status": _COMPILER_OVERALL_SUCCESS_STATUS,
        "compiler_component_only_non_overall_statuses": list(
            _COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES
        ),
        "compiler_structured_failure_statuses": list(
            _COMPILER_STRUCTURED_FAILURE_STATUSES
        ),
        "remap_overall_success_status": _REMAP_OVERALL_SUCCESS_STATUS,
        "remap_non_overall_statuses": list(_REMAP_NON_OVERALL_STATUSES),
        "remap_structured_failure_statuses": list(
            _REMAP_STRUCTURED_FAILURE_STATUSES
        ),
        "known_but_non_overall_status_seen_as_overall": "programming_error",
        "programming_error": {
            "transport": "exception_only",
            "exception_chaining_required": True,
            "caller_normalizes_Exception": True,
            "caller_catches_BaseException": False,
            "keyboard_interrupt_not_normalized_by_caller": True,
            "system_exit_not_normalized_by_caller": True,
            "reached_stage_context_or_product_invariant_violation": "raise_caller_error",
            "malformed_product": "raise_caller_error",
            "unknown_status": "raise_caller_error",
            "field_order_or_schema_inconsistency": "raise_caller_error",
            "programming_error_swallowed": False,
        },
        "extractor_failure": {
            "accepted_error_token": _EXTRACTOR_ERROR,
            "accepted_failure_reasons": list(_EXTRACTOR_REASONS),
            "runtime_status": "extractor_failure",
            "failure_stage": "extractor",
            "compiler_bridge_fast_calls": 0,
            "remap_context_fast_calls": 0,
            "device_copy_back": False,
            "name_normalization": False,
            "membership_recast": False,
            "virtual_node_stripping": False,
            "batch_repair": False,
        },
        "compiler_failure": {
            "precondition": "extractor_success",
            "compiler_bridge_fast_calls": 1,
            "compiler_status_must_be_in": list(
                _COMPILER_STRUCTURED_FAILURE_STATUSES
            ),
            "failure_reason_must_equal_compiler_status": True,
            "compiler_failure_output10_or_none": "whole_exact_output10",
            "adapter_input_exact18_required": None,
            "remap_context_fast_calls": 0,
        },
        "remap_failure": {
            "precondition": "compiler_status_equals_COMPILED_EXACT",
            "remap_context_fast_calls": 1,
            "remap_status_must_be_in": list(_REMAP_STRUCTURED_FAILURE_STATUSES),
            "failure_reason_must_equal_remap_status": True,
            "remap_output17_or_none": "whole_exact_output17_unchanged",
        },
        "full_success": {
            "extractor_success_required": True,
            "compiler_status_required": "COMPILED_EXACT",
            "compiler_success_failure_reason_required": "NONE",
            "remap_status_required": "REMAPPED_EXACT",
            "remap_success_failure_reason_required": "NONE",
            "joint_layout_descriptor_none_is_failure": False,
            "whole_success_output10_retained": False,
            "transient_success_exact18_retained": False,
            "whole_success_output17_retained": True,
        },
        "status_failure_reason_invariants": {
            "compiler_success_failure_reason_required": "NONE",
            "compiler_failure_reason_must_equal_compiler_status": True,
            "remap_success_failure_reason_required": "NONE",
            "remap_failure_reason_must_equal_remap_status": True,
            "status_failure_reason_inconsistency": "programming_error",
        },
        "exact14_field_order": list(_EXACT14_FIELDS),
        "compiler_output10_field_order": list(_COMPILER_OUTPUT_FIELDS),
        "compiler_success_exact18_field_order": list(_EXACT18_FIELDS),
        "remap_input_exact18_field_order": list(_EXACT18_FIELDS),
        "remap_output17_field_order": list(_REMAP_OUTPUT_FIELDS),
    }


def _lifecycle_artifact() -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_runtime_caller_lifecycle_and_io_v1",
        "startup_lifecycle": {
            "scope": "once_per_process_per_DDP_rank_startup",
            "remap_context_build_count": 1,
            "compiler_context_build_count": 1,
            "compiler_context_derived_from_exact_remap_context_object": True,
            "same_remap_object_consumed_by_bridge": True,
            "same_remap_context_used_for_fast_remap": True,
            "lightning_lifecycle_owner_implemented_by_this_gate": False,
        },
        "per_batch_lifecycle": {
            "remap_context_builds": 0,
            "compiler_context_builds": 0,
            "worker_context_build_count": 0,
            "per_batch_context_build_count": 0,
            "pickle_required": False,
            "global_singleton": False,
            "cross_process_shared_mutable_context": False,
        },
        "mutation_boundary": {
            "caller_input_batch_unchanged": True,
            "observation_input_to_compiler_unchanged": True,
            "exact18_input_to_remap_unchanged": True,
            "in_place_batch_sidecar_insertion": False,
            "target_residue_extra_field_ignored_by_extractor": True,
            "target_residue_participates_in_task2_identity_selection": False,
            "virtual_nodes_supported": False,
            "nonzero_or_malformed_virtual_payload_fails_at_extractor": True,
            "strip_or_repair_allowed": False,
        },
        "per_batch_call_vector": {
            "extractor_calls": 1,
            "compiler_bridge_fast_calls": "1_if_extractor_success_else_0",
            "remap_context_fast_calls": "1_if_compiler_status_COMPILED_EXACT_else_0",
            "remap_context_builds": 0,
            "compiler_context_builds": 0,
            "old_compiler_authority_calls": 0,
            "stable5_parser_calls": 0,
            "reconciliation_calls": 0,
            "successor_calls": 0,
            "state_transition_gate_calls": 0,
            "formal_authority_calls": 0,
            "filesystem_reads": 0,
            "filesystem_writes": 0,
            "Git_calls": 0,
            "subprocess_calls": 0,
            "artifact_writes": 0,
            "report_generation_calls": 0,
            "cache_lookups": 0,
            "model_forward_calls": 0,
            "backward_calls": 0,
            "optimizer_steps": 0,
        },
        "latency_SLA_added": False,
        "canonical_masks": [
            {"semantic_long_name": long_name, "display_alias": alias}
            for long_name, alias in _CANONICAL_MASKS
        ],
        "canonical_mask_count": 5,
        "readiness": dict(_READINESS),
    }


def _acceptance_artifact() -> dict[str, object]:
    cases = (
        "repository_declared_environment_frozen",
        "corroborating_snapshot_distinguished_from_dependency_authority",
        "current_environment_exact_version_not_required",
        "lightning_1_8_4_pre_transfer_order_audited",
        "corroborating_lightning_2_6_5_order_recorded",
        "single_device_scope_frozen",
        "DDP_scope_frozen",
        "DataParallel_excluded",
        "predict_current_path_not_claimed",
        "option_B_retained",
        "exact14_to_compiler_zero_conversion",
        "exact18_to_remap_zero_conversion",
        "runtime_result_exact11",
        "programming_error_exception_only",
        "caller_normalizes_Exception_not_BaseException",
        "status_failure_reason_invariants_frozen",
        "overall_status_eligibility_frozen",
        "known_but_non_overall_status_rejected",
        "clean_tracked_successor_requires_published_origin",
        "extractor_failure_short_circuit",
        "compiler_failure_whole_output10",
        "compiler_failure_no_remap",
        "remap_failure_whole_output17",
        "full_success_requires_both_exact_statuses",
        "joint_none_success_allowed",
        "same_remap_object_lifecycle",
        "worker_context_zero",
        "per_batch_context_build_zero",
        "no_pickle_or_global_context",
        "input_mutation_forbidden",
        "target_residue_independent",
        "virtual_nodes_fail_closed",
        "per_batch_no_io",
        "canonical_mask_exact5_with_B3",
        "training_boundaries_closed",
        "ready_for_runtime_caller_implementation_true",
        "caller_not_implemented_by_gate",
        "lightning_hook_not_implemented_by_gate",
        "sidecar_envelope_not_implemented_by_gate",
    )
    return {
        "schema_version": "covapie_current11_task2_runtime_caller_acceptance_matrix_v1",
        "case_count": len(cases),
        "cases": [{"case_id": name, "passed": True} for name in cases],
        "all_passed": True,
    }


def _validate_semantics(artifacts: Mapping[str, bytes]) -> None:
    try:
        parsed = {
            name: json.loads(artifacts[name].decode("utf-8"))
            for name in _STABLE_NAMES
        }
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    manifest = parsed[_MANIFEST]
    framework = parsed[_FRAMEWORK]
    schema = parsed[_RESULT_SCHEMA]
    routing = parsed[_ROUTING]
    lifecycle = parsed[_LIFECYCLE]
    acceptance = parsed[_ACCEPTANCE]
    snapshot = framework.get("corroborating_engineering_environment_snapshot", {})
    programming = routing.get("programming_error", {})
    invariants = routing.get("status_failure_reason_invariants", {})
    compiler_failure = routing.get("compiler_failure", {})
    remap_failure = routing.get("remap_failure", {})
    repository_lifecycle = manifest.get("repository_lifecycle_contract", {})
    if (
        schema.get("field_order") != list(_RESULT_FIELDS)
        or schema.get("exact_field_count") != 11
        or schema.get("terminal_classes") != list(_TERMINAL_CLASSES)
        or routing.get("caller_programming_error_token") != _CALLER_ERROR
        or routing.get("compiler_overall_success_status")
        != _COMPILER_OVERALL_SUCCESS_STATUS
        or routing.get("compiler_component_only_non_overall_statuses")
        != list(_COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES)
        or routing.get("compiler_structured_failure_statuses")
        != list(_COMPILER_STRUCTURED_FAILURE_STATUSES)
        or routing.get("remap_overall_success_status")
        != _REMAP_OVERALL_SUCCESS_STATUS
        or routing.get("remap_non_overall_statuses")
        != list(_REMAP_NON_OVERALL_STATUSES)
        or routing.get("remap_structured_failure_statuses")
        != list(_REMAP_STRUCTURED_FAILURE_STATUSES)
        or routing.get("known_but_non_overall_status_seen_as_overall")
        != "programming_error"
        or compiler_failure.get("compiler_status_must_be_in")
        != list(_COMPILER_STRUCTURED_FAILURE_STATUSES)
        or remap_failure.get("remap_status_must_be_in")
        != list(_REMAP_STRUCTURED_FAILURE_STATUSES)
        or _COMPILER_OVERALL_SUCCESS_STATUS
        in _COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES
        or _COMPILER_OVERALL_SUCCESS_STATUS in _COMPILER_STRUCTURED_FAILURE_STATUSES
        or set(_COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES)
        & set(_COMPILER_STRUCTURED_FAILURE_STATUSES)
        or _REMAP_OVERALL_SUCCESS_STATUS in _REMAP_NON_OVERALL_STATUSES
        or _REMAP_OVERALL_SUCCESS_STATUS in _REMAP_STRUCTURED_FAILURE_STATUSES
        or set(_REMAP_NON_OVERALL_STATUSES) & set(_REMAP_STRUCTURED_FAILURE_STATUSES)
        or routing.get("compiler_success_exact18_field_order")
        != routing.get("remap_input_exact18_field_order")
        or framework.get("selected_lightning_insertion_point") != _INSERTION_POINT
        or framework.get("DataParallel_not_supported_by_this_v1") is not True
        or framework.get("current_environment_exact_version_required") is not False
        or framework.get("current_environment_not_required") is not True
        or snapshot.get("snapshot_scope") != "design_audit_observation_only"
        or snapshot.get("dependency_authority") is not False
        or snapshot.get("runtime_execution_environment_requirement") is not False
        or snapshot.get("checker_current_environment_claim") is not False
        or repository_lifecycle.get(
            "clean_tracked_successor_requires_HEAD_equals_origin_main"
        )
        is not True
        or repository_lifecycle.get("committed_unpushed_successor_rejected")
        is not True
        or programming.get("caller_normalizes_Exception") is not True
        or programming.get("caller_catches_BaseException") is not False
        or programming.get("keyboard_interrupt_not_normalized_by_caller") is not True
        or programming.get("system_exit_not_normalized_by_caller") is not True
        or invariants
        != {
            "compiler_success_failure_reason_required": "NONE",
            "compiler_failure_reason_must_equal_compiler_status": True,
            "remap_success_failure_reason_required": "NONE",
            "remap_failure_reason_must_equal_remap_status": True,
            "status_failure_reason_inconsistency": "programming_error",
        }
        or lifecycle.get("canonical_mask_count") != 5
        or lifecycle.get("readiness") != _READINESS
        or acceptance.get("all_passed") is not True
        or acceptance.get("case_count") != len(acceptance.get("cases", ()))
    ):
        _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repo_root = _require_root(repo_root)
    state_root = _require_root(state_root)
    lifecycle, repository = _repository_lifecycle(repo_root)
    for relative in _REPOSITORY_EXACT4:
        _safe_text_file(repo_root / relative)
    owners = _validate_owner_sources(repo_root)
    _validate_environment(repo_root)
    _validate_product_contracts(repo_root)
    design_identity = _file_identity(state_root / _DESIGN_REPORT_RELATIVE)
    if design_identity != _DESIGN_REPORT_IDENTITY:
        _fail()

    values = {
        _MANIFEST: _manifest_artifact(owners),
        _FRAMEWORK: _framework_artifact(),
        _RESULT_SCHEMA: _result_schema_artifact(),
        _ROUTING: _routing_artifact(),
        _LIFECYCLE: _lifecycle_artifact(),
        _ACCEPTANCE: _acceptance_artifact(),
    }
    artifacts = {name: _canonical_json(values[name]) for name in _STABLE_NAMES}
    _validate_semantics(artifacts)
    stable = _stable_digest(artifacts)
    artifacts[_REPORT] = _canonical_json(
        {
            "schema_version": "covapie_current11_task2_runtime_caller_contract_gate_report_v1",
            "status": (
                "PASS_RUNTIME_CALLER_CONTRACT_GATE_PRECOMMIT_CANDIDATE_ONLY"
                if lifecycle == "precommit-untracked"
                else "PASS_RUNTIME_CALLER_CONTRACT_GATE_PUBLISHED_SUCCESSOR"
            ),
            "repository_lifecycle": lifecycle,
            "repository": repository,
            "selected_architecture": _ARCHITECTURE,
            "selected_lightning_insertion_point": _INSERTION_POINT,
            "selected_insertion_point_claim": _INSERTION_CLAIM,
            "Option_B_retained": True,
            "stable_contract_digest": stable,
            "readiness": dict(_READINESS),
            "caller_implementation_created": False,
            "lightning_hook_created": False,
            "sidecar_envelope_created": False,
            "persistent_artifacts_written": 0,
        }
    )
    if tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    return artifacts


def build_covapie_current11_task2_runtime_caller_contract_gate_v1(
    *, repo_root: Path, state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic runtime-caller contract artifacts in memory."""
    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
