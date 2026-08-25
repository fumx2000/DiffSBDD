#!/usr/bin/env python3
"""Repository-state-neutral checker for the cumulative1000 census V1."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_v1 as subject,
)


FIXED_SOURCE_SPECS = (
    ("repository_relative", subject._UNIVERSE, 492899, "5998991f4a777dc8364d773e68a438837e656983aab805dae388b64c3619dbc5"),
    ("repository_parent_relative", subject._STRUCTURAL_1_500, 6469651, "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44"),
    ("repository_relative", subject._STRUCTURAL_501_1000, 5988559, "4f5ee75a645ee560cb8e272fd3ead8ba7a446dadf9aece38f12f0eeecad16e5f"),
    ("repository_relative", "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_g3h_v1.py", 12686, "2e1e0775b8123d7266bcc6d462a9b39c0ce3c0c9385e7aba4eee1f2fb5c367a6"),
    ("repository_relative", subject._QUEUE, 50116, "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"),
    ("repository_relative", subject._LEGACY_HUMAN, 91133, "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441"),
    ("repository_relative", subject._BATCH_SNAPSHOT, 33764, "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200"),
    ("repository_relative", subject._RUNTIME_INDEX, 13511, "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410"),
    ("repository_relative", subject._RUNTIME_INVENTORY, 45567, "b8a0f4c2bc8ca46141775f0a5fa54322d12db685b37c930659f6f4a1ca3b4052"),
    ("repository_relative", subject._FFQ_EVENT, 21239, "781972cbee68403805bb0266db65221b0973cb61e666925264dc0d50524090a0"),
    ("repository_relative", "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py", 42406, "f4656f414a5d31d5e967b39885dd5d89e9bf205135dbd29b3285e0d1e856367f"),
    ("repository_relative", subject._G3H_EVENT, 20247, "f7afc5caf16bb81e18223258cfb39be79c7a18dd4938b756599ad228f6cffe10"),
    ("repository_relative", "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py", 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b"),
)

EXPECTED_STATUS = {
    "CURRENTLY_UNREVIEWED": 273,
    "CURRENTLY_IN_PROGRESS": 9,
    "COMPLETED_HUMAN_POSITIVE": 32,
    "COMPLETED_HUMAN_NEGATIVE": 54,
    "COMPLETED_PARTIAL_AUTHORITY": 1,
    "CURRENT_RUNTIME_MODEL_USABLE": 17,
    "PUBLISHED_EXACT_AUTO_NEGATIVE": 32,
    "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
    "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
    "QUARANTINE_REPRESENTATION_GAP": 78,
    "REJECTED_FEATURE_INCOMPATIBLE": 2,
}

EXPECTED_BOOLEAN_COUNTS = {
    "raw_structure_available": 997,
    "exact_cys_sg_event_recovered": 867,
    "explicit_covalent_evidence": 867,
    "distance_only_event_inference_used": 0,
    "full_coordinate_post_evidence_available": 867,
    "ccd_graph_complete": 865,
    "feature_compatible": 865,
    "structural_processing_success": 865,
    "post_geometry_source_evidence_available": 867,
    "representation_gap": 78,
    "feature_incompatible": 2,
    "priority_review_in_scope": 338,
    "reactive_pair_raw_structural_evidence": 865,
    "reactive_pair_sample_authoritative": 49,
    "reactive_pair_training_target_available": 41,
    "role_partition_sample_authoritative": 49,
    "canonical_mask_structural_labels_available": 49,
    "post_geometry_sample_authoritative": 21,
    "post_geometry_training_target_available": 17,
    "pre_geometry_authoritative": 0,
    "pre_geometry_training_target_available": 0,
    "training_use_include": 29,
    "future_training_admission_candidate": 12,
    "formal_training_admitted": 5,
    "current_runtime_model_usable": 17,
}

FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pyc",
    ".tmp",
    ".part",
)
MAX_CANDIDATE_FILE_BYTES = 1024 * 1024


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _event_set_sha256(event_ids: set[str]) -> str:
    return _sha256(_canonical_json(sorted(event_ids)).encode("utf-8"))


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    return path.read_bytes()


def _validate_text(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("NOT_UTF8:" + label) from error
    if "\x00" in text or "\r" in text:
        raise ValueError("TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def _resolve(root: Path, namespace: str, relative: str) -> Path:
    if namespace == "repository_relative":
        return root / relative
    if namespace == "repository_parent_relative":
        return root.parent / relative
    raise ValueError("PATH_NAMESPACE_INVALID:" + namespace)


def verify_exact7_candidate_inventory_v1(root: Path) -> dict[str, object]:
    bindings: list[dict[str, object]] = []
    output_dir = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if not output_dir.is_dir():
        raise ValueError("OUTPUT_DIRECTORY_MISSING")
    output_files = sorted(path.name for path in output_dir.iterdir() if path.is_file())
    if output_files != sorted(
        (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    ):
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read_regular_file(path, "EXACT7:" + relative)
        _validate_text(payload, relative)
        if stat.S_IMODE(path.stat().st_mode) != 0o644:
            raise ValueError("EXACT7_MODE_NOT_0644:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT7_FORBIDDEN_SUFFIX:" + relative)
        if len(payload) > MAX_CANDIDATE_FILE_BYTES:
            raise ValueError("EXACT7_FILE_EXCEEDS_1_MIB:" + relative)
        bindings.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha256(payload),
                "mode": "0644",
            }
        )
    return {"candidate_file_count": 7, "candidate_file_bindings": bindings}


def verify_fixed_sources_v1(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for namespace, relative, byte_count, sha256 in FIXED_SOURCE_SPECS:
        payload = _read_regular_file(
            _resolve(root, namespace, relative), "FIXED_SOURCE:" + relative
        )
        if len(payload) != byte_count:
            raise ValueError("FIXED_SOURCE_BYTE_COUNT_MISMATCH:" + relative)
        if _sha256(payload) != sha256:
            raise ValueError("FIXED_SOURCE_SHA256_MISMATCH:" + relative)
        result.append(
            {
                "path_namespace": namespace,
                "path": relative,
                "byte_count": byte_count,
                "sha256": sha256,
            }
        )
    return result


def _parse_csv(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != subject.CENSUS_COLUMNS_V1:
        raise ValueError("MATERIALIZED_CENSUS_HEADER_INVALID")
    rows = [dict(row) for row in reader]
    if any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows):
        raise ValueError("MATERIALIZED_CENSUS_ROW_SCHEMA_INVALID")
    return rows


def independently_verify_census_v1(
    census_payload: bytes, summary_payload: bytes
) -> dict[str, object]:
    rows = _parse_csv(census_payload)
    summary = json.loads(summary_payload)
    if len(rows) != 1000:
        raise ValueError("MATERIALIZED_CENSUS_ROW_COUNT_INVALID")
    try:
        ranks = [int(row["scaleup_rank"]) for row in rows]
    except ValueError as error:
        raise ValueError("MATERIALIZED_CENSUS_RANK_INVALID") from error
    if ranks != list(range(1, 1001)):
        raise ValueError("MATERIALIZED_CENSUS_RANK_GAP")
    event_ids = {row["canonical_event_id"] for row in rows}
    if len(event_ids) != 1000:
        raise ValueError("MATERIALIZED_CENSUS_EVENT_DUPLICATE")
    if _event_set_sha256(event_ids) != subject.EXPECTED_EVENT_SET_SHA256_V1[
        "universe"
    ]:
        raise ValueError("MATERIALIZED_CENSUS_EVENT_SET_SHA_INVALID")
    if len({row["pdb_id"] for row in rows}) != 546:
        raise ValueError("MATERIALIZED_CENSUS_PDB_COUNT_INVALID")
    if len({row["ligand_component_id"] for row in rows}) != 416:
        raise ValueError("MATERIALIZED_CENSUS_LIGAND_COUNT_INVALID")
    for field, expected in EXPECTED_BOOLEAN_COUNTS.items():
        if sum(row[field] == "true" for row in rows) != expected:
            raise ValueError("MATERIALIZED_BOOLEAN_COUNT_INVALID:" + field)
    if Counter(row["current_global_status"] for row in rows) != Counter(
        EXPECTED_STATUS
    ):
        raise ValueError("MATERIALIZED_EXACT11_STATUS_INVALID")
    chemistry = Counter(row["chemistry_disposition"] for row in rows)
    if chemistry != Counter({"POSITIVE": 49, "NOT_ESTABLISHED": 86, "UNRESOLVED": 865}):
        raise ValueError("MATERIALIZED_CHEMISTRY_COUNTS_INVALID")
    task = Counter(row["task_relevance_disposition"] for row in rows)
    if task != Counter({"RELEVANT": 50, "NOT_RELEVANT": 86, "UNRESOLVED": 864}):
        raise ValueError("MATERIALIZED_TASK_COUNTS_INVALID")
    training = Counter(row["training_use_disposition"] for row in rows)
    if training != Counter(
        {
            "INCLUDE": 29,
            "EXCLUDE_FROM_TRAINING_ONLY": 20,
            "NOT_APPLICABLE": 86,
            "UNRESOLVED": 865,
        }
    ):
        raise ValueError("MATERIALIZED_TRAINING_USE_COUNTS_INVALID")
    event_sets = {
        "chemistry_positive": {
            row["canonical_event_id"] for row in rows if row["chemistry_disposition"] == "POSITIVE"
        },
        "chemistry_not_established": {
            row["canonical_event_id"] for row in rows if row["chemistry_disposition"] == "NOT_ESTABLISHED"
        },
        "chemistry_unresolved": {
            row["canonical_event_id"] for row in rows if row["chemistry_disposition"] == "UNRESOLVED"
        },
        "task_relevant": {
            row["canonical_event_id"] for row in rows if row["task_relevance_disposition"] == "RELEVANT"
        },
        "training_include": {
            row["canonical_event_id"] for row in rows if row["training_use_disposition"] == "INCLUDE"
        },
        "training_exclude": {
            row["canonical_event_id"]
            for row in rows
            if row["training_use_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"
        },
    }
    for name, expected in subject.EXPECTED_EVENT_SET_SHA256_V1.items():
        if name == "universe":
            continue
        if name in event_sets and _event_set_sha256(event_sets[name]) != expected:
            raise ValueError("MATERIALIZED_EVENT_SET_SHA_INVALID:" + name)
    if any(
        row["chemistry_disposition"] == "NEGATIVE"
        or (
            row["training_use_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY"
            and row["chemistry_disposition"] != "POSITIVE"
        )
        or (
            row["task_relevance_disposition"] == "NOT_RELEVANT"
            and row["chemistry_disposition"] != "NOT_ESTABLISHED"
        )
        for row in rows
    ):
        raise ValueError("MATERIALIZED_NEGATIVE_SEMANTICS_INVALID")
    if any(
        row["role_partition_sample_authoritative"] == "false"
        and row["structurally_applicable_task_ids_json"] != "null"
        for row in rows
    ):
        raise ValueError("MATERIALIZED_ROLELESS_APPLICABILITY_NOT_UNKNOWN")
    if summary["canonical_exact5"]["task_count"] != 5 or not summary[
        "canonical_exact5"
    ]["B3_present"]:
        raise ValueError("MATERIALIZED_EXACT5_INVALID")
    if summary["training_stage"][
        "training_materialization_allowed_global_status"
    ] != "NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY":
        raise ValueError("MATERIALIZED_TRAINING_MATERIALIZATION_STATUS_INVALID")
    return {
        "row_count": len(rows),
        "event_set_sha256": _event_set_sha256(event_ids),
        "status_counts": dict(Counter(row["current_global_status"] for row in rows)),
        "chemistry_counts": dict(chemistry),
        "task_relevance_counts": dict(task),
        "training_use_counts": dict(training),
    }


def verify_manifest_v1(
    root: Path,
    artifacts: Mapping[str, bytes],
) -> dict[str, object]:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    if manifest.get("schema_version") != subject.SCHEMA_VERSION:
        raise ValueError("MANIFEST_SCHEMA_INVALID")
    inventory = manifest.get("candidate_inventory")
    if inventory != {
        "exact_file_count": 7,
        "paths": list(subject.EXACT7_PATHS_V1),
    }:
        raise ValueError("MANIFEST_CANDIDATE_INVENTORY_INVALID")
    contract = manifest.get("candidate_contract_bindings")
    expected_contract_paths = {
        subject.PRODUCTION_RELATIVE.as_posix(),
        subject.CHECKER_RELATIVE.as_posix(),
        subject.TEST_RELATIVE.as_posix(),
        subject.GUIDE_RELATIVE.as_posix(),
    }
    if type(contract) is not list or {row.get("path") for row in contract} != expected_contract_paths:
        raise ValueError("MANIFEST_CONTRACT_BINDINGS_INVALID")
    for row in contract:
        payload = _read_regular_file(root / row["path"], "MANIFEST_CONTRACT")
        if row.get("byte_count") != len(payload) or row.get("sha256") != _sha256(payload):
            raise ValueError("MANIFEST_CONTRACT_BINDING_DRIFT:" + row["path"])
    semantic = manifest.get("semantic_source_bindings")
    if type(semantic) is not list or not semantic:
        raise ValueError("MANIFEST_SEMANTIC_BINDINGS_INVALID")
    identities: set[tuple[str, str]] = set()
    for row in semantic:
        if set(row) != {"artifact_role", "path", "path_namespace", "byte_count", "sha256"}:
            raise ValueError("MANIFEST_SEMANTIC_BINDING_SCHEMA_INVALID")
        identity = (row["path_namespace"], row["path"])
        if identity in identities:
            raise ValueError("MANIFEST_SEMANTIC_BINDING_DUPLICATE")
        identities.add(identity)
        payload = _read_regular_file(
            _resolve(root, row["path_namespace"], row["path"]),
            "MANIFEST_SEMANTIC_SOURCE",
        )
        if row["byte_count"] != len(payload) or row["sha256"] != _sha256(payload):
            raise ValueError("MANIFEST_SEMANTIC_BINDING_DRIFT:" + row["path"])
    output_inventory = manifest.get("output_inventory")
    if output_inventory != {
        "exact_output_count": 3,
        "paths": [
            (subject.OUTPUT_DIRECTORY_RELATIVE / subject.CENSUS_FILE).as_posix(),
            (subject.OUTPUT_DIRECTORY_RELATIVE / subject.SUMMARY_FILE).as_posix(),
            (subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE).as_posix(),
        ],
    }:
        raise ValueError("MANIFEST_OUTPUT_INVENTORY_INVALID")
    output_bindings = manifest.get("output_bindings_excluding_manifest_self")
    if type(output_bindings) is not list or len(output_bindings) != 2:
        raise ValueError("MANIFEST_OUTPUT_BINDINGS_INVALID")
    for row in output_bindings:
        filename = PurePosixPath(row["path"]).name
        if filename == subject.MANIFEST_FILE:
            raise ValueError("MANIFEST_SELF_HASH_PRESENT")
        payload = artifacts.get(filename)
        if payload is None or row["byte_count"] != len(payload) or row["sha256"] != _sha256(payload):
            raise ValueError("MANIFEST_OUTPUT_BINDING_DRIFT:" + filename)
    if manifest.get("manifest_self_binding") != {
        "path": (subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE).as_posix(),
        "sha256_recorded_inside_self": False,
        "policy": "MANIFEST_SELF_SHA256_PROHIBITED",
    }:
        raise ValueError("MANIFEST_SELF_HASH_POLICY_INVALID")
    boundary = manifest.get("authority_boundary")
    if type(boundary) is not dict or boundary.get(
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"
    ) is not True:
        raise ValueError("MANIFEST_READINESS_NOT_ASSERTED")
    return {
        "semantic_source_binding_count": len(semantic),
        "output_binding_count_excluding_self": len(output_bindings),
        "manifest_self_hash_recorded": False,
    }


def _verify_determinism(root: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    with tempfile.TemporaryDirectory(prefix="covapie-census-v1-a-") as first_dir, tempfile.TemporaryDirectory(
        prefix="covapie-census-v1-b-"
    ) as second_dir:
        first = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_v1(
            root, Path(first_dir) / "out"
        )
        second = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_v1(
            root, Path(second_dir) / "out"
        )
        if set(first) != {subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE}:
            raise ValueError("BUILDER_NOT_EXACT3")
        if first != second:
            raise ValueError("DOUBLE_MATERIALIZATION_NOT_BYTE_IDENTICAL")
        disk_first = {
            filename: (Path(first_dir) / "out" / filename).read_bytes()
            for filename in first
        }
        disk_second = {
            filename: (Path(second_dir) / "out" / filename).read_bytes()
            for filename in second
        }
        if disk_first != first or disk_second != second:
            raise ValueError("MATERIALIZED_DISK_BYTES_MISMATCH")
        return first, {filename: _sha256(payload) for filename, payload in first.items()}


def _assert_non_actions(summary: Mapping[str, Any]) -> None:
    boundary = summary["authority_boundary"]
    false_keys = (
        "new_human_authority_created",
        "new_chemistry_authority_created",
        "new_reusable_authority_created",
        "tensor_integration_performed",
        "loader_modified",
        "batch_modified",
        "model_forward_performed",
        "auxiliary_head_executed",
        "loss_executed",
        "backward_performed",
        "optimizer_created",
        "optimizer_step_performed",
        "parameter_update_performed",
        "training_performed",
        "fine_tune_performed",
        "training_admission_created",
        "training_dataset_changed",
        "feature_semantics_audit_performed",
    )
    if any(boundary.get(key) is not False for key in false_keys):
        raise ValueError("TRAINING_OR_MODEL_NON_ACTION_INVALID")
    if boundary.get("HUMAN_REVIEW_DECISION_NOT_PERFORMED") is not True:
        raise ValueError("HUMAN_REVIEW_NON_ACTION_INVALID")
    if boundary.get("READY_FOR_FORMAL_TRAINING") is not False:
        raise ValueError("FORMAL_TRAINING_READINESS_INVALID")


def run_check_v1(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    candidate = verify_exact7_candidate_inventory_v1(root)
    fixed = verify_fixed_sources_v1(root)
    rebuilt, deterministic_sha = _verify_determinism(root)
    materialized = {
        filename: _read_regular_file(
            root / subject.OUTPUT_DIRECTORY_RELATIVE / filename,
            "MATERIALIZED:" + filename,
        )
        for filename in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    if materialized != rebuilt:
        raise ValueError("PUBLISHED_OUTPUTS_DO_NOT_MATCH_FRESH_BUILDER")
    census = independently_verify_census_v1(
        materialized[subject.CENSUS_FILE], materialized[subject.SUMMARY_FILE]
    )
    manifest = verify_manifest_v1(root, materialized)
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    _assert_non_actions(summary)
    if summary["authority_boundary"][
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"
    ] is not True:
        raise ValueError("CURRENT_GLOBAL_READINESS_CENSUS_NOT_COMPLETE")
    return {
        "schema_version": subject.SCHEMA_VERSION,
        "candidate": candidate,
        "fixed_source_binding_count": len(fixed),
        "deterministic_double_materialization": True,
        "deterministic_output_sha256": deterministic_sha,
        "census": census,
        "manifest": manifest,
        "all_training_and_model_non_actions_asserted": True,
        "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE": True,
        "READY_FOR_FORMAL_TRAINING": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = run_check_v1(args.repo_root)
    if result["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is not True:
        raise ValueError("CHECKER_READINESS_ASSERTION_FAILED")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
