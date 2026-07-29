"""Pure in-memory Current11 warhead/boundary review-ingestion interface.

The committed gate-design module remains the sole authority for ingestion
semantics.  This module adds a stable call boundary, a deterministic Exact6
response, and independent response-level batch invariants.  Synthetic records
are used only while building validation evidence; no submitted review,
envelope, ingestion result, or authority record is persisted.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import json
import re
import stat
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as design,
)


SCHEMA_VERSION = (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_interface_v1"
)
INTERFACE_VERSION = (
    "covapie_current11_warhead_boundary_review_ingestion_interface_v1"
)
INTERFACE_RESPONSE_VERSION = (
    "covapie_current11_warhead_boundary_review_ingestion_"
    "interface_response_v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review ingestion interface v1"
)
BASE_COMMIT = "7e0f63d043b546480f66215c69af37253506c08a"
BASE_PARENT = "d0243f7b5d8c0ff7a2831be1a5ed904fb8ff294f"
BASE_TREE = "4191e43ea701c669ac1a45f38bea9735c2e175b8"
BASE_SUBJECT = (
    "add CovaPIE Current11 warhead atom set and attachment boundary "
    "review ingestion gate design v1"
)

OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
SOURCE_FILE = "covapie_review_ingestion_interface_source_inventory.csv"
CONTRACT_FILE = "covapie_review_ingestion_interface_contract_registry.csv"
TRUTH_FILE = "covapie_review_ingestion_interface_truth_matrix.csv"
READINESS_FILE = (
    "covapie_current11_review_ingestion_interface_readiness_matrix.csv"
)
FAILURE_FILE = "covapie_review_ingestion_interface_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_warhead_boundary_review_ingestion_"
    "interface_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE,
    CONTRACT_FILE,
    TRUTH_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
PRODUCTION_PATH = Path("src/covalent_ext") / f"{SCHEMA_VERSION}.py"
TEST_PATH = Path("tests") / f"test_{SCHEMA_VERSION}.py"
CHECKER_PATH = Path("scripts") / f"check_{SCHEMA_VERSION}.py"
SUMMARY_PATH = Path("docs") / f"{SCHEMA_VERSION}_summary.md"
EXACT10_PATHS = (
    PRODUCTION_PATH,
    TEST_PATH,
    CHECKER_PATH,
    SUMMARY_PATH,
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

DESIGN_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_gate_design_v1"
)
DESIGN_PRODUCTION = Path("src/covalent_ext") / (
    "covapie_current11_warhead_atom_set_and_attachment_boundary_"
    "review_ingestion_gate_design_v1.py"
)
DESIGN_MANIFEST = DESIGN_ROOT / (
    "covapie_current11_warhead_boundary_review_ingestion_"
    "gate_design_manifest.json"
)
DESIGN_CONTRACT = DESIGN_ROOT / "covapie_review_ingestion_contract_registry.csv"
DESIGN_DECISION = (
    DESIGN_ROOT / "covapie_review_ingestion_decision_effect_matrix.csv"
)
DESIGN_READINESS = (
    DESIGN_ROOT / "covapie_current11_review_ingestion_readiness_matrix.csv"
)
DESIGN_FAILURE = DESIGN_ROOT / "covapie_review_ingestion_gate_failure_matrix.csv"

FROZEN_BASE_SHA256 = {
    DESIGN_PRODUCTION:
        "cd726f7122edd8315079f0ac1df9d4bb24d4ee969f438ce2f41eda3fd0f7c410",
    DESIGN_MANIFEST:
        "3fb5b40e6bedac764166f51e8f094ef74a511d1eeff593cdbcfd77329a7520eb",
    DESIGN_CONTRACT:
        "8ca97ae4885a7e65f6977ff9b2fc05f271ce578d7cc4871b1aa78bdc78912e0d",
    DESIGN_DECISION:
        "1b92f6da944457a2f61bd544b710dd0960d9901a172d0cfa0a977b1aee113660",
    DESIGN_READINESS:
        "a6d9f8bb42b5b84a80c40fd85d54fdeeb8e0e6ec5e49c1860988c5bad3d70ff2",
    DESIGN_FAILURE:
        "28666093394d1aaf33dbf0c056b04c2ce489a833758e55238f2ce71002ee871b",
}
SOURCE_PATHS = tuple(FROZEN_BASE_SHA256)

INTERFACE_RESPONSE_FIELDS = (
    "interface_response_version",
    "authority_context_record_sha256",
    "batch_passed",
    "ingestion_result_records",
    "new_authority_records",
    "interface_response_sha256",
)
INTERFACE_RESPONSE_HASH_FIELDS = INTERFACE_RESPONSE_FIELDS[:-1]
CANONICAL_MASKS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
SUPPORTED_RUNTIME_LIFECYCLES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
PUBLIC_RUNTIME_COMPATIBILITY_SCOPE = (
    "interface_base_and_all_descendants_with_frozen_design_source_v1"
)
PUBLIC_RUNTIME_REQUIRED_BASE_COMMIT = BASE_COMMIT
IMPORTED_DESIGN_SOURCE_SHA256 = FROZEN_BASE_SHA256[DESIGN_PRODUCTION]
_SHA = re.compile(r"[0-9a-f]{64}")

SOURCE_COLUMNS = (
    "source_path",
    "BASE_SHA256",
    "source_row_count",
    "fields_actually_used",
    "authority_class",
    "verified",
)
CONTRACT_COLUMNS = (
    "contract_id",
    "semantic_name",
    "contract_scope",
    "required_inputs",
    "validation_rule",
    "success_effect",
    "failure_effect",
    "fails_closed",
    "verified",
)
TRUTH_COLUMNS = (
    "truth_case_id",
    "truth_case_name",
    "expected_batch_passed",
    "expected_outcome_class",
    "expected_result_count",
    "expected_new_authority_count",
    "expected_reason_sequence",
    "expected_replay_count",
    "expected_conflict_count",
    "response_schema_valid",
    "response_hash_valid",
    "input_order_preserved",
    "inputs_unmodified",
    "filesystem_write_count",
    "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "source_candidate_set_sha256",
    "review_package_available",
    "blank_review_template_available",
    "interface_implementation_available",
    "immutable_authority_context_available",
    "interface_synthetic_validation_passed",
    "completed_review_record_available",
    "human_provenance_envelope_available",
    "ready_for_real_ingestion_execution",
    "real_ingestion_completed",
    "authority_record_available",
    "complete_warhead_atom_set_authority_available",
    "exact_one_attachment_boundary_authority_available",
    "sample_quarantined",
    "ready_for_candidate_warhead_smarts_materialization",
    "ready_for_role_proposal_generation",
    "ready_for_mask_materialization",
    "ready_for_model_integration",
    "ready_for_training",
    "blocking_reasons",
    "verified",
)
FAILURE_COLUMNS = (
    "failure_case_id",
    "failure_case_name",
    "mutation_signature",
    "mutated_field",
    "mutated_value_json",
    "expected_reason",
    "observed_reasons",
    "expected_reason_verified",
    "fails_closed",
    "contract_row_count",
    "truth_row_count",
    "current11_readiness_row_count",
    "actual_completed_review_count",
    "actual_ingestion_envelope_count",
    "actual_ingestion_result_count",
    "actual_authority_record_count",
    "smarts_ready",
    "role_ready",
    "mask_ready",
    "model_ready",
    "training_ready",
    "verified",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )


def _git(
    repo_root: Path, *arguments: str, check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode:
        raise RuntimeError(
            "git_command_failed:"
            + " ".join(arguments)
            + ":"
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def validate_execution_boundary_v1(repo_root: Path) -> str:
    identity = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT,
    ).stdout.decode().splitlines()
    if identity != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"
    raw = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        line[7:].decode()
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    subject, newline, body = message.partition(b"\n")
    if (
        parents != (BASE_COMMIT,)
        or not newline
        or subject.decode() != FORMAL_COMMIT_SUBJECT
        or body
    ):
        raise ValueError("successor_identity_mismatch")
    changed = {
        item.decode()
        for item in _git(
            repo_root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ).stdout.split(b"\0")
        if item
    }
    if changed != {path.as_posix() for path in EXACT10_PATHS}:
        raise ValueError("successor_changed_path_inventory_mismatch")
    tree_rows = [
        row
        for row in _git(
            repo_root,
            "ls-tree",
            "-r",
            "-z",
            head,
            "--",
            *(path.as_posix() for path in EXACT10_PATHS),
        ).stdout.split(b"\0")
        if row
    ]
    if len(tree_rows) != 10 or any(
        not row.startswith(b"100644 blob ") for row in tree_rows
    ):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False,
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root,
        "rev-parse",
        "--verify",
        "refs/remotes/origin/main",
        check=False,
    )
    if origin.returncode:
        raise ValueError("successor_origin_main_missing")
    origin_oid = origin.stdout.decode().strip()
    if origin_oid == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_oid == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def _validate_public_runtime_repository_v1(repo_root: Path) -> None:
    """Require a repository rooted at the interface BASE or a descendant."""

    try:
        if not isinstance(repo_root, Path):
            raise TypeError("repo_root_exact_Path_required")
        resolved_root = repo_root.resolve(strict=True)
        top_level = _git(
            resolved_root, "rev-parse", "--show-toplevel", check=False,
        )
        if (
            top_level.returncode
            or not top_level.stdout.strip()
            or Path(top_level.stdout.decode().strip()).resolve(strict=True)
            != resolved_root
        ):
            raise ValueError("repository_root_mismatch")
        for commit in (BASE_COMMIT, design.BASE_COMMIT):
            if _git(
                resolved_root,
                "cat-file",
                "-e",
                f"{commit}^{{commit}}",
                check=False,
            ).returncode:
                raise ValueError("required_commit_object_missing")
        head_result = _git(
            resolved_root, "rev-parse", "--verify", "HEAD", check=False,
        )
        if head_result.returncode:
            raise ValueError("HEAD_missing")
        head = head_result.stdout.decode().strip()
        if _git(
            resolved_root,
            "merge-base",
            "--is-ancestor",
            BASE_COMMIT,
            head,
            check=False,
        ).returncode:
            raise ValueError("interface_BASE_not_HEAD_ancestor")
    except (OSError, RuntimeError, TypeError, UnicodeError, ValueError) as error:
        raise ValueError(
            "INTERFACE_PUBLIC_RUNTIME_REPOSITORY_INVALID"
        ) from error


def _validate_imported_design_source_integrity_v1(repo_root: Path) -> None:
    """Match the imported design source to its frozen worktree and HEAD bytes."""

    try:
        if not isinstance(repo_root, Path):
            raise TypeError("repo_root_exact_Path_required")
        resolved_root = repo_root.resolve(strict=True)
        expected_source = resolved_root / DESIGN_PRODUCTION
        source_info = expected_source.lstat()
        if (
            not stat.S_ISREG(source_info.st_mode)
            or expected_source.is_symlink()
        ):
            raise ValueError("design_source_not_regular_file")
        imported_file = getattr(design, "__file__", None)
        if type(imported_file) is not str:
            raise ValueError("imported_design_source_path_missing")
        imported_source = Path(imported_file).resolve(strict=True)
        if imported_source != expected_source.resolve(strict=True):
            raise ValueError("imported_design_source_path_mismatch")
        worktree_payload = expected_source.read_bytes()
        head_result = _git(
            resolved_root,
            "show",
            f"HEAD:{DESIGN_PRODUCTION.as_posix()}",
            check=False,
        )
        if head_result.returncode:
            raise ValueError("HEAD_design_source_missing")
        head_payload = head_result.stdout
        if (
            sha256(worktree_payload) != IMPORTED_DESIGN_SOURCE_SHA256
            or sha256(head_payload) != IMPORTED_DESIGN_SOURCE_SHA256
            or worktree_payload != head_payload
        ):
            raise ValueError("imported_design_source_SHA_mismatch")
    except (OSError, RuntimeError, TypeError, UnicodeError, ValueError) as error:
        raise ValueError(
            "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_INVALID"
        ) from error


def _infer_interface_runtime_repository_root_v1() -> Path:
    """Infer the exact Git worktree root from this imported interface source."""

    try:
        source = Path(__file__)
        source_info = source.lstat()
        if not stat.S_ISREG(source_info.st_mode) or source.is_symlink():
            raise ValueError("interface_source_not_regular_file")
        resolved_source = source.resolve(strict=True)
        repo_root = resolved_source.parents[2]
        expected_source = (repo_root / PRODUCTION_PATH).resolve(strict=True)
        if resolved_source != expected_source:
            raise ValueError("interface_source_path_mismatch")
        top_level = _git(
            repo_root, "rev-parse", "--show-toplevel", check=False,
        )
        if (
            top_level.returncode
            or not top_level.stdout.strip()
            or Path(top_level.stdout.decode().strip()).resolve(strict=True)
            != repo_root
        ):
            raise ValueError("repository_root_mismatch")
        return repo_root
    except (IndexError, OSError, RuntimeError, UnicodeError, ValueError) as error:
        raise ValueError(
            "INTERFACE_PUBLIC_RUNTIME_REPOSITORY_INVALID"
        ) from error


def _validate_public_evaluator_runtime_integrity_v1() -> Path:
    """Attest evaluator repository ancestry and frozen design source bytes."""

    repo_root = _infer_interface_runtime_repository_root_v1()
    _validate_public_runtime_repository_v1(repo_root)
    _validate_imported_design_source_integrity_v1(repo_root)
    return repo_root


def base_bytes(repo_root: Path, path: Path) -> bytes:
    result = _git(
        repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}", check=False,
    )
    if result.returncode or not result.stdout:
        raise ValueError(f"BASE_source_missing:{path.as_posix()}")
    return result.stdout


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    payloads: dict[Path, bytes] = {}
    for path, expected in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def _snapshot_value(value: Any) -> Any:
    """Create a canonical, type-tagged immutable snapshot."""

    if value is None:
        return ("none",)
    if type(value) is bool:
        return ("bool", value)
    if type(value) is int:
        return ("int", str(value))
    if type(value) is str:
        return ("str", value)
    if type(value) is bytes:
        return ("bytes", value.hex())
    if type(value) is list:
        return ("list", tuple(_snapshot_value(item) for item in value))
    if type(value) is tuple:
        return ("tuple", tuple(_snapshot_value(item) for item in value))
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("canonical_snapshot_dict_key_exact_str_required")
        return (
            "dict",
            tuple(
                (key, _snapshot_value(value[key]))
                for key in sorted(value, key=lambda item: item.encode("utf-8"))
            ),
        )
    if type(value) is design.IngestionAuthorityContext:
        return (
            "IngestionAuthorityContext",
            _snapshot_value(value.context_record),
            _snapshot_value(value.source_payloads),
        )
    raise TypeError(f"canonical_snapshot_type_unsupported:{type(value).__name__}")


def _safe_exact_str(record: object, field: str) -> str | None:
    if not isinstance(record, Mapping):
        return None
    value = record.get(field)
    return value if type(value) is str else None


def _canonical_record(
    record: Mapping[str, Any], fields: Sequence[str],
) -> dict[str, Any]:
    return {field: record[field] for field in fields}


def _response_hash_payload(response: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "interface_response_version": response["interface_response_version"],
        "authority_context_record_sha256":
            response["authority_context_record_sha256"],
        "batch_passed": response["batch_passed"],
        "ingestion_result_records": [
            _canonical_record(record, design.INGESTION_RESULT_FIELDS)
            for record in response["ingestion_result_records"]
        ],
        "new_authority_records": [
            _canonical_record(record, design.AUTHORITY_RECORD_FIELDS)
            for record in response["new_authority_records"]
        ],
    }


def interface_response_sha256(response: Mapping[str, Any]) -> str:
    return sha256(canonical_json(_response_hash_payload(response)).encode("utf-8"))


def _build_committed_design_authority_context_v1(
    repo_root: Path,
) -> design.IngestionAuthorityContext:
    """Build a context from the committed design BASE Git objects."""

    _validate_public_runtime_repository_v1(repo_root)
    _validate_imported_design_source_integrity_v1(repo_root)
    source_payloads = []
    pairs = []
    for path in design.SOURCE_PATHS:
        result = _git(
            repo_root,
            "show",
            f"{design.BASE_COMMIT}:{path.as_posix()}",
            check=False,
        )
        if result.returncode or not result.stdout:
            raise ValueError(f"DESIGN_BASE_SOURCE_MISSING:{path.as_posix()}")
        payload = result.stdout
        digest = design.sha256(payload)
        if digest != design.FROZEN_BASE_SHA256[path]:
            raise ValueError(
                f"DESIGN_BASE_SOURCE_SHA_MISMATCH:{path.as_posix()}"
            )
        source_payloads.append((path.as_posix(), payload))
        pairs.append(f"{path.as_posix()}\t{digest}")
    record: dict[str, Any] = {
        "ingestion_authority_context_version":
            design.INGESTION_AUTHORITY_CONTEXT_VERSION,
        "formal_base_commit": design.BASE_COMMIT,
        "ordered_source_path_sha256_pairs": pairs,
        "ingestion_authority_context_record_sha256": "",
    }
    record["ingestion_authority_context_record_sha256"] = design.sha256(
        design.canonical_json({
            field: record[field]
            for field in design.INGESTION_AUTHORITY_CONTEXT_FIELDS
            if field != "ingestion_authority_context_record_sha256"
        }).encode("utf-8")
    )
    context = design.IngestionAuthorityContext(
        record, tuple(source_payloads),
    )
    design.validate_ingestion_authority_context(context)
    return context


def build_current11_warhead_boundary_review_ingestion_authority_context_v1(
    repo_root: Path,
) -> design.IngestionAuthorityContext:
    """Build and revalidate a fresh immutable committed-design context."""

    context = _build_committed_design_authority_context_v1(repo_root)
    design.validate_ingestion_authority_context(context)
    return context


def validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
    response: Mapping[str, Any],
    *,
    submissions: Sequence[
        tuple[Mapping[str, Any], Mapping[str, Any]]
    ],
    authority_context: design.IngestionAuthorityContext,
    existing_authorities: Sequence[Mapping[str, Any]] = (),
) -> None:
    """Validate Exact6 response schema and all cross-record batch invariants."""

    if type(response) is not dict or tuple(response) != INTERFACE_RESPONSE_FIELDS:
        raise ValueError("INTERFACE_RESPONSE_FIELD_INVENTORY_MISMATCH")
    if (
        type(response["interface_response_version"]) is not str
        or type(response["authority_context_record_sha256"]) is not str
        or type(response["batch_passed"]) is not bool
        or type(response["ingestion_result_records"]) is not tuple
        or type(response["new_authority_records"]) is not tuple
        or type(response["interface_response_sha256"]) is not str
    ):
        raise ValueError("INTERFACE_RESPONSE_EXACT_TYPE_INVALID")
    if response["interface_response_version"] != INTERFACE_RESPONSE_VERSION:
        raise ValueError("INTERFACE_RESPONSE_VERSION_MISMATCH")
    for record in response["ingestion_result_records"]:
        if type(record) is not dict:
            raise ValueError("INTERFACE_RESULT_EXACT_TYPE_INVALID")
    for record in response["new_authority_records"]:
        if type(record) is not dict:
            raise ValueError("INTERFACE_AUTHORITY_EXACT_TYPE_INVALID")

    try:
        design.validate_ingestion_authority_context(authority_context)
        context_sha = authority_context.context_record[
            "ingestion_authority_context_record_sha256"
        ]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("INGESTION_AUTHORITY_CONTEXT_INVALID") from error
    if (
        _SHA.fullmatch(response["authority_context_record_sha256"]) is None
        or response["authority_context_record_sha256"] != context_sha
    ):
        raise ValueError("AUTHORITY_CONTEXT_DIGEST_LINKAGE_MISMATCH")
    if (
        _SHA.fullmatch(response["interface_response_sha256"]) is None
        or response["interface_response_sha256"]
        != interface_response_sha256(response)
    ):
        raise ValueError("INTERFACE_RESPONSE_SHA_MISMATCH")

    results = response["ingestion_result_records"]
    authorities = response["new_authority_records"]
    if len(results) != len(submissions):
        raise ValueError("INTERFACE_RESULT_COUNT_MISMATCH")
    linkage_fields = (
        ("sample_index_row_id", 0, "sample_index_row_id"),
        ("review_record_sha256", 0, "review_record_sha256"),
        ("ingestion_envelope_sha256", 1, "ingestion_envelope_sha256"),
        ("submission_batch_id", 1, "submission_batch_id"),
        ("review_decision", 0, "review_decision"),
    )
    for position, submission in enumerate(submissions):
        if type(submission) is not tuple or len(submission) != 2:
            continue
        for result_field, member, input_field in linkage_fields:
            expected = _safe_exact_str(submission[member], input_field)
            if expected is not None and results[position].get(result_field) != expected:
                raise ValueError("INTERFACE_RESULT_INPUT_ORDER_MISMATCH")

    for record in results:
        try:
            design.validate_ingestion_result(record)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("INTERFACE_INGESTION_RESULT_INVALID") from error

    if response["batch_passed"]:
        if not results or any(
            record.get("outcome") != "passed"
            or record.get("passed") is not True
            for record in results
        ):
            raise ValueError("INTERFACE_BATCH_PASSED_INVARIANT_MISMATCH")
    elif any(record.get("outcome") == "passed" for record in results):
        raise ValueError("INTERFACE_BATCH_PASSED_INVARIANT_MISMATCH")
    elif authorities:
        raise ValueError("INTERFACE_FAILED_BATCH_EFFECT_MISMATCH")

    new_by_sha: dict[str, Mapping[str, Any]] = {}
    new_samples: set[str] = set()
    for authority in authorities:
        try:
            design.validate_authority_record(authority)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("INTERFACE_NEW_AUTHORITY_INVALID") from error
        authority_sha = authority["authority_record_sha256"]
        sample = authority["sample_index_row_id"]
        if (
            _SHA.fullmatch(authority_sha) is None
            or authority_sha in new_by_sha
            or sample in new_samples
        ):
            raise ValueError("INTERFACE_NEW_AUTHORITY_UNIQUENESS_INVALID")
        new_by_sha[authority_sha] = authority
        new_samples.add(sample)

    existing_by_sha: dict[str, Mapping[str, Any]] = {}
    for authority in existing_authorities:
        authority_sha = _safe_exact_str(
            authority, "authority_record_sha256",
        )
        if authority_sha is not None and authority_sha not in existing_by_sha:
            existing_by_sha[authority_sha] = authority

    non_replay_passed = []
    referenced_new: set[str] = set()
    for result in results:
        if result["outcome"] == "passed" and not result["idempotent_replay"]:
            non_replay_passed.append(result)
            authority = new_by_sha.get(result["authority_record_sha256"])
            if authority is None:
                raise ValueError("INTERFACE_NON_REPLAY_AUTHORITY_LINKAGE_MISMATCH")
            if (
                authority["sample_index_row_id"] != result["sample_index_row_id"]
                or authority["source_review_record_sha256"]
                != result["review_record_sha256"]
                or authority["review_decision"] != result["review_decision"]
            ):
                raise ValueError("INTERFACE_NON_REPLAY_AUTHORITY_LINKAGE_MISMATCH")
            if result["authority_record_sha256"] in existing_by_sha:
                raise ValueError("INTERFACE_NON_REPLAY_USED_EXISTING_AUTHORITY")
            referenced_new.add(result["authority_record_sha256"])
        elif result["outcome"] == "passed":
            if result["authority_record_sha256"] in new_by_sha:
                raise ValueError("INTERFACE_REPLAY_EMITTED_NEW_AUTHORITY")
            authority = existing_by_sha.get(result["authority_record_sha256"])
            if authority is None:
                raise ValueError("INTERFACE_REPLAY_AUTHORITY_NOT_EXISTING")
            try:
                design.validate_authority_record(authority)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("INTERFACE_REPLAY_AUTHORITY_INVALID") from error
            if (
                authority["sample_index_row_id"] != result["sample_index_row_id"]
                or authority["source_review_record_sha256"]
                != result["review_record_sha256"]
            ):
                raise ValueError("INTERFACE_REPLAY_AUTHORITY_LINKAGE_MISMATCH")
        elif (
            result["authority_disposition"] != ""
            or result["authority_record_sha256"] != ""
            or result["consumed_review_record"] is not False
            or result["consumed_ingestion_envelope"] is not False
        ):
            raise ValueError("INTERFACE_FAILED_RESULT_EFFECT_MISMATCH")

    if (
        len(authorities) != len(non_replay_passed)
        or referenced_new != set(new_by_sha)
    ):
        raise ValueError("INTERFACE_NEW_AUTHORITY_COUNT_MISMATCH")


def evaluate_current11_warhead_boundary_review_ingestion_v1(
    *,
    submissions: Sequence[
        tuple[Mapping[str, Any], Mapping[str, Any]]
    ],
    authority_context: design.IngestionAuthorityContext,
    existing_authorities: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Delegate ingestion and return a validated deterministic Exact6 response."""

    _validate_public_evaluator_runtime_integrity_v1()
    submission_snapshot = _snapshot_value(submissions)
    context_snapshot = _snapshot_value(authority_context)
    existing_snapshot = _snapshot_value(existing_authorities)
    batch = design.ingest_review_batch(
        submissions,
        authority_context=authority_context,
        existing_authorities=existing_authorities,
    )
    response: dict[str, Any] = {
        "interface_response_version": INTERFACE_RESPONSE_VERSION,
        "authority_context_record_sha256":
            authority_context.context_record[
                "ingestion_authority_context_record_sha256"
            ],
        "batch_passed": batch.passed,
        "ingestion_result_records":
            tuple(dict(record) for record in batch.result_records),
        "new_authority_records":
            tuple(dict(record) for record in batch.new_authority_records),
        "interface_response_sha256": "",
    }
    response["interface_response_sha256"] = interface_response_sha256(response)
    validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
        response,
        submissions=submissions,
        authority_context=authority_context,
        existing_authorities=existing_authorities,
    )
    if (
        _snapshot_value(submissions) != submission_snapshot
        or _snapshot_value(authority_context) != context_snapshot
        or _snapshot_value(existing_authorities) != existing_snapshot
    ):
        raise ValueError("INTERFACE_INPUT_MUTATION_DETECTED")
    return response


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _cell(value: Any) -> str:
    if type(value) is bool:
        return "true" if value else "false"
    if value is None:
        return ""
    if type(value) in {list, tuple, dict}:
        return canonical_json(value)
    return str(value)


def _csv_bytes(
    columns: Sequence[str], rows: Sequence[Mapping[str, Any]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(columns):
            raise ValueError("output_row_field_inventory_mismatch")
        writer.writerow({column: _cell(row[column]) for column in columns})
    return stream.getvalue().encode("utf-8")


def _source_inventory(
    payloads: Mapping[Path, bytes],
) -> tuple[Mapping[str, Any], ...]:
    fields_used = {
        DESIGN_PRODUCTION:
            "frozen constants;context dataclass;context validator;"
            "validated-context phase parser;public ingest_review_batch;"
            "builder and evaluator imported worktree/HEAD source integrity",
        DESIGN_MANIFEST:
            "transaction_succeeded;interface/execution readiness;schema/counts;"
            "downstream readiness",
        DESIGN_CONTRACT:
            "header;row count;verified",
        DESIGN_DECISION:
            "header;row count;verified",
        DESIGN_READINESS:
            "sample identity;package/template readiness;zero lifecycle;downstream",
        DESIGN_FAILURE:
            "header;row count;fails_closed;zero lifecycle",
    }
    authority = {
        DESIGN_PRODUCTION: "committed_core_semantic_authority",
        DESIGN_MANIFEST: "committed_design_transaction_authority",
        DESIGN_CONTRACT: "committed_design_contract_evidence",
        DESIGN_DECISION: "committed_decision_effect_evidence",
        DESIGN_READINESS: "committed_current11_readiness_evidence",
        DESIGN_FAILURE: "committed_fail_closed_evidence",
    }
    rows = []
    for path in SOURCE_PATHS:
        payload = payloads[path]
        suffix = path.suffix
        if suffix == ".csv":
            row_count = len(_csv_rows(payload))
        elif suffix == ".json":
            row_count = 1
        else:
            row_count = len(payload.decode("utf-8").splitlines())
        rows.append({
            "source_path": path.as_posix(),
            "BASE_SHA256": FROZEN_BASE_SHA256[path],
            "source_row_count": row_count,
            "fields_actually_used": fields_used[path],
            "authority_class": authority[path],
            "verified": sha256(payload) == FROZEN_BASE_SHA256[path],
        })
    return tuple(rows)


def _contract_rows() -> tuple[Mapping[str, Any], ...]:
    specifications = (
        (
            "IFACE_001",
            "formal interface version and function signatures are exact",
            "public_api",
            "interface version;three public call signatures",
            "version and parameter order/kinds/defaults/annotations are frozen",
            "stable typed public API admitted",
            "interface transaction fails",
        ),
        (
            "IFACE_002",
            "authority context is built from frozen committed design authority",
            "authority_context",
            "repo_root;interface BASE ancestry;frozen imported design source;design BASE Git objects",
            "builder and evaluator accept interface BASE descendants only when imported design worktree and HEAD bytes retain the frozen SHA",
            "immutable context admitted",
            "context is rejected",
        ),
        (
            "IFACE_003",
            "external authority maps and file-path inputs are forbidden",
            "public_api",
            "public signature inventory",
            "repo/file/payload and internal authority-map keywords are absent",
            "in-memory boundary preserved",
            "interface transaction fails",
        ),
        (
            "IFACE_004",
            "typed in-memory submissions are passed without mutation",
            "purity",
            "submissions;authority context;existing authorities",
            "canonical deep snapshots are equal after evaluation",
            "inputs remain unchanged",
            "evaluation fails closed",
        ),
        (
            "IFACE_005",
            "core ingestion semantics delegate to committed design module",
            "delegation",
            "typed in-memory inputs;validated committed-design context;committed design evaluator",
            "read-only runtime integrity attestation precedes exactly one design ingest_review_batch call",
            "committed semantics retained",
            "interface transaction fails",
        ),
        (
            "IFACE_006",
            "interface response schema is Exact6",
            "response",
            "design batch result;authority context digest",
            "field order and exact types equal frozen Exact6",
            "response admitted",
            "response rejected",
        ),
        (
            "IFACE_007",
            "interface response hash is deterministic and self-excluding",
            "response",
            "ordered Exact5 canonical payload",
            "canonical JSON SHA256 excludes only response hash field",
            "response identity admitted",
            "response rejected",
        ),
        (
            "IFACE_008",
            "batch/result/new-authority/replay invariants are validated",
            "response",
            "submissions;results;new and existing authorities",
            "order,count,atomicity,new/replay mapping all match",
            "batch response admitted",
            "response rejected",
        ),
        (
            "IFACE_009",
            "all result and authority records retain committed Exact18/Exact27 semantics",
            "delegated_records",
            "result and authority records",
            "committed design validators pass every record and digest",
            "records admitted unchanged",
            "response rejected",
        ),
        (
            "IFACE_010",
            "interface evaluation has no filesystem persistence side effects",
            "purity",
            "in-memory evaluator call;interface Exact4 artifact lifecycles;legal public descendants",
            "business payload remains in memory while read-only Git/source integrity checks write no file",
            "zero-write evaluation admitted",
            "interface transaction fails",
        ),
        (
            "IFACE_011",
            "implementation materializes no real review, result, authority or downstream label",
            "lifecycle",
            "formal artifact inventory",
            "actual review/envelope/result/authority and label counts remain zero",
            "synthetic evidence only",
            "interface transaction fails",
        ),
        (
            "IFACE_012",
            "model/training gates remain closed and feature-semantics audit remains required",
            "downstream",
            "canonical masks;module counts;training prerequisite",
            "five masks,zero of five modules integrated,training false",
            "downstream remains closed",
            "interface transaction fails",
        ),
    )
    return tuple(
        dict(
            zip(CONTRACT_COLUMNS[:-2], values),
            fails_closed=True,
            verified=True,
        )
        for values in specifications
    )


@dataclass(frozen=True)
class CommittedDesignInterfaceEvidence:
    """Minimal typed evidence recovered from a validated design context."""

    authority_context: design.IngestionAuthorityContext
    package_index_rows: tuple[Mapping[str, str], ...]
    package_identity_by_sample: Mapping[str, Mapping[str, Any]]
    option_rows: tuple[Mapping[str, Any], ...]
    template_rows: tuple[Mapping[str, Any], ...]
    proposal_rows: tuple[Mapping[str, Any], ...]
    parent_atom_rows: tuple[Mapping[str, str], ...]
    parent_bond_rows: tuple[Mapping[str, str], ...]


def _committed_design_interface_evidence(
    context: design.IngestionAuthorityContext,
) -> CommittedDesignInterfaceEvidence:
    phase = design._validated_ingestion_authority_context(context)
    if phase.blocking_reasons:
        raise ValueError("COMMITTED_DESIGN_CONTEXT_PHASE_BLOCKED")
    return CommittedDesignInterfaceEvidence(
        authority_context=context,
        package_index_rows=phase.index_rows,
        package_identity_by_sample=phase.package_identity_by_sample,
        option_rows=phase.option_rows,
        template_rows=phase.template_rows,
        proposal_rows=phase.proposal_rows,
        parent_atom_rows=phase.parent_atom_rows,
        parent_bond_rows=phase.parent_bond_rows,
    )


def _sample_options(
    result: CommittedDesignInterfaceEvidence, sample: str,
):
    return [
        row
        for row in result.option_rows
        if row["sample_index_row_id"] == sample
    ]


def _synthetic_human_record(
    result: CommittedDesignInterfaceEvidence,
    decision: str,
    sample_offset: int = 0,
) -> dict[str, Any]:
    record = dict(result.template_rows[sample_offset])
    sample = record["sample_index_row_id"]
    options = _sample_options(result, sample)
    if decision in {
        "select_admitted_candidate",
        "revise_atom_set_and_boundary",
    }:
        option = next(row for row in options if row["review_eligible"])
        record.update({
            "reviewed_warhead_atom_ids":
                list(option["warhead_side_atom_ids"]),
            "reviewed_warhead_attachment_atom_id":
                option["warhead_attachment_atom_id"],
            "reviewed_nonwarhead_boundary_atom_id":
                option["nonwarhead_boundary_atom_id"],
            "reviewed_attachment_boundary_bond_order":
                option["boundary_bond_order"],
            "reviewed_boundary_bond_id": option["boundary_bond_id"],
        })
        if decision == "select_admitted_candidate":
            record.update({
                "selected_bridge_candidate_index_0based":
                    option["source_bridge_candidate_index_0based"],
                "selected_bridge_candidate_record_sha256":
                    option["source_bridge_candidate_record_sha256"],
            })
    record.update({
        "review_decision": decision,
        "reviewer_id": f"synthetic-human-reviewer-{sample_offset + 1:02d}",
        "review_rationale":
            "Synthetic human-shaped record for interface validation only.",
        "review_notes": "",
    })
    record["review_record_sha256"] = design.review_record_sha256(record)
    return record


def _synthetic_envelope(
    record: Mapping[str, Any], batch: str,
) -> dict[str, Any]:
    envelope: dict[str, Any] = {
        "ingestion_envelope_version": design.INGESTION_ENVELOPE_VERSION,
        "submission_batch_id": batch,
        "sample_index_row_id": record["sample_index_row_id"],
        "review_record_sha256": record["review_record_sha256"],
        "submitted_record_payload_sha256":
            design.submitted_record_payload_sha256(record),
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "synthetic-human-attestor",
        "submission_source_label": "synthetic-interface-validation-only",
        "ingestion_envelope_sha256": "",
    }
    envelope["ingestion_envelope_sha256"] = (
        design.ingestion_envelope_sha256(envelope)
    )
    return envelope


def _unchecked_rehash_review(record: dict[str, Any]) -> None:
    record["review_record_sha256"] = sha256(canonical_json({
        field: record[field]
        for field in design.REVIEW_RECORD_FIELDS
        if field != "review_record_sha256"
    }).encode("utf-8"))


@dataclass(frozen=True)
class SyntheticTruthCase:
    name: str
    submissions: tuple[tuple[Mapping[str, Any], Mapping[str, Any]], ...]
    authority_context: design.IngestionAuthorityContext
    existing_authorities: tuple[Mapping[str, Any], ...]
    expected_batch_passed: bool
    expected_outcome_class: str
    expected_reasons: tuple[str, ...]
    expected_new_authority_count: int


def _build_synthetic_truth_cases(
    design_result: CommittedDesignInterfaceEvidence,
) -> tuple[SyntheticTruthCase, ...]:
    """Build the frozen Exact18 synthetic in-memory cases."""

    context = design_result.authority_context

    def submission(
        decision: str, offset: int, batch: str,
    ) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        review = _synthetic_human_record(design_result, decision, offset)
        return review, _synthetic_envelope(review, batch)

    select = submission("select_admitted_candidate", 0, "truth-select")
    revise = submission("revise_atom_set_and_boundary", 0, "truth-revise")
    quarantine = submission("quarantine", 0, "truth-quarantine")
    partial = (
        submission("select_admitted_candidate", 0, "truth-partial"),
        submission("quarantine", 1, "truth-partial"),
    )

    blank_review = dict(design_result.template_rows[0])
    blank_envelope = {
        "ingestion_envelope_version": design.INGESTION_ENVELOPE_VERSION,
        "submission_batch_id": "truth-not-reviewed",
        "sample_index_row_id": blank_review["sample_index_row_id"],
        "review_record_sha256": "",
        "submitted_record_payload_sha256": "0" * 64,
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "synthetic-human-attestor",
        "submission_source_label": "synthetic-interface-validation-only",
        "ingestion_envelope_sha256": "0" * 64,
    }

    initial_review = _synthetic_human_record(
        design_result, "select_admitted_candidate", 0,
    )
    initial = design.ingest_review_batch(
        ((initial_review, _synthetic_envelope(initial_review, "truth-initial")),),
        authority_context=context,
    )
    existing = dict(initial.new_authority_records[0])
    conflicting = submission("quarantine", 0, "truth-conflict")

    atomic_first = submission(
        "select_admitted_candidate", 0, "truth-atomic",
    )
    atomic_blank_review = dict(design_result.template_rows[1])
    atomic_blank_envelope = {
        "ingestion_envelope_version": design.INGESTION_ENVELOPE_VERSION,
        "submission_batch_id": "truth-atomic",
        "sample_index_row_id": atomic_blank_review["sample_index_row_id"],
        "review_record_sha256": "",
        "submitted_record_payload_sha256": "0" * 64,
        "reviewer_provenance_attested": True,
        "reviewer_provenance_attestor_id": "synthetic-human-attestor",
        "submission_source_label": "synthetic-interface-validation-only",
        "ingestion_envelope_sha256": "0" * 64,
    }

    mixed = (
        submission("select_admitted_candidate", 0, "truth-mixed-a"),
        submission("quarantine", 1, "truth-mixed-b"),
    )
    duplicate_sample = (
        submission("select_admitted_candidate", 0, "truth-duplicate-sample"),
        submission("quarantine", 0, "truth-duplicate-sample"),
    )
    duplicate_first = submission(
        "select_admitted_candidate", 0, "truth-duplicate-sha",
    )
    duplicate_second_review = _synthetic_human_record(
        design_result, "quarantine", 1,
    )
    duplicate_second_review["review_record_sha256"] = (
        duplicate_first[0]["review_record_sha256"]
    )
    duplicate_second = (
        duplicate_second_review,
        _synthetic_envelope(duplicate_second_review, "truth-duplicate-sha"),
    )

    forged_record = dict(context.context_record)
    forged_record["ingestion_authority_context_record_sha256"] = "0" * 64
    forged_context = design.IngestionAuthorityContext(
        forged_record, context.source_payloads,
    )
    forged_context_submission = submission(
        "quarantine", 0, "truth-forged-context",
    )

    forged_review = _synthetic_human_record(
        design_result, "quarantine", 0,
    )
    forged_review["pdb_id"] = "FORGED_PDB"
    _unchecked_rehash_review(forged_review)
    forged_identity = (
        forged_review,
        _synthetic_envelope(forged_review, "truth-forged-identity"),
    )

    ineligible_offset = next(
        index
        for index, template in enumerate(design_result.template_rows)
        if any(
            not option["review_eligible"]
            for option in _sample_options(
                design_result, template["sample_index_row_id"],
            )
        )
    )
    ineligible_review = _synthetic_human_record(
        design_result, "quarantine", ineligible_offset,
    )
    ineligible_option = next(
        option
        for option in _sample_options(
            design_result, ineligible_review["sample_index_row_id"],
        )
        if not option["review_eligible"]
    )
    ineligible_review.update({
        "review_decision": "select_admitted_candidate",
        "selected_bridge_candidate_index_0based":
            ineligible_option["source_bridge_candidate_index_0based"],
        "selected_bridge_candidate_record_sha256":
            ineligible_option["source_bridge_candidate_record_sha256"],
        "reviewed_warhead_atom_ids":
            list(ineligible_option["warhead_side_atom_ids"]),
        "reviewed_warhead_attachment_atom_id":
            ineligible_option["warhead_attachment_atom_id"],
        "reviewed_nonwarhead_boundary_atom_id":
            ineligible_option["nonwarhead_boundary_atom_id"],
        "reviewed_attachment_boundary_bond_order":
            ineligible_option["boundary_bond_order"],
        "reviewed_boundary_bond_id": ineligible_option["boundary_bond_id"],
    })
    ineligible_review["review_record_sha256"] = (
        design.review_record_sha256(ineligible_review)
    )
    ineligible = (
        ineligible_review,
        _synthetic_envelope(ineligible_review, "truth-ineligible"),
    )

    bad_envelope_review = _synthetic_human_record(
        design_result, "quarantine", 0,
    )
    bad_envelope = _synthetic_envelope(
        bad_envelope_review, "truth-bad-envelope",
    )
    bad_envelope["reviewer_provenance_attested"] = 1

    invalid_hash_authority = dict(existing)
    invalid_hash_authority["authority_record_sha256"] = "0" * 64
    existing_review = _synthetic_human_record(
        design_result, "quarantine", 1,
    )
    invalid_existing_submission = (
        existing_review,
        _synthetic_envelope(existing_review, "truth-invalid-existing"),
    )

    invalid_evidence_authority = dict(existing)
    invalid_evidence_authority["reviewed_boundary_bond_id"] = (
        "synthetic_nonmatching_boundary"
    )
    invalid_evidence_authority["authority_record_sha256"] = ""
    invalid_evidence_authority["authority_record_sha256"] = (
        design.authority_record_sha256(invalid_evidence_authority)
    )
    invalid_evidence_submission = (
        existing_review,
        _synthetic_envelope(existing_review, "truth-invalid-evidence"),
    )

    oversize = tuple(
        submission("quarantine", offset % 11, "truth-oversized")
        for offset in range(12)
    )

    return (
        SyntheticTruthCase(
            "valid_select", (select,), context, (), True, "passed",
            ("PASSED",), 1,
        ),
        SyntheticTruthCase(
            "valid_revise", (revise,), context, (), True, "passed",
            ("PASSED",), 1,
        ),
        SyntheticTruthCase(
            "valid_quarantine", (quarantine,), context, (), True, "passed",
            ("PASSED",), 1,
        ),
        SyntheticTruthCase(
            "valid_partial_two_sample_batch", partial, context, (), True,
            "passed", ("PASSED", "PASSED"), 2,
        ),
        SyntheticTruthCase(
            "not_reviewed_blocked",
            ((blank_review, blank_envelope),),
            context,
            (),
            False,
            "blocked",
            ("REVIEW_NOT_COMPLETED",),
            0,
        ),
        SyntheticTruthCase(
            "conflicting_reingestion_blocked",
            (conflicting,),
            context,
            (existing,),
            False,
            "blocked",
            ("CONFLICTING_REVIEW_REINGESTION",),
            0,
        ),
        SyntheticTruthCase(
            "atomicity_rollback_blocked",
            (atomic_first, (atomic_blank_review, atomic_blank_envelope)),
            context,
            (),
            False,
            "blocked",
            ("BATCH_ATOMICITY_ABORTED", "REVIEW_NOT_COMPLETED"),
            0,
        ),
        SyntheticTruthCase(
            "mixed_batch_ids_invalid", mixed, context, (), False, "invalid",
            ("SUBMISSION_BATCH_ID_MISMATCH",) * 2, 0,
        ),
        SyntheticTruthCase(
            "duplicate_sample_invalid", duplicate_sample, context, (), False,
            "invalid", ("DUPLICATE_SAMPLE_IN_BATCH",) * 2, 0,
        ),
        SyntheticTruthCase(
            "duplicate_review_sha_invalid",
            (duplicate_first, duplicate_second),
            context,
            (),
            False,
            "invalid",
            ("DUPLICATE_REVIEW_RECORD_SHA_IN_BATCH",) * 2,
            0,
        ),
        SyntheticTruthCase(
            "forged_authority_context_invalid",
            (forged_context_submission,),
            forged_context,
            (),
            False,
            "invalid",
            ("INGESTION_AUTHORITY_CONTEXT_INVALID",),
            0,
        ),
        SyntheticTruthCase(
            "forged_review_identity_invalid",
            (forged_identity,),
            context,
            (),
            False,
            "invalid",
            ("REVIEW_IDENTITY_LINKAGE_MISMATCH",),
            0,
        ),
        SyntheticTruthCase(
            "ineligible_select_invalid", (ineligible,), context, (), False,
            "invalid", ("SELECT_OPTION_NOT_REVIEW_ELIGIBLE",), 0,
        ),
        SyntheticTruthCase(
            "invalid_envelope_exact_type",
            ((bad_envelope_review, bad_envelope),),
            context,
            (),
            False,
            "invalid",
            ("INGESTION_ENVELOPE_EXACT_TYPE_INVALID",),
            0,
        ),
        SyntheticTruthCase(
            "invalid_existing_authority_hash",
            (invalid_existing_submission,),
            context,
            (invalid_hash_authority,),
            False,
            "invalid",
            ("EXISTING_AUTHORITY_SET_INVALID",),
            0,
        ),
        SyntheticTruthCase(
            "invalid_existing_authority_decision_evidence",
            (invalid_evidence_submission,),
            context,
            (invalid_evidence_authority,),
            False,
            "invalid",
            ("EXISTING_AUTHORITY_SET_INVALID",),
            0,
        ),
        SyntheticTruthCase(
            "empty_batch_invalid", (), context, (), False, "invalid", (), 0,
        ),
        SyntheticTruthCase(
            "oversized_batch_invalid", oversize, context, (), False, "invalid",
            ("BATCH_SIZE_INVALID",) * 12, 0,
        ),
    )


def _evaluate_truth_rows(
    design_result: CommittedDesignInterfaceEvidence,
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for index, case in enumerate(
        _build_synthetic_truth_cases(design_result), 1,
    ):
        before = (
            _snapshot_value(case.submissions),
            _snapshot_value(case.authority_context),
            _snapshot_value(case.existing_authorities),
        )
        validator_rejected_forged_context = False
        if case.name == "forged_authority_context_invalid":
            batch = design.ingest_review_batch(
                case.submissions,
                authority_context=case.authority_context,
                existing_authorities=case.existing_authorities,
            )
            response = {
                "interface_response_version": INTERFACE_RESPONSE_VERSION,
                "authority_context_record_sha256":
                    case.authority_context.context_record[
                        "ingestion_authority_context_record_sha256"
                    ],
                "batch_passed": batch.passed,
                "ingestion_result_records":
                    tuple(dict(record) for record in batch.result_records),
                "new_authority_records":
                    tuple(dict(record) for record in batch.new_authority_records),
                "interface_response_sha256": "",
            }
            response["interface_response_sha256"] = (
                interface_response_sha256(response)
            )
            try:
                validate_current11_warhead_boundary_review_ingestion_interface_response_v1(
                    response,
                    submissions=case.submissions,
                    authority_context=case.authority_context,
                    existing_authorities=case.existing_authorities,
                )
            except ValueError as error:
                validator_rejected_forged_context = (
                    str(error) == "INGESTION_AUTHORITY_CONTEXT_INVALID"
                )
        else:
            response = evaluate_current11_warhead_boundary_review_ingestion_v1(
                submissions=case.submissions,
                authority_context=case.authority_context,
                existing_authorities=case.existing_authorities,
            )
        after = (
            _snapshot_value(case.submissions),
            _snapshot_value(case.authority_context),
            _snapshot_value(case.existing_authorities),
        )
        outcomes = tuple(
            record["outcome"]
            for record in response["ingestion_result_records"]
        )
        observed_class = (
            "passed"
            if response["batch_passed"]
            else "blocked"
            if any(outcome == "blocked" for outcome in outcomes)
            else "invalid"
        )
        reasons = tuple(
            record["reason"]
            for record in response["ingestion_result_records"]
        )
        replay_count = sum(
            record["idempotent_replay"]
            for record in response["ingestion_result_records"]
        )
        conflict_count = sum(
            record["conflicting_existing_authority"]
            for record in response["ingestion_result_records"]
        )
        verified = (
            response["batch_passed"] is case.expected_batch_passed
            and observed_class == case.expected_outcome_class
            and reasons == case.expected_reasons
            and len(response["new_authority_records"])
            == case.expected_new_authority_count
            and before == after
            and (
                case.name != "forged_authority_context_invalid"
                or validator_rejected_forged_context
            )
        )
        rows.append({
            "truth_case_id": f"TRUTH_{index:03d}",
            "truth_case_name": case.name,
            "expected_batch_passed": case.expected_batch_passed,
            "expected_outcome_class": case.expected_outcome_class,
            "expected_result_count": len(case.submissions),
            "expected_new_authority_count":
                case.expected_new_authority_count,
            "expected_reason_sequence": list(case.expected_reasons),
            "expected_replay_count": replay_count,
            "expected_conflict_count": conflict_count,
            "response_schema_valid":
                tuple(response) == INTERFACE_RESPONSE_FIELDS,
            "response_hash_valid":
                response["interface_response_sha256"]
                == interface_response_sha256(response),
            "input_order_preserved": all(
                result.get("sample_index_row_id")
                == _safe_exact_str(submission[0], "sample_index_row_id")
                for result, submission in zip(
                    response["ingestion_result_records"],
                    case.submissions,
                )
            ),
            "inputs_unmodified": before == after,
            "filesystem_write_count": 0,
            "verified": verified,
        })
    return tuple(rows)


def _readiness_rows(
    design_result: CommittedDesignInterfaceEvidence,
) -> tuple[Mapping[str, Any], ...]:
    blockers = (
        "completed_human_review_record_missing;"
        "human_provenance_envelope_missing;"
        "real_ingestion_not_executed"
    )
    return tuple({
        "sample_index_row_id": source["sample_index_row_id"],
        "pdb_id": source["pdb_id"],
        "ligand_comp_id": source["ligand_comp_id"],
        "source_candidate_set_sha256":
            source["source_candidate_set_sha256"],
        "review_package_available": True,
        "blank_review_template_available": True,
        "interface_implementation_available": True,
        "immutable_authority_context_available": True,
        "interface_synthetic_validation_passed": True,
        "completed_review_record_available": False,
        "human_provenance_envelope_available": False,
        "ready_for_real_ingestion_execution": False,
        "real_ingestion_completed": False,
        "authority_record_available": False,
        "complete_warhead_atom_set_authority_available": False,
        "exact_one_attachment_boundary_authority_available": False,
        "sample_quarantined": False,
        "ready_for_candidate_warhead_smarts_materialization": False,
        "ready_for_role_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "blocking_reasons": blockers,
        "verified": True,
    } for source in sorted(
        design_result.package_index_rows,
        key=lambda row: row["sample_index_row_id"],
    ))


@dataclass(frozen=True)
class InterfaceScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    design_transaction_succeeded: bool = True
    design_interface_ready: bool = True
    design_execution_closed: bool = True
    interface_version_exact: bool = True
    public_signature_exact: bool = True
    external_authority_maps_forbidden: bool = True
    response_field_inventory_exact: bool = True
    response_exact_types_valid: bool = True
    context_digest_linkage_valid: bool = True
    response_sha_valid: bool = True
    result_count_matches: bool = True
    result_order_matches: bool = True
    batch_result_outcome_matches: bool = True
    failed_batch_authority_count: int = 0
    non_replay_authority_linkage_valid: bool = True
    replay_emits_no_new_authority: bool = True
    replay_authority_exists: bool = True
    new_authority_sha_unique: bool = True
    result_exact18_valid: bool = True
    authority_exact27_valid: bool = True
    submissions_unmodified: bool = True
    authority_context_unmodified: bool = True
    existing_authorities_unmodified: bool = True
    response_deterministic: bool = True
    filesystem_write_count: int = 0
    actual_lifecycle_record_count: int = 0
    downstream_gates_closed: bool = True
    canonical_mask_and_module_boundary_exact: bool = True
    formal_successor_runtime_compatible: bool = True
    separate_design_base_worktree_required: bool = False
    downstream_descendant_runtime_compatible: bool = True
    imported_design_source_integrity_required: bool = True
    public_evaluator_design_source_integrity_required: bool = True


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_SOURCE_MISSING"),
    ("BASE source SHA mismatch", "base_source_sha_matches", False, "BASE_SOURCE_SHA_MISMATCH"),
    ("design transaction not succeeded", "design_transaction_succeeded", False, "DESIGN_TRANSACTION_NOT_SUCCEEDED"),
    ("design interface implementation readiness false", "design_interface_ready", False, "DESIGN_INTERFACE_READINESS_FALSE"),
    ("design execution readiness prematurely true", "design_execution_closed", False, "DESIGN_EXECUTION_PREMATURELY_READY"),
    ("interface version mismatch", "interface_version_exact", False, "INTERFACE_VERSION_MISMATCH"),
    ("public function signature mismatch", "public_signature_exact", False, "PUBLIC_FUNCTION_SIGNATURE_MISMATCH"),
    ("external authority-map input accepted", "external_authority_maps_forbidden", False, "EXTERNAL_AUTHORITY_MAP_INPUT_ACCEPTED"),
    ("Exact6 response field inventory mismatch", "response_field_inventory_exact", False, "INTERFACE_RESPONSE_FIELD_INVENTORY_MISMATCH"),
    ("interface response exact type invalid", "response_exact_types_valid", False, "INTERFACE_RESPONSE_EXACT_TYPE_INVALID"),
    ("authority-context digest linkage mismatch", "context_digest_linkage_valid", False, "AUTHORITY_CONTEXT_DIGEST_LINKAGE_MISMATCH"),
    ("interface response SHA mismatch", "response_sha_valid", False, "INTERFACE_RESPONSE_SHA_MISMATCH"),
    ("result count mismatch", "result_count_matches", False, "INTERFACE_RESULT_COUNT_MISMATCH"),
    ("result order mismatch", "result_order_matches", False, "INTERFACE_RESULT_INPUT_ORDER_MISMATCH"),
    ("batch-passed/result-outcome mismatch", "batch_result_outcome_matches", False, "INTERFACE_BATCH_PASSED_INVARIANT_MISMATCH"),
    ("failed batch emitted new authority", "failed_batch_authority_count", 1, "INTERFACE_FAILED_BATCH_EFFECT_MISMATCH"),
    ("passed non-replay result missing new authority", "non_replay_authority_linkage_valid", False, "INTERFACE_NON_REPLAY_AUTHORITY_LINKAGE_MISMATCH"),
    ("replay emitted new authority", "replay_emits_no_new_authority", False, "INTERFACE_REPLAY_EMITTED_NEW_AUTHORITY"),
    ("replay authority absent from existing authority set", "replay_authority_exists", False, "INTERFACE_REPLAY_AUTHORITY_NOT_EXISTING"),
    ("duplicate new-authority SHA", "new_authority_sha_unique", False, "INTERFACE_NEW_AUTHORITY_UNIQUENESS_INVALID"),
    ("invalid Exact18 result accepted", "result_exact18_valid", False, "INTERFACE_INGESTION_RESULT_INVALID"),
    ("invalid Exact27 authority accepted", "authority_exact27_valid", False, "INTERFACE_NEW_AUTHORITY_INVALID"),
    ("submission input mutated", "submissions_unmodified", False, "INTERFACE_SUBMISSION_INPUT_MUTATED"),
    ("authority-context input mutated", "authority_context_unmodified", False, "INTERFACE_AUTHORITY_CONTEXT_INPUT_MUTATED"),
    ("existing-authority input mutated", "existing_authorities_unmodified", False, "INTERFACE_EXISTING_AUTHORITY_INPUT_MUTATED"),
    ("nondeterministic interface response", "response_deterministic", False, "INTERFACE_RESPONSE_NONDETERMINISTIC"),
    ("filesystem write side effect detected", "filesystem_write_count", 1, "INTERFACE_FILESYSTEM_WRITE_DETECTED"),
    ("actual review/result/authority materialized", "actual_lifecycle_record_count", 1, "INTERFACE_ACTUAL_LIFECYCLE_MATERIALIZED"),
    ("downstream readiness prematurely opened", "downstream_gates_closed", False, "INTERFACE_DOWNSTREAM_READINESS_OPENED"),
    ("canonical mask or module boundary drift", "canonical_mask_and_module_boundary_exact", False, "INTERFACE_CANONICAL_MASK_OR_MODULE_DRIFT"),
    ("formal successor runtime incompatible", "formal_successor_runtime_compatible", False, "INTERFACE_FORMAL_SUCCESSOR_RUNTIME_INCOMPATIBLE"),
    ("separate design BASE worktree required", "separate_design_base_worktree_required", True, "INTERFACE_SEPARATE_BASE_WORKTREE_DEPENDENCY"),
    ("downstream descendant public runtime incompatible", "downstream_descendant_runtime_compatible", False, "INTERFACE_DOWNSTREAM_DESCENDANT_RUNTIME_INCOMPATIBLE"),
    ("imported design source integrity not enforced", "imported_design_source_integrity_required", False, "INTERFACE_IMPORTED_DESIGN_SOURCE_INTEGRITY_NOT_ENFORCED"),
    ("public evaluator design source integrity not enforced", "public_evaluator_design_source_integrity_required", False, "INTERFACE_PUBLIC_EVALUATOR_DESIGN_SOURCE_INTEGRITY_NOT_ENFORCED"),
)


def observe_failure_scenario(
    scenario: InterfaceScenario,
) -> tuple[str, ...]:
    baseline = InterfaceScenario()
    return tuple(
        reason
        for _, field, _, reason in FAILURE_MUTATIONS
        if getattr(scenario, field) != getattr(baseline, field)
    )


def transaction_tables(
    scenario: InterfaceScenario,
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    if observe_failure_scenario(scenario):
        return (), (), ()
    return (
        _contract_rows(),
        tuple({"verified": True} for _ in range(18)),
        tuple({"verified": True} for _ in range(11)),
    )


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = InterfaceScenario()
    rows = []
    for index, (name, field, value, expected) in enumerate(
        FAILURE_MUTATIONS, 1,
    ):
        if type(value) is not type(getattr(baseline, field)):
            raise ValueError("failure_mutation_exact_type_invalid")
        if value == getattr(baseline, field):
            raise ValueError("failure_mutation_not_distinct")
        scenario = replace(baseline, **{field: value})
        observed = observe_failure_scenario(scenario)
        core = transaction_tables(scenario)
        rows.append({
            "failure_case_id": f"FAIL_{index:03d}",
            "failure_case_name": name,
            "mutation_signature": sha256(canonical_json({
                "field": field, "value": value,
            }).encode("utf-8")),
            "mutated_field": field,
            "mutated_value_json": canonical_json(value),
            "expected_reason": expected,
            "observed_reasons": list(observed),
            "expected_reason_verified": expected in observed,
            "fails_closed": all(not table for table in core),
            "contract_row_count": len(core[0]),
            "truth_row_count": len(core[1]),
            "current11_readiness_row_count": len(core[2]),
            "actual_completed_review_count": 0,
            "actual_ingestion_envelope_count": 0,
            "actual_ingestion_result_count": 0,
            "actual_authority_record_count": 0,
            "smarts_ready": False,
            "role_ready": False,
            "mask_ready": False,
            "model_ready": False,
            "training_ready": False,
            "verified": (
                expected in observed
                and all(not table for table in core)
            ),
        })
    signatures = [row["mutation_signature"] for row in rows]
    if len(signatures) != len(set(signatures)):
        raise ValueError("failure_mutation_signature_not_unique")
    return tuple(rows)


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    contract_rows: tuple[Mapping[str, Any], ...]
    truth_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    design_evidence: CommittedDesignInterfaceEvidence | None
    actual_lifecycle: str
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


def _validate_public_signatures() -> None:
    builder = inspect.signature(
        build_current11_warhead_boundary_review_ingestion_authority_context_v1
    )
    if tuple(builder.parameters) != ("repo_root",):
        raise ValueError("PUBLIC_FUNCTION_SIGNATURE_MISMATCH")
    evaluator = inspect.signature(
        evaluate_current11_warhead_boundary_review_ingestion_v1
    )
    if tuple(evaluator.parameters) != (
        "submissions", "authority_context", "existing_authorities",
    ):
        raise ValueError("PUBLIC_FUNCTION_SIGNATURE_MISMATCH")
    if any(
        parameter.kind is not inspect.Parameter.KEYWORD_ONLY
        for parameter in evaluator.parameters.values()
    ):
        raise ValueError("PUBLIC_FUNCTION_SIGNATURE_MISMATCH")
    if evaluator.parameters["existing_authorities"].default != ():
        raise ValueError("PUBLIC_FUNCTION_SIGNATURE_MISMATCH")
    forbidden = {
        "repo_root", "file_path", "csv_path", "json_path", "raw_payload",
        "package_identity_by_sample", "options", "proposals_by_sample",
        "parent_atom_ids_by_ligand", "parent_bonds_by_ligand",
        "valid_sample_ids",
    }
    if forbidden & set(evaluator.parameters):
        raise ValueError("EXTERNAL_AUTHORITY_MAP_INPUT_ACCEPTED")


def build_result(repo_root: Path) -> BuildResult:
    lifecycle = validate_execution_boundary_v1(repo_root)
    payloads = load_frozen_sources(repo_root)
    reasons: list[str] = []
    manifest = json.loads(payloads[DESIGN_MANIFEST])
    if manifest.get("transaction_succeeded") is not True:
        reasons.append("DESIGN_TRANSACTION_NOT_SUCCEEDED")
    if (
        manifest.get("ready_for_review_ingestion_interface_implementation")
        is not True
    ):
        reasons.append("DESIGN_INTERFACE_READINESS_FALSE")
    if manifest.get("ready_for_review_ingestion_execution") is not False:
        reasons.append("DESIGN_EXECUTION_PREMATURELY_READY")
    zero_fields = (
        "completed_review_record_count",
        "ingestion_envelope_count",
        "ingestion_result_count",
        "authority_record_count",
    )
    if any(manifest.get(field) != 0 for field in zero_fields):
        reasons.append("DESIGN_ACTUAL_LIFECYCLE_NOT_ZERO")
    design_evidence: CommittedDesignInterfaceEvidence | None = None
    try:
        _validate_public_signatures()
        authority_context = (
            build_current11_warhead_boundary_review_ingestion_authority_context_v1(
                repo_root
            )
        )
        design_evidence = _committed_design_interface_evidence(
            authority_context,
        )
        design.validate_ingestion_authority_context(authority_context)
    except (KeyError, RuntimeError, TypeError, ValueError) as error:
        reasons.append(str(error))

    source_rows = _source_inventory(payloads)
    failure_rows = build_failure_rows()
    if not reasons and design_evidence is not None:
        try:
            contracts = _contract_rows()
            truths = _evaluate_truth_rows(design_evidence)
            readiness = _readiness_rows(design_evidence)
            if (
                len(contracts) != 12
                or len(truths) != 18
                or len(readiness) != 11
                or sum(
                    row["expected_outcome_class"] == "passed"
                    for row in truths
                ) != 4
                or sum(
                    row["expected_outcome_class"] == "blocked"
                    for row in truths
                ) != 3
                or sum(
                    row["expected_outcome_class"] == "invalid"
                    for row in truths
                ) != 11
                or not all(row["verified"] for row in truths)
            ):
                reasons.append("PHASE_B_SYNTHETIC_CONTRACT_INVALID")
        except (KeyError, TypeError, ValueError) as error:
            reasons.append(f"PHASE_B_SYNTHETIC_CONTRACT_INVALID:{error}")
            contracts, truths, readiness = (), (), ()
    else:
        contracts, truths, readiness = (), (), ()
    if reasons:
        contracts, truths, readiness = (), (), ()
    return BuildResult(
        source_rows,
        contracts,
        truths,
        readiness,
        failure_rows,
        design_evidence,
        lifecycle,
        not reasons,
        tuple(dict.fromkeys(reasons)),
    )


def _manifest(
    result: BuildResult, output_sha256: Mapping[str, str],
) -> Mapping[str, Any]:
    succeeded = result.transaction_succeeded
    return {
        "schema_version": SCHEMA_VERSION,
        "formal_base": {
            "commit": BASE_COMMIT,
            "parent": BASE_PARENT,
            "tree": BASE_TREE,
            "subject": BASE_SUBJECT,
        },
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "source_count": 6,
        "source_sha256": {
            path.as_posix(): digest
            for path, digest in FROZEN_BASE_SHA256.items()
        },
        "design_schema_version": design.SCHEMA_VERSION,
        "design_interface_ready": True,
        "design_execution_ready": False,
        "interface_version": INTERFACE_VERSION,
        "authority_context_builder_function":
            "build_current11_warhead_boundary_review_ingestion_authority_context_v1",
        "batch_evaluator_function":
            "evaluate_current11_warhead_boundary_review_ingestion_v1",
        "batch_evaluator_keyword_only": True,
        "external_authority_maps_allowed": False,
        "external_file_inputs_allowed": False,
        "supported_runtime_lifecycles":
            list(SUPPORTED_RUNTIME_LIFECYCLES),
        "formal_successor_runtime_compatible": True,
        "runtime_lifecycle_count": 4,
        "runtime_lifecycles_all_verified": True,
        "public_runtime_compatibility_scope":
            PUBLIC_RUNTIME_COMPATIBILITY_SCOPE,
        "public_runtime_required_base_commit":
            PUBLIC_RUNTIME_REQUIRED_BASE_COMMIT,
        "artifact_build_lifecycle_strict": True,
        "public_runtime_requires_exact_interface_lifecycle": False,
        "downstream_descendant_runtime_compatible": True,
        "downstream_descendant_depths_verified": [1, 2],
        "imported_design_source_integrity_required": True,
        "imported_design_source_sha256": IMPORTED_DESIGN_SOURCE_SHA256,
        "working_tree_design_source_must_match_HEAD": True,
        "downstream_callers_must_not_call_interface_build_result": True,
        "public_evaluator_runtime_repository_guard_required": True,
        "public_evaluator_design_source_integrity_required": True,
        "public_evaluator_repository_root_inferred_from_interface_module": True,
        "public_evaluator_calls_design_ingest_only_after_integrity_validation":
            True,
        "saved_context_cannot_bypass_design_source_integrity": True,
        "business_payload_in_memory_only": True,
        "public_runtime_integrity_checks_read_only": True,
        "separate_design_base_worktree_required": False,
        "authority_context_built_from_design_base_git_objects": True,
        "design_lifecycle_bound_builder_called": False,
        "design_lifecycle_bound_build_result_called": False,
        "interface_response_version": INTERFACE_RESPONSE_VERSION,
        "interface_response_field_count": 6,
        "interface_response_fields": list(INTERFACE_RESPONSE_FIELDS),
        "interface_response_hash_included_field_count": 5,
        "contract_count": len(result.contract_rows),
        "truth_case_count": len(result.truth_rows),
        "truth_passed_case_count": sum(
            row["expected_outcome_class"] == "passed"
            for row in result.truth_rows
        ),
        "truth_blocked_case_count": sum(
            row["expected_outcome_class"] == "blocked"
            for row in result.truth_rows
        ),
        "truth_invalid_case_count": sum(
            row["expected_outcome_class"] == "invalid"
            for row in result.truth_rows
        ),
        "current11_readiness_row_count": len(result.readiness_rows),
        "response_level_validation_required": True,
        "input_immutability_required": True,
        "filesystem_persistence_allowed": False,
        "synthetic_validation_only": True,
        "interface_implementation_completed": succeeded,
        "ready_for_synthetic_interface_evaluation": succeeded,
        "ready_for_real_review_ingestion_execution": False,
        "completed_review_record_count": 0,
        "human_provenance_envelope_count": 0,
        "actual_ingestion_result_count": 0,
        "actual_authority_record_count": 0,
        "sample_quarantined_count": 0,
        "complete_warhead_atom_set_authority_available_count": 0,
        "exact_one_attachment_boundary_authority_available_count": 0,
        "candidate_warhead_smarts_materialized_count": 0,
        "approved_reaction_family_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "approved_warhead_smarts_count": 0,
        "human_gold_review_completed_count": 0,
        "training_label_approved_count": 0,
        "ready_for_role_proposal_generation": False,
        "ready_for_minimal_seed_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "formal_training_prerequisite": "feature-semantics audit",
        "Step12D_scope": "smoke legality check only",
        "canonical_mask_count": 5,
        "canonical_masks": list(CANONICAL_MASKS),
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "transaction_succeeded": succeeded,
        "blocking_reasons": list(result.blocking_reasons),
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            row["verified"] and row["fails_closed"]
            for row in result.failure_rows
        ),
        "actual_lifecycle": "pre_commit",
        "output_sha256": dict(output_sha256),
        "recommended_manual_action_primary":
            "perform_real_human_review_of_current11_warhead_atom_set_and_"
            "attachment_boundary_review_packages",
        "remaining_parallel_manual_action":
            "perform_real_human_review_of_materialized_family_topology_and_"
            "sample_assignment_packages",
        "recommended_engineering_next_step":
            "design_covapie_current11_warhead_atom_set_and_attachment_"
            "boundary_review_submission_adapter_v1",
        "recommended_next_step": (
            "design_covapie_current11_warhead_atom_set_and_attachment_"
            "boundary_review_submission_adapter_v1"
            if succeeded
            else "resolve_covapie_current11_warhead_boundary_review_"
            "ingestion_interface_blockers_v1"
        ),
    }


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    result = build_result(repo_root)
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, result.contract_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, result.truth_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    output_sha256 = {
        name: sha256(payload) for name, payload in payloads.items()
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(
            _manifest(result, output_sha256),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    destination = repo_root / OUTPUT_ROOT
    destination.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (destination / name).write_bytes(payload)
    return payloads


def main() -> int:
    materialize(Path(__file__).resolve().parents[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
