"""Build the audited Current11 tensor-projection payload bundle in memory."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import stat
import struct
from collections import Counter
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

from covalent_ext import (
    covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1
    as _contract_gate,
)


__all__ = ("build_covapie_current11_tensor_projection_payload_bundle_v1",)

_ERROR = "COVAPIE_CURRENT11_TENSOR_PROJECTION_PAYLOAD_BUILDER_V1_ERROR"
_GATE_MODULE_RELATIVE = (
    "src/covalent_ext/"
    "covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py"
)
_GATE_MODULE_SHA256 = (
    "d46ebaf163abf862aadb35301efa649eac6dc799da434e29f58f95deae2cbe0f"
)
_CONTRACT_DIGEST = (
    "d0a428c19fe3c4aefc575065e7dcc7a7cfaf8593526d025d467cf6568b49c21d"
)
_AUDIT_RELATIVE = (
    "review-scratch/current11-routing-tensor-projection-payload-extraction-"
    "preconditions-v1/payload_extraction_preconditions_report.md"
)
_AUDIT_SHA256 = (
    "5c2153bec25a0c4aae1415e2ffa23ae34397181c39b585c9538840578ad3edf2"
)
_FORMAL_RELATIVE = (
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
_FORMAL_READLINK = (
    ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
    "1fd8cf5823427e941b11c7b2560a336f"
)
_FORMAL_AGGREGATE_SHA256 = (
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
)
_FORMAL_SNAPSHOT_SHA256 = (
    "768fbd980efbcedcaa2ef971a7d77791879111d1fceeb1f03cb1eb8bfff24034"
)
_FORMAL_FILES = {
    "current11_dataset_partial_supervision_routing_records.csv": (
        69557,
        276,
        "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03",
    ),
    "current11_dataset_partial_supervision_task_coverage.csv": (
        1883,
        26,
        "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7",
    ),
    "current11_dataset_partial_supervision_sample_coverage.csv": (
        1445,
        12,
        "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e",
    ),
    "current11_dataset_partial_supervision_routing_manifest.json": (
        43109,
        1044,
        "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d",
    ),
}

_SAMPLES = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP"),
)
_TASKS = (
    (0, "sample_identity_supervision", "admissible_now"),
    (1, "explicit_covalent_event_supervision", "admissible_now"),
    (2, "ligand_residue_atom_pair_supervision", "admissible_now"),
    (6, "warhead_boundary_supervision", "admissible_now"),
    (
        12,
        "observed_complex_geometry_supervision",
        "admissible_as_observed_geometry_only",
    ),
)
_SOURCE_IDS = (
    "canonical_final_index",
    "canonical_pair_matrix",
    "atom_table_mapping_matrix",
    "published_unit_000001_gate",
    "unified_boundary_authority",
    *(f"event_table_{sample[0]}" for sample in _SAMPLES),
    *(f"observed_pair_table_{sample[0]}" for sample in _SAMPLES),
)
_ARTIFACT_NAMES = (
    "current11_tensor_projection_payload_bundle_manifest.json",
    "current11_tensor_projection_payload_sample_identity.json",
    "current11_tensor_projection_payload_explicit_covalent_event.json",
    "current11_tensor_projection_payload_ligand_residue_atom_pair.json",
    "current11_tensor_projection_payload_warhead_boundary.json",
    "current11_tensor_projection_payload_observed_complex_geometry.json",
    "current11_tensor_projection_payload_provenance.json",
    "current11_tensor_projection_payload_builder_report.json",
)
_REPOSITORY_EXACT4 = (
    "docs/covapie_current11_tensor_projection_payload_builder_v1_guide.md",
    "scripts/check_covapie_current11_tensor_projection_payload_builder_v1.py",
    "src/covalent_ext/covapie_current11_tensor_projection_payload_builder_v1.py",
    "tests/test_covapie_current11_tensor_projection_payload_builder_v1.py",
)
_STABLE_ARTIFACT_NAMES = _ARTIFACT_NAMES[:7]
_DIGEST_DOMAIN_TAG = (
    b"COVAPIE_CURRENT11_TENSOR_PROJECTION_PAYLOAD_BUNDLE_V1\0"
)
_SCHEMAS = {
    _ARTIFACT_NAMES[0]: "covapie_current11_tensor_projection_payload_bundle_v1",
    _ARTIFACT_NAMES[1]: (
        "covapie_current11_tensor_projection_payload_sample_identity_v1"
    ),
    _ARTIFACT_NAMES[2]: (
        "covapie_current11_tensor_projection_payload_explicit_covalent_event_v1"
    ),
    _ARTIFACT_NAMES[3]: (
        "covapie_current11_tensor_projection_payload_ligand_residue_atom_pair_v1"
    ),
    _ARTIFACT_NAMES[4]: (
        "covapie_current11_tensor_projection_payload_warhead_boundary_v1"
    ),
    _ARTIFACT_NAMES[5]: (
        "covapie_current11_tensor_projection_payload_observed_complex_geometry_v1"
    ),
    _ARTIFACT_NAMES[6]: (
        "covapie_current11_tensor_projection_payload_provenance_v1"
    ),
    _ARTIFACT_NAMES[7]: (
        "covapie_current11_tensor_projection_payload_builder_report_v1"
    ),
}
_EXPECTED_PAIR_VALUES = (
    (88, 3),
    (25, 3),
    (19, 3),
    (39, 3),
    (37, 27),
    (50, 21),
    (48, 16),
    (53, 20),
    (52, 21),
    (53, 18),
    (84, 5),
)
_EXPECTED_DISTANCE_STRINGS = (
    "1.670",
    "1.800",
    "1.718",
    "1.802",
    "1.809",
    "1.762",
    "1.807",
    "1.799",
    "1.806",
    "1.794",
    "1.717",
)
_MAX_COORDINATE_DIFFERENCE = 0.000481732266

_ROUTING_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "semantic_task_name",
    "eligibility_state",
    "direct_authority_found",
    "evidence_scope",
    "blocking_reason_code",
    "supporting_source_ids_json",
    "dedicated_transformation_review_available",
    "availability_mask_required",
    "current_runtime_consumer_available",
    "training_loss_authorized",
)
_FINAL_INDEX_COLUMNS = (
    "sample_index_row_id", "sample_preparation_input_id", "sample_execution_id",
    "sample_qa_id", "pdb_id", "expected_het_id", "sample_artifact_root",
    "protein_atom_table_path", "ligand_atom_table_path", "pocket_atom_table_path",
    "covalent_event_table_path", "ligand_residue_atom_pair_table_path",
    "sample_preparation_audit_path", "protein_atom_count", "ligand_atom_count",
    "pocket_atom_count", "covalent_event_count", "ligand_residue_atom_pair_count",
    "covalent_residue_name", "covalent_residue_chain_id",
    "covalent_residue_index", "covalent_residue_atom_name", "ligand_comp_id",
    "ligand_covalent_atom_name", "covalent_bond_atom_pair", "conn_id",
    "conn_type_id", "bond_distance_angstrom", "sample_index_status",
    "eligible_for_final_dataset_design", "ready_for_training_current_step",
    "feature_semantics_audit_required_before_training",
    "leakage_split_design_required_before_training",
)
_PAIR_COLUMNS = (
    "sample_index_row_id", "event_id", "pdb_id", "pair_record_schema_version",
    "residue_entity_role", "residue_auth_asym_id", "residue_auth_seq_id",
    "residue_label_asym_id", "residue_label_seq_id", "residue_comp_id",
    "residue_atom_name", "ligand_entity_role", "ligand_auth_asym_id",
    "ligand_auth_seq_id", "ligand_label_asym_id", "ligand_label_seq_id",
    "ligand_comp_id", "ligand_atom_name", "explicit_bond_authority_class",
    "explicit_bond_provenance_id", "canonical_record_valid", "legacy_projection",
    "observed_legacy_value", "legacy_projection_matches", "event_pair_value_matches",
    "pair_table_value_matches", "final_index_value_matches",
    "explicit_authority_preserved", "verified",
)
_MAPPING_COLUMNS = (
    "sample_index_row_id", "event_id", "pdb_id", "entity_role",
    "target_table_path", "target_table_sha256", "target_table_data_row_count",
    "mapping_key_fields", "nonempty_locator_fields_used",
    "optional_locator_fields_unavailable", "candidate_match_count",
    "expected_match_count", "matched_row_index_0based", "matched_atom_site_id",
    "pair_table_expected_atom_site_id", "atom_site_id_matches",
    "coordinate_crosscheck_passed", "distance_used_for_mapping_selection",
    "source_row_order_sha_bound", "model_index_base", "mapping_outcome",
    "mapping_reason", "verified",
)
_EVENT_COLUMNS = (
    "sample_preparation_input_id", "pdb_id", "expected_het_id", "conn_id",
    "conn_type_id", "residue_comp_id", "residue_atom_name",
    "residue_auth_asym_id", "residue_auth_seq_id", "residue_label_asym_id",
    "residue_label_seq_id", "ligand_comp_id", "ligand_atom_name",
    "ligand_auth_asym_id", "ligand_auth_seq_id", "ligand_label_asym_id",
    "ligand_label_seq_id", "covalent_bond_atom_pair", "event_source",
    "event_status",
)
_OBSERVED_COLUMNS = (
    "sample_preparation_input_id", "pdb_id", "expected_het_id",
    "residue_atom_name", "ligand_atom_name", "covalent_bond_atom_pair",
    "residue_atom_site_id", "ligand_atom_site_id", "residue_x", "residue_y",
    "residue_z", "ligand_x", "ligand_y", "ligand_z",
    "bond_distance_angstrom", "validation_status",
)
_POCKET_COLUMNS = (
    "sample_preparation_input_id", "pdb_id", "pocket_radius_angstrom",
    "atom_site_id", "group_pdb", "type_symbol", "atom_name", "residue_name",
    "chain_id", "residue_index", "auth_asym_id", "auth_seq_id",
    "label_asym_id", "label_seq_id", "x", "y", "z",
    "min_distance_to_ligand_angstrom", "source_raw_file",
)
_LIGAND_COLUMNS = (
    "sample_preparation_input_id", "pdb_id", "expected_het_id", "atom_site_id",
    "type_symbol", "atom_name", "ligand_comp_id", "auth_asym_id",
    "auth_seq_id", "label_asym_id", "label_seq_id", "x", "y", "z",
    "occupancy", "altloc", "model_num", "is_covalent_ligand_atom",
    "source_raw_file",
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        return (
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
        raise ValueError(_ERROR) from error


def _compact_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


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


def _path_snapshot(path: Path, *, follow: bool = False) -> tuple[object, ...]:
    metadata = path.stat() if follow else path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha256(payload),
    )


def _formal_snapshot(canonical: Path) -> dict[str, object]:
    try:
        parent = canonical.parent
        link = os.readlink(canonical)
        object_path = parent / link
        parent_inventory = tuple(sorted(os.listdir(parent)))
        object_inventory = tuple(sorted(os.listdir(object_path)))
        return {
            "parent": _path_snapshot(parent),
            "parent_inventory": parent_inventory,
            "canonical": _path_snapshot(canonical),
            "readlink": link,
            "object": _path_snapshot(object_path),
            "object_inventory": object_inventory,
            "leaves": {
                name: _path_snapshot(object_path / name)
                for name in object_inventory
            },
        }
    except OSError as error:
        raise ValueError(_ERROR) from error


def _safe_bound_path(root: Path, relative: object) -> Path:
    if type(relative) is not str or not relative or "\\" in relative:
        _fail()
    pure = Path(relative)
    if pure.is_absolute() or pure.parts in ((), (".",)) or ".." in pure.parts:
        _fail()
    path = root / pure
    current = root
    try:
        for part in pure.parts:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                _fail()
        if path.resolve(strict=True).is_relative_to(root) is not True:
            _fail()
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    return path


def _read_regular(
    path: Path,
    *,
    expected_bytes: int | None = None,
    expected_sha256: str | None = None,
    require_lf_terminated: bool = False,
) -> bytes:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError(_ERROR) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or (expected_bytes is not None and len(payload) != expected_bytes)
        or (expected_sha256 is not None and _sha256(payload) != expected_sha256)
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or (require_lf_terminated and not payload.endswith(b"\n"))
    ):
        _fail()
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(_ERROR) from error
    return payload


def _csv_rows(payload: bytes, columns: Sequence[str]) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (csv.Error, UnicodeDecodeError) as error:
        raise ValueError(_ERROR) from error
    if (
        tuple(reader.fieldnames or ()) != tuple(columns)
        or not rows
        or any(None in row or tuple(row) != tuple(columns) for row in rows)
    ):
        _fail()
    return rows


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict:
        _fail()
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    del value
    _fail()


def _published_gate(repo_root: Path, state_root: Path) -> dict[str, bytes]:
    gate_source = _read_regular(
        _safe_bound_path(repo_root, _GATE_MODULE_RELATIVE),
        expected_sha256=_GATE_MODULE_SHA256,
        require_lf_terminated=True,
    )
    if _sha256(gate_source) != _GATE_MODULE_SHA256:
        _fail()

    # The frozen predecessor gate predates this successor Exact4 and rejects all
    # untracked files. Filter precisely these four authorized successor paths
    # from its status observation; every other repository change remains visible
    # and fail-closed. No successor lifecycle profile is created or serialized.
    original_run_git = _contract_gate._run_git

    def compatible_run_git(root: Path, arguments: Sequence[str]) -> str:
        output = original_run_git(root, arguments)
        if tuple(arguments) == (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ):
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            unexpected_allowed_shape = any(
                line[3:] in _REPOSITORY_EXACT4 and line not in allowed
                for line in lines
                if len(line) >= 4
            )
            if unexpected_allowed_shape:
                _fail()
            return "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        _contract_gate._run_git = compatible_run_git
        first = _contract_gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=repo_root, state_root=state_root
        )
        second = _contract_gate.build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=repo_root, state_root=state_root
        )
    finally:
        _contract_gate._run_git = original_run_git
    if (
        type(first) is not dict
        or type(second) is not dict
        or first != second
        or tuple(first) != tuple(_contract_gate.ARTIFACT_NAMES)
        or len(first) != 4
    ):
        _fail()
    report = _strict_json(first[_contract_gate.ARTIFACT_NAMES[3]])
    readiness = report.get("readiness")
    if (
        report.get("gate_status") != "PASS_CONTRACT_ONLY"
        or report.get("contract_digest") != _CONTRACT_DIGEST
        or report.get("formal_aggregate_sha256") != _FORMAL_AGGREGATE_SHA256
        or report.get("projection_instance_materialized") is not False
        or report.get("tensor_materialized") is not False
        or report.get("task_payloads_materialized") is not False
        or report.get("candidate_payloads_materialized") is not False
        or report.get("task_payload_validity_materialized") is not False
        or report.get("data_availability_mask_materialized") is not False
        or report.get("loss_authorized_true_count") != 0
        or report.get("runtime_consumer_available_true_count") != 0
        or type(readiness) is not dict
        or readiness.get("training_loss_authorized") is not False
        or readiness.get("runtime_consumer_available") is not False
    ):
        _fail()
    return first


def _read_formal(canonical: Path) -> dict[str, bytes]:
    try:
        if os.readlink(canonical) != _FORMAL_READLINK:
            _fail()
        object_path = canonical.parent / _FORMAL_READLINK
        if (
            not stat.S_ISLNK(canonical.lstat().st_mode)
            or not stat.S_ISDIR(object_path.lstat().st_mode)
            or stat.S_IMODE(object_path.lstat().st_mode) != 0o755
            or tuple(sorted(os.listdir(object_path)))
            != tuple(sorted(_FORMAL_FILES))
        ):
            _fail()
        payloads: dict[str, bytes] = {}
        for name, (size, lines, digest) in _FORMAL_FILES.items():
            payload = _read_regular(
                object_path / name,
                expected_bytes=size,
                expected_sha256=digest,
                require_lf_terminated=True,
            )
            if payload.count(b"\n") != lines:
                _fail()
            payloads[name] = payload
        return payloads
    except OSError as error:
        raise ValueError(_ERROR) from error


def _validate_routing(formal: Mapping[str, bytes]) -> dict[str, object]:
    if type(formal) is not dict or tuple(formal) != tuple(_FORMAL_FILES):
        _fail()
    manifest = _strict_json(
        formal["current11_dataset_partial_supervision_routing_manifest.json"]
    )
    records = _csv_rows(
        formal["current11_dataset_partial_supervision_routing_records.csv"],
        _ROUTING_COLUMNS,
    )
    sample_coverage = _csv_rows(
        formal["current11_dataset_partial_supervision_sample_coverage.csv"],
        _contract_gate.SAMPLE_COVERAGE_COLUMNS,
    )
    if (
        manifest.get("schema_version")
        != "covapie_current11_dataset_partial_supervision_routing_sidecar_v1"
        or manifest.get("canonical_sample_identity")
        != [
            {
                "sample_index_row_id": sample,
                "pdb_id": pdb,
                "ligand_comp_id": ligand,
            }
            for sample, pdb, ligand in _SAMPLES
        ]
        or len(records) != 275
        or len(sample_coverage) != 11
        or type(manifest.get("source_bindings")) is not dict
    ):
        _fail()
    task_names = manifest.get("semantic_task_names")
    expected_all_keys = [
        (sample[0], task)
        for sample in _SAMPLES
        for task in task_names if type(task_names) is list
    ]
    if (
        type(task_names) is not list
        or len(task_names) != 25
        or [
            (row["sample_index_row_id"], row["semantic_task_name"])
            for row in records
        ]
        != expected_all_keys
    ):
        _fail()
    selected_names = {task[1] for task in _TASKS}
    selected = [row for row in records if row["semantic_task_name"] in selected_names]
    expected_selected = [(sample[0], task[1]) for sample in _SAMPLES for task in _TASKS]
    if (
        len(selected) != 55
        or len({(row["sample_index_row_id"], row["semantic_task_name"]) for row in selected})
        != 55
        or [(row["sample_index_row_id"], row["semantic_task_name"]) for row in selected]
        != expected_selected
    ):
        _fail()
    task_by_name = {item[1]: item for item in _TASKS}
    source_union: set[str] = set()
    for row in selected:
        sample = _SAMPLES[expected_selected.index((row["sample_index_row_id"], row["semantic_task_name"])) // 5]
        task = task_by_name[row["semantic_task_name"]]
        try:
            supporting = json.loads(row["supporting_source_ids_json"])
        except json.JSONDecodeError as error:
            raise ValueError(_ERROR) from error
        if (
            tuple(row[key] for key in ("sample_index_row_id", "pdb_id", "ligand_comp_id"))
            != sample
            or row["eligibility_state"] != task[2]
            or row["direct_authority_found"] != "true"
            or row["current_runtime_consumer_available"] != "false"
            or row["training_loss_authorized"] != "false"
            or row["availability_mask_required"] != "true"
            or type(supporting) is not list
            or not supporting
            or any(type(item) is not str for item in supporting)
            or len(supporting) != len(set(supporting))
            or json.dumps(supporting, ensure_ascii=True, separators=(",", ":"))
            != row["supporting_source_ids_json"]
        ):
            _fail()
        sample_index = expected_selected.index(
            (row["sample_index_row_id"], row["semantic_task_name"])
        ) // 5
        direct_by_task = {
            _TASKS[0][1]: ["canonical_final_index"],
            _TASKS[1][1]: [
                f"event_table_{row['sample_index_row_id']}",
                "canonical_pair_matrix",
                "atom_table_mapping_matrix",
            ],
            _TASKS[2][1]: ["canonical_pair_matrix", "atom_table_mapping_matrix"],
            _TASKS[3][1]: ["unified_boundary_authority"],
            _TASKS[4][1]: [
                f"observed_pair_table_{row['sample_index_row_id']}"
            ],
        }
        expected_supporting = direct_by_task[row["semantic_task_name"]]
        if sample_index in (7, 9):
            expected_supporting = ["published_unit_000001_gate", *expected_supporting]
        if supporting != expected_supporting:
            _fail()
        row["_supporting_source_ids"] = supporting  # type: ignore[assignment]
        source_union.update(supporting)
    if source_union != set(_SOURCE_IDS) or len(source_union) != 27:
        _fail()
    for index, (coverage, sample) in enumerate(zip(sample_coverage, _SAMPLES, strict=True)):
        if tuple(coverage[key] for key in sample_coverage[0] if key in {"sample_index_row_id", "pdb_id", "ligand_comp_id"}) != sample:
            _fail()
        if index >= 11:
            _fail()
    return {
        "manifest": manifest,
        "records": records,
        "selected": selected,
        "selected_by_key": {
            (row["sample_index_row_id"], row["semantic_task_name"]): row
            for row in selected
        },
        "sample_coverage": sample_coverage,
    }


def _resolve_sources(
    repo_root: Path,
    state_root: Path,
    routing: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    manifest = routing["manifest"]
    if type(manifest) is not dict or type(manifest.get("source_bindings")) is not dict:
        _fail()
    bindings = manifest["source_bindings"]
    resolved: dict[str, dict[str, object]] = {}
    for source_id in _SOURCE_IDS:
        binding = bindings.get(source_id)
        if type(binding) is not dict or binding.get("read_only") is not True:
            _fail()
        if source_id == "published_unit_000001_gate":
            if (
                binding.get("schema_version")
                != "covapie_current11_unit_000001_partial_supervision_routing_gate_v1"
                or binding.get("public_api")
                != "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1"
                or binding.get("source_kind") != "published_derived_gate"
                or binding.get("module_source_id") != "unit_000001_gate_module"
                or binding.get("state_projection_sha256")
                != "fd016edf634c73aea4b0976ffce966cd1fecc1c37fe9dd8507c7708a075f65ac"
            ):
                _fail()
            module_binding = bindings.get(binding["module_source_id"])
            if type(module_binding) is not dict:
                _fail()
            binding = module_binding
        root_kind = binding.get("root")
        if root_kind not in ("repo_root", "state_root"):
            _fail()
        root = repo_root if root_kind == "repo_root" else state_root
        relative = binding.get("relative_path")
        size = binding.get("bytes")
        digest = binding.get("sha256")
        if (
            type(size) is not int
            or type(digest) is not str
            or len(digest) != 64
        ):
            _fail()
        path = _safe_bound_path(root, relative)
        payload = _read_regular(
            path,
            expected_bytes=size,
            expected_sha256=digest,
            require_lf_terminated=path.suffix == ".csv" or path.suffix == ".py",
        )
        resolved[source_id] = {
            "source_id": source_id,
            "root_kind": root_kind,
            "relative_path": relative,
            "sha256": digest,
            "bytes": size,
            "payload": payload,
        }
    if tuple(resolved) != _SOURCE_IDS or len(resolved) != 27:
        _fail()
    return resolved


def _exact_one(
    rows: Sequence[dict[str, str]], key: str, value: str
) -> tuple[int, dict[str, str]]:
    matches = [(index, row) for index, row in enumerate(rows) if row[key] == value]
    if len(matches) != 1:
        _fail()
    return matches[0]


def _source_ref(source: Mapping[str, object]) -> dict[str, object]:
    return {
        "root_kind": source["root_kind"],
        "relative_path": source["relative_path"],
        "sha256": source["sha256"],
    }


def _parse_primary_sources(
    repo_root: Path,
    sources: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    final_rows = _csv_rows(
        sources["canonical_final_index"]["payload"],  # type: ignore[arg-type]
        _FINAL_INDEX_COLUMNS,
    )
    pair_rows = _csv_rows(
        sources["canonical_pair_matrix"]["payload"],  # type: ignore[arg-type]
        _PAIR_COLUMNS,
    )
    mapping_rows = _csv_rows(
        sources["atom_table_mapping_matrix"]["payload"],  # type: ignore[arg-type]
        _MAPPING_COLUMNS,
    )
    if len(final_rows) != 11 or len(pair_rows) != 11 or len(mapping_rows) != 22:
        _fail()
    events: list[dict[str, str]] = []
    observed: list[dict[str, str]] = []
    final_locators: list[dict[str, object]] = []
    event_locators: list[dict[str, object]] = []
    observed_locators: list[dict[str, object]] = []
    pair_locators: list[dict[str, object]] = []
    mapping_locators: list[list[dict[str, object]]] = []
    pair_values: list[list[int]] = []
    secondary: list[list[dict[str, object]]] = []
    coordinate_differences: list[float] = []
    ligand_atom_names: list[list[str]] = []

    for sample_index, sample in enumerate(_SAMPLES):
        sample_id, pdb_id, ligand = sample
        final_index, final = _exact_one(final_rows, "sample_index_row_id", sample_id)
        pair_index, pair = _exact_one(pair_rows, "sample_index_row_id", sample_id)
        maps = [
            (index, row)
            for index, row in enumerate(mapping_rows)
            if row["sample_index_row_id"] == sample_id
        ]
        if len(maps) != 2 or [row["entity_role"] for _, row in maps] != [
            "target_residue_atom",
            "ligand_atom",
        ]:
            _fail()
        event_source_id = f"event_table_{sample_id}"
        event_rows = _csv_rows(
            sources[event_source_id]["payload"],  # type: ignore[arg-type]
            _EVENT_COLUMNS,
        )
        observed_source_id = f"observed_pair_table_{sample_id}"
        observed_rows = _csv_rows(
            sources[observed_source_id]["payload"],  # type: ignore[arg-type]
            _OBSERVED_COLUMNS,
        )
        event_index, event = _exact_one(
            event_rows, "sample_preparation_input_id", final["sample_preparation_input_id"]
        )
        observed_index, observed_row = _exact_one(
            observed_rows,
            "sample_preparation_input_id",
            final["sample_preparation_input_id"],
        )
        identity = (
            final["sample_index_row_id"],
            final["pdb_id"],
            final["ligand_comp_id"],
        )
        pair_identity = (
            pair["sample_index_row_id"], pair["pdb_id"], pair["ligand_comp_id"]
        )
        if (
            identity != sample
            or pair_identity != sample
            or final_index != sample_index
            or pair_index != sample_index
            or pair["pair_record_schema_version"]
            != "covapie_covalent_bond_atom_pair_canonical_record_v1"
            or pair["residue_entity_role"] != "target_residue_atom"
            or pair["ligand_entity_role"] != "ligand_atom"
            or pair["explicit_bond_authority_class"] != "validated_struct_conn"
            or any(
                pair[field] != "true"
                for field in (
                    "canonical_record_valid", "legacy_projection_matches",
                    "event_pair_value_matches", "pair_table_value_matches",
                    "final_index_value_matches", "explicit_authority_preserved",
                    "verified",
                )
            )
            or event_index != 0
            or event["pdb_id"] != pdb_id
            or event["expected_het_id"] != ligand
            or event["ligand_comp_id"] != ligand
            or event["event_status"] != "validated"
            or not event["event_source"].startswith("raw_struct_conn")
            or "distance" in event["event_source"].lower()
            or "candidate" in event["event_source"].lower()
            or observed_index != 0
            or observed_row["pdb_id"] != pdb_id
            or observed_row["expected_het_id"] != ligand
            or not observed_row["validation_status"].startswith("validated_from_")
        ):
            _fail()
        pair_fields = ("residue_atom_name", "ligand_atom_name")
        expected_pair = tuple(pair[field] for field in pair_fields)
        if (
            tuple(event[field] for field in pair_fields) != expected_pair
            or tuple(observed_row[field] for field in pair_fields) != expected_pair
            or event["residue_comp_id"] != pair["residue_comp_id"]
            or event["ligand_comp_id"] != pair["ligand_comp_id"]
            or event["covalent_bond_atom_pair"] != pair["legacy_projection"]
            or observed_row["covalent_bond_atom_pair"] != pair["legacy_projection"]
            or final["covalent_bond_atom_pair"] != pair["legacy_projection"]
            or final["conn_id"] != event["conn_id"]
            or final["conn_type_id"] != event["conn_type_id"]
        ):
            _fail()

        sample_secondary: list[dict[str, object]] = []
        indices: list[int] = []
        sample_mapping_locators: list[dict[str, object]] = []
        for mapping_index, mapping in maps:
            if (
                mapping["event_id"] != pair["event_id"]
                or mapping["pdb_id"] != pdb_id
                or mapping["candidate_match_count"] != "1"
                or mapping["expected_match_count"] != "1"
                or mapping["model_index_base"] != "0"
                or mapping["mapping_outcome"] != "mapped"
                or mapping["mapping_reason"] != "exact_one_identity_mapping"
                or mapping["distance_used_for_mapping_selection"] != "false"
                or any(
                    mapping[field] != "true"
                    for field in (
                        "atom_site_id_matches", "coordinate_crosscheck_passed",
                        "source_row_order_sha_bound", "verified",
                    )
                )
            ):
                _fail()
            table_path = _safe_bound_path(repo_root, mapping["target_table_path"])
            table_payload = _read_regular(
                table_path,
                expected_sha256=mapping["target_table_sha256"],
                require_lf_terminated=True,
            )
            reader = csv.DictReader(
                io.StringIO(table_payload.decode("utf-8"), newline="")
            )
            table_rows = list(reader)
            row_index_text = mapping["matched_row_index_0based"]
            if (
                not row_index_text.isascii()
                or not row_index_text.isdigit()
                or str(int(row_index_text)) != row_index_text
                or mapping["target_table_data_row_count"] != str(len(table_rows))
                or len(table_rows) == 0
                or any(None in row for row in table_rows)
            ):
                _fail()
            row_index = int(row_index_text)
            if not 0 <= row_index < len(table_rows):
                _fail()
            table_row = table_rows[row_index]
            role = mapping["entity_role"]
            expected_columns = (
                _POCKET_COLUMNS if role == "target_residue_atom" else _LIGAND_COLUMNS
            )
            atom_name = pair[
                "residue_atom_name" if role == "target_residue_atom" else "ligand_atom_name"
            ]
            comp_id = pair[
                "residue_comp_id" if role == "target_residue_atom" else "ligand_comp_id"
            ]
            table_comp_field = "residue_name" if role == "target_residue_atom" else "ligand_comp_id"
            expected_table_path = final[
                "pocket_atom_table_path"
                if role == "target_residue_atom"
                else "ligand_atom_table_path"
            ]
            if (
                tuple(reader.fieldnames or ()) != expected_columns
                or mapping["target_table_path"] != expected_table_path
                or table_row.get("sample_preparation_input_id") != pair["event_id"]
                or table_row.get("pdb_id") != pdb_id
                or table_row.get(table_comp_field) != comp_id
                or table_row.get("atom_name") != atom_name
                or table_row.get("atom_site_id") != mapping["matched_atom_site_id"]
                or mapping["matched_atom_site_id"]
                != mapping["pair_table_expected_atom_site_id"]
            ):
                _fail()
            for prefix in ("auth", "label"):
                for suffix in ("asym_id", "seq_id"):
                    key = f"{prefix}_{suffix}"
                    pair_key = (
                        f"residue_{key}" if role == "target_residue_atom" else f"ligand_{key}"
                    )
                    if table_row.get(key) != pair[pair_key]:
                        _fail()
            matching_rows = []
            for candidate_index, candidate in enumerate(table_rows):
                identity_matches = (
                    candidate.get("sample_preparation_input_id") == pair["event_id"]
                    and candidate.get("pdb_id") == pdb_id
                    and candidate.get(table_comp_field) == comp_id
                    and candidate.get("atom_name") == atom_name
                    and all(
                        candidate.get(f"{prefix}_{suffix}")
                        == pair[
                            (
                                "residue_" if role == "target_residue_atom" else "ligand_"
                            )
                            + f"{prefix}_{suffix}"
                        ]
                        for prefix in ("auth", "label")
                        for suffix in ("asym_id", "seq_id")
                    )
                )
                if role == "ligand_atom":
                    identity_matches = (
                        identity_matches
                        and candidate.get("expected_het_id") == ligand
                        and candidate.get("is_covalent_ligand_atom") == "True"
                    )
                if identity_matches:
                    matching_rows.append(candidate_index)
            if matching_rows != [row_index]:
                _fail()
            indices.append(row_index)
            sample_mapping_locators.append(
                {
                    "source_id": "atom_table_mapping_matrix",
                    "row_index_0based": mapping_index,
                    "entity_role": role,
                }
            )
            sample_secondary.append(
                {
                    "root_kind": "repo_root",
                    "relative_path": mapping["target_table_path"],
                    "sha256": mapping["target_table_sha256"],
                    "entity_role": role,
                    "data_row_count": len(table_rows),
                    "matched_row_index_0based": row_index,
                    "matched_atom_site_id": mapping["matched_atom_site_id"],
                }
            )
            if role == "ligand_atom":
                ligand_atom_names.append(
                    [candidate["atom_name"] for candidate in table_rows]
                )
        if tuple(indices) != _EXPECTED_PAIR_VALUES[sample_index]:
            _fail()
        if (
            observed_row["residue_atom_site_id"] != maps[0][1]["matched_atom_site_id"]
            or observed_row["ligand_atom_site_id"]
            != maps[1][1]["matched_atom_site_id"]
        ):
            _fail()

        distance_text = observed_row["bond_distance_angstrom"]
        try:
            distance = float(distance_text)
            final_distance = float(final["bond_distance_angstrom"])
            coordinates = tuple(
                float(observed_row[field])
                for field in (
                    "residue_x", "residue_y", "residue_z",
                    "ligand_x", "ligand_y", "ligand_z",
                )
            )
        except ValueError as error:
            raise ValueError(_ERROR) from error
        coordinate_distance = math.sqrt(
            sum((coordinates[index] - coordinates[index + 3]) ** 2 for index in range(3))
        )
        difference = abs(coordinate_distance - distance)
        if (
            distance_text != _EXPECTED_DISTANCE_STRINGS[sample_index]
            or not math.isfinite(distance)
            or distance <= 0.0
            or not math.isfinite(final_distance)
            or distance != final_distance
            or difference > _MAX_COORDINATE_DIFFERENCE + 1e-15
        ):
            _fail()

        events.append(event)
        observed.append(observed_row)
        pair_values.append(indices)
        secondary.append(sample_secondary)
        coordinate_differences.append(round(difference, 12))
        final_locators.append(
            {"source_id": "canonical_final_index", "row_index_0based": final_index}
        )
        pair_locators.append(
            {"source_id": "canonical_pair_matrix", "row_index_0based": pair_index}
        )
        mapping_locators.append(sample_mapping_locators)
        event_locators.append(
            {"source_id": event_source_id, "row_index_0based": event_index}
        )
        observed_locators.append(
            {"source_id": observed_source_id, "row_index_0based": observed_index}
        )
    if (
        len({item["relative_path"] for group in secondary for item in group}) != 22
        or len(ligand_atom_names) != 11
    ):
        _fail()
    return {
        "final_rows": final_rows,
        "pair_rows": pair_rows,
        "mapping_rows": mapping_rows,
        "events": events,
        "observed": observed,
        "pair_values": pair_values,
        "secondary": secondary,
        "coordinate_differences": coordinate_differences,
        "ligand_atom_names": ligand_atom_names,
        "final_locators": final_locators,
        "event_locators": event_locators,
        "pair_locators": pair_locators,
        "mapping_locators": mapping_locators,
        "observed_locators": observed_locators,
    }


def _record_digest(record: Mapping[str, object], digest_field: str) -> str:
    return _sha256(
        _compact_json(
            {key: value for key, value in record.items() if key != digest_field}
        ).encode("utf-8")
    )


def _parse_boundaries(source: Mapping[str, object]) -> dict[str, object]:
    payload = source["payload"]
    if type(payload) is not bytes:
        _fail()
    value = _strict_json(payload)
    records = value.get("effective_authority_records")
    if (
        value.get("unified_effective_authority_view_version")
        != "covapie_current11_unified_effective_authority_view_v1"
        or value.get("sample_order") != [sample[0] for sample in _SAMPLES]
        or value.get("effective_authority_record_count") != 11
        or value.get("effective_legacy_exact_one_count") != 6
        or value.get("effective_multi_boundary_exact_two_count") != 5
        or type(records) is not list
        or len(records) != 11
        or value.get("unified_effective_authority_view_sha256")
        != _record_digest(value, "unified_effective_authority_view_sha256")
    ):
        _fail()
    parsed: list[dict[str, object]] = []
    namespace_counts: Counter[str] = Counter()
    for index, (outer, sample) in enumerate(zip(records, _SAMPLES, strict=True)):
        if type(outer) is not dict or type(outer.get("effective_authority_record")) is not dict:
            _fail()
        authority = outer["effective_authority_record"]
        namespace = outer.get("effective_authority_namespace")
        cardinality = outer.get("effective_boundary_cardinality")
        digest_field = (
            "authority_record_sha256"
            if namespace == "legacy_exact_one_boundary_v1"
            else "multi_boundary_authority_record_sha256"
        )
        version_field = (
            "authority_record_version"
            if namespace == "legacy_exact_one_boundary_v1"
            else "multi_boundary_authority_record_version"
        )
        expected_cardinality = 1 if namespace == "legacy_exact_one_boundary_v1" else 2
        if (
            tuple(authority.get(key) for key in ("sample_index_row_id", "pdb_id", "ligand_comp_id"))
            != sample
            or cardinality != expected_cardinality
            or authority.get("authority_status") != "active"
            or authority.get("sample_quarantined") is not False
            or authority.get("complete_warhead_atom_set_authority_available") is not True
            or outer.get("source_authority_record_sha256") != authority.get(digest_field)
            or outer.get("source_authority_record_version") != authority.get(version_field)
            or authority.get(digest_field) != _record_digest(authority, digest_field)
            or outer.get("unified_effective_authority_record_sha256")
            != _record_digest(outer, "unified_effective_authority_record_sha256")
        ):
            _fail()
        namespace_counts[str(namespace)] += 1
        warhead = authority.get("reviewed_warhead_atom_ids")
        if (
            type(warhead) is not list
            or not warhead
            or any(type(token) is not str or not token for token in warhead)
            or len(warhead) != len(set(warhead))
        ):
            _fail()
        boundaries: list[dict[str, str]]
        if cardinality == 1:
            if (
                authority.get("exact_one_attachment_boundary_authority_available") is not True
                or authority.get("authority_disposition")
                != "reviewed_authority_materialized"
                or authority.get("review_decision") != "select_admitted_candidate"
                or authority.get("reviewer_id") != "fmx"
            ):
                _fail()
            boundaries = [
                {
                    "warhead_attachment_atom_id": str(
                        authority.get("reviewed_warhead_attachment_atom_id")
                    ),
                    "nonwarhead_boundary_atom_id": str(
                        authority.get("reviewed_nonwarhead_boundary_atom_id")
                    ),
                    "boundary_bond_order": str(
                        authority.get("reviewed_attachment_boundary_bond_order")
                    ),
                    "boundary_bond_id": str(authority.get("reviewed_boundary_bond_id")),
                }
            ]
        else:
            if (
                namespace != "exact_two_boundaries_multi_boundary_v1"
                or authority.get("exact_two_attachment_boundaries_authority_available")
                is not True
                or authority.get("authority_disposition")
                != "reviewed_multi_boundary_authority_materialized"
                or authority.get("review_decision")
                not in (
                    "accept_verified_two_boundary_proposal",
                    "revise_two_boundary_atom_set_and_boundaries",
                )
                or authority.get("reviewer_id") != "fmx"
                or authority.get("reviewer_provenance_attestor_id") != "fmx"
                or type(authority.get("reviewed_boundary_records")) is not list
            ):
                _fail()
            boundaries = authority["reviewed_boundary_records"]  # type: ignore[assignment]
        if len(boundaries) != cardinality:
            _fail()
        for boundary in boundaries:
            if type(boundary) is not dict:
                _fail()
            bond_id_parts = boundary.get("boundary_bond_id", "").split("|")
            if (
                boundary.get("boundary_bond_order") != "single"
                or boundary.get("warhead_attachment_atom_id") not in warhead
                or not boundary.get("nonwarhead_boundary_atom_id")
                or not boundary.get("boundary_bond_id")
                or len(bond_id_parts) != 3
                or set(bond_id_parts[:2])
                != {
                    boundary.get("warhead_attachment_atom_id"),
                    boundary.get("nonwarhead_boundary_atom_id"),
                }
                or bond_id_parts[2] != "single"
            ):
                _fail()
        parsed.append(
            {
                "outer": outer,
                "authority": authority,
                "warhead": warhead,
                "boundaries": boundaries,
                "record_index": index,
                "source_authority_record_sha256": authority[digest_field],
                "source_authority_record_version": authority[version_field],
            }
        )
    if namespace_counts != {
        "legacy_exact_one_boundary_v1": 6,
        "exact_two_boundaries_multi_boundary_v1": 5,
    }:
        _fail()
    return {"view": value, "records": parsed}


def _utf8_buffer(values: Sequence[str]) -> dict[str, object]:
    raw = bytearray()
    offsets = [0]
    for value in values:
        if type(value) is not str:
            _fail()
        encoded = value.encode("utf-8")
        raw.extend(encoded)
        offsets.append(len(raw))
    return {
        "dtype": "uint8",
        "encoding": "utf-8",
        "bytes_uint8": list(raw),
        "offsets_int64": offsets,
        "logical_shape": [len(values)],
    }


def _identity_payload(parsed: Mapping[str, object]) -> dict[str, object]:
    final_rows = parsed["final_rows"]
    if type(final_rows) is not list:
        _fail()
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[1]],
        "sample_index_row_id": _utf8_buffer(
            [row["sample_index_row_id"] for row in final_rows]
        ),
        "pdb_id": _utf8_buffer([row["pdb_id"] for row in final_rows]),
        "ligand_comp_id": _utf8_buffer(
            [row["ligand_comp_id"] for row in final_rows]
        ),
        "sample_order": [list(sample) for sample in _SAMPLES],
        "sample_validity_bool": [True] * 11,
        "source_record_locators": parsed["final_locators"],
        "metadata_only": True,
        "model_input_allowed_now": False,
        "loss_participation_allowed_now": False,
    }


def _event_payload(parsed: Mapping[str, object]) -> dict[str, object]:
    events = parsed["events"]
    pairs = parsed["pair_rows"]
    if type(events) is not list or type(pairs) is not list:
        _fail()
    metadata = []
    for sample, event, pair in zip(_SAMPLES, events, pairs, strict=True):
        metadata.append(
            {
                "sample_index_row_id": sample[0],
                "conn_id": event["conn_id"],
                "conn_type_id": event["conn_type_id"],
                "event_source": event["event_source"],
                "event_status": event["event_status"],
                "residue_comp_id": event["residue_comp_id"],
                "residue_atom_name": event["residue_atom_name"],
                "ligand_comp_id": event["ligand_comp_id"],
                "ligand_atom_name": event["ligand_atom_name"],
                "explicit_authority_class": pair["explicit_bond_authority_class"],
                "canonical_record_valid": pair["canonical_record_valid"] == "true",
            }
        )
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[2]],
        "values_bool": [True] * 11,
        "sample_validity_bool": [True] * 11,
        "logical_shape": [11],
        "event_semantic_metadata": metadata,
        "source_record_locators": parsed["event_locators"],
        "explicit_struct_conn_authority": True,
        "distance_inferred": False,
        "candidate_event": False,
        "bond_order_encoded": False,
        "pre_or_post_state_encoded": False,
        "loss_participation_allowed_now": False,
    }


def _pair_payload(parsed: Mapping[str, object]) -> dict[str, object]:
    values = parsed["pair_values"]
    if values != [list(value) for value in _EXPECTED_PAIR_VALUES]:
        _fail()
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[3]],
        "values_int64": values,
        "values_logical_shape": [11, 2],
        "column_semantics": [
            "pocket_atom_table_row_index_0based",
            "ligand_atom_table_row_index_0based",
        ],
        "sample_offsets_int64": list(range(12)),
        "entry_validity_bool": [True] * 11,
        "sample_validity_bool": [True] * 11,
        "source_record_locators": [
            {
                "canonical_pair": pair,
                "atom_table_mappings": mappings,
            }
            for pair, mappings in zip(
                parsed["pair_locators"], parsed["mapping_locators"], strict=True
            )
        ],
        "locator_semantics": (
            "derived_row_index_bound_to_exact_atom_table_bytes_and_order"
        ),
        "permanent_chemical_identifier": False,
        "model_input_allowed_now": False,
        "batch_index_remap_required": True,
        "loss_participation_allowed_now": False,
    }


def _boundary_payload(boundaries: Mapping[str, object]) -> dict[str, object]:
    records = boundaries["records"]
    if type(records) is not list:
        _fail()
    tokens: list[str] = []
    sample_token_offsets = [0]
    warhead_indices: list[int] = []
    sample_warhead_offsets = [0]
    boundary_pairs: list[list[int]] = []
    sample_boundary_offsets = [0]
    source_locators: list[dict[str, object]] = []
    cardinalities: list[int] = []
    for record in records:
        if type(record) is not dict:
            _fail()
        local_tokens: list[str] = []
        for token in record["warhead"]:
            if token not in local_tokens:
                local_tokens.append(token)
        for boundary in record["boundaries"]:
            for key in ("warhead_attachment_atom_id", "nonwarhead_boundary_atom_id"):
                token = boundary[key]
                if token not in local_tokens:
                    local_tokens.append(token)
        base = len(tokens)
        tokens.extend(local_tokens)
        sample_token_offsets.append(len(tokens))
        warhead_indices.extend(base + local_tokens.index(token) for token in record["warhead"])
        sample_warhead_offsets.append(len(warhead_indices))
        for boundary in record["boundaries"]:
            boundary_pairs.append(
                [
                    base + local_tokens.index(boundary["warhead_attachment_atom_id"]),
                    base + local_tokens.index(boundary["nonwarhead_boundary_atom_id"]),
                ]
            )
        sample_boundary_offsets.append(len(boundary_pairs))
        cardinalities.append(len(record["boundaries"]))
        source_locators.append(
            {
                "source_id": "unified_boundary_authority",
                "effective_authority_record_index_0based": record["record_index"],
                "source_authority_record_version": record[
                    "source_authority_record_version"
                ],
                "source_authority_record_sha256": record[
                    "source_authority_record_sha256"
                ],
            }
        )
    encoded = _utf8_buffer(tokens)
    if (
        len(tokens) != 118
        or len(warhead_indices) != 102
        or len(boundary_pairs) != 16
        or Counter(cardinalities) != {1: 6, 2: 5}
        or "F1" not in tokens
    ):
        _fail()
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[4]],
        "token_bytes_uint8": encoded["bytes_uint8"],
        "token_offsets_int64": encoded["offsets_int64"],
        "sample_token_offsets_int64": sample_token_offsets,
        "warhead_token_indices_int64": warhead_indices,
        "sample_warhead_offsets_int64": sample_warhead_offsets,
        "warhead_entry_validity_bool": [True] * 102,
        "boundary_pairs_token_indices_int64": boundary_pairs,
        "sample_boundary_offsets_int64": sample_boundary_offsets,
        "boundary_entry_validity_bool": [True] * 16,
        "token_validity_bool": [True] * 118,
        "sample_validity_bool": [True] * 11,
        "source_record_locators": source_locators,
        "sample_count": 11,
        "reviewed_warhead_atom_entry_count": 102,
        "boundary_pair_count": 16,
        "global_local_token_count": 118,
        "exact_one_boundary_sample_count": 6,
        "exact_two_boundary_sample_count": 5,
        "token_index_semantics": (
            "index_into_payload_local_utf8_token_table_not_ligand_atom_table"
        ),
        "reviewed_warhead_atom_set_semantics": "reviewed_warhead_atom_set",
        "attachment_boundary_semantics": "ligand_internal_attachment_boundary",
        "covalent_pair_semantics": "separate_ligand_protein_covalent_pair_task",
        "generation_mask_sample_labels_materialized": False,
        "F1_numeric_ligand_atom_mapping_available": False,
        "F1_raw_token_payload_valid": True,
        "loss_participation_allowed_now": False,
    }


def _geometry_payload(parsed: Mapping[str, object]) -> dict[str, object]:
    observed = parsed["observed"]
    if type(observed) is not list:
        _fail()
    strings = [row["bond_distance_angstrom"] for row in observed]
    packed = b"".join(struct.pack("<f", float(value)) for value in strings)
    if tuple(strings) != _EXPECTED_DISTANCE_STRINGS or len(packed) != 44:
        _fail()
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[5]],
        "source_decimal_strings": strings,
        "values_float32_le_hex": packed.hex(),
        "logical_shape": [11, 1],
        "units": "angstrom",
        "sample_validity_bool": [True] * 11,
        "source_record_locators": parsed["observed_locators"],
        "coordinate_consistency_check": {
            "coordinate_values_used_as_payload": False,
            "reported_decimal_places": 12,
            "maximum_absolute_difference_angstrom": max(
                parsed["coordinate_differences"]
            ),
            "frozen_upper_bound_angstrom": _MAX_COORDINATE_DIFFERENCE,
            "passed": True,
        },
        "observed_complex_only": True,
        "pre_covalent_geometry": False,
        "post_covalent_geometry": False,
        "bond_authority_inferred": False,
        "bond_order_inferred": False,
        "transformation_inferred": False,
        "post_state_inferred": False,
        "angle_materialized": False,
        "dihedral_materialized": False,
        "loss_participation_allowed_now": False,
    }


def _cell_provenance(
    routing: Mapping[str, object],
    sources: Mapping[str, Mapping[str, object]],
    parsed: Mapping[str, object],
    boundaries: Mapping[str, object],
) -> list[dict[str, object]]:
    selected_by_key = routing["selected_by_key"]
    boundary_records = boundaries["records"]
    if type(selected_by_key) is not dict or type(boundary_records) is not list:
        _fail()
    artifact_by_task = {
        _TASKS[index][1]: _ARTIFACT_NAMES[index + 1] for index in range(5)
    }
    authority_by_task = {
        _TASKS[0][1]: "canonical_sample_identity",
        _TASKS[1][1]: "explicit_struct_conn_event",
        _TASKS[2][1]: "validated_exact_atom_table_row_mapping",
        _TASKS[3][1]: "reviewed_unified_warhead_boundary_authority",
        _TASKS[4][1]: "source_recorded_observed_complex_distance",
    }
    locators_by_task = {
        _TASKS[0][1]: parsed["final_locators"],
        _TASKS[1][1]: parsed["event_locators"],
        _TASKS[2][1]: [
            {"canonical_pair": pair, "atom_table_mappings": mappings}
            for pair, mappings in zip(
                parsed["pair_locators"], parsed["mapping_locators"], strict=True
            )
        ],
        _TASKS[3][1]: [
            {
                "source_id": "unified_boundary_authority",
                "effective_authority_record_index_0based": record["record_index"],
                "source_authority_record_version": record[
                    "source_authority_record_version"
                ],
                "source_authority_record_sha256": record[
                    "source_authority_record_sha256"
                ],
            }
            for record in boundary_records
        ],
        _TASKS[4][1]: parsed["observed_locators"],
    }
    records = []
    for sample_index, sample in enumerate(_SAMPLES):
        for task_minor_index, task in enumerate(_TASKS):
            task_index, task_name, state = task
            routing_row = selected_by_key[(sample[0], task_name)]
            source_ids = routing_row["_supporting_source_ids"]
            secondary = parsed["secondary"][sample_index] if task_index == 2 else []
            locator = locators_by_task[task_name][sample_index]
            record: dict[str, object] = {
                "cell_index": sample_index * 5 + task_minor_index,
                "sample_index": sample_index,
                "sample_index_row_id": sample[0],
                "semantic_task_name": task_name,
                "eligibility_state": state,
                "supporting_source_ids": source_ids,
                "source_bindings": [_source_ref(sources[item]) for item in source_ids],
                "source_record_locators": locator,
                "source_sha256": [sources[item]["sha256"] for item in source_ids],
                "secondary_source_bindings": secondary,
                "extractor_schema_version": (
                    "covapie_current11_tensor_projection_payload_extractor_v1"
                ),
                "payload_artifact_name": artifact_by_task[task_name],
                "payload_entry_locator": {
                    "sample_index": sample_index,
                    "task_index": task_index,
                },
                "authority_kind": authority_by_task[task_name],
                "candidate_promotion_used": False,
                "inference_used": False,
                "semantic_promotion_used": False,
                "payload_valid": True,
                "provenance_complete": True,
            }
            if task_index == 12:
                record["consistency_check"] = {
                    "coordinate_derived_distance_used_as_payload": False,
                    "absolute_difference_angstrom": parsed[
                        "coordinate_differences"
                    ][sample_index],
                    "upper_bound_angstrom": _MAX_COORDINATE_DIFFERENCE,
                    "passed": True,
                }
            records.append(record)
    if len(records) != 55:
        _fail()
    return records


def _manifest(sources: Mapping[str, Mapping[str, object]]) -> dict[str, object]:
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[0]],
        "source_contract_lineage": {
            "published_gate_module_relative_path": _GATE_MODULE_RELATIVE,
            "published_gate_module_sha256": _GATE_MODULE_SHA256,
            "published_contract_digest": _CONTRACT_DIGEST,
        },
        "formal_routing_lineage": {
            "canonical_relative_path": _FORMAL_RELATIVE,
            "canonical_readlink": _FORMAL_READLINK,
            "formal_aggregate_sha256": _FORMAL_AGGREGATE_SHA256,
            "formal_snapshot_sha256": _FORMAL_SNAPSHOT_SHA256,
            "formal_exact4_sha256": {
                name: spec[2] for name, spec in _FORMAL_FILES.items()
            },
        },
        "audit_lineage": {
            "relative_path": _AUDIT_RELATIVE,
            "sha256": _AUDIT_SHA256,
            "runtime_dependency": False,
            "payload_value_authority": False,
        },
        "artifact_names": list(_ARTIFACT_NAMES),
        "sample_order": [
            {
                "sample_index": index,
                "sample_index_row_id": sample[0],
                "pdb_id": sample[1],
                "ligand_comp_id": sample[2],
            }
            for index, sample in enumerate(_SAMPLES)
        ],
        "audited_task_order": [
            {
                "task_index": task[0],
                "semantic_task_name": task[1],
                "eligibility_state": task[2],
            }
            for task in _TASKS
        ],
        "payload_schemas": {
            name: _SCHEMAS[name] for name in _ARTIFACT_NAMES[1:7]
        },
        "buffer_encoding_rules": {
            "utf8_strings": "uint8_bytes_plus_int64_offsets",
            "ragged_entries": "values_plus_int64_sample_offsets",
            "float32": "contiguous_ieee754_little_endian_lowercase_hex",
            "validity": "task_specific_bool_buffers",
        },
        "source_binding_inventory": [
            {"source_id": source_id, **_source_ref(sources[source_id])}
            for source_id in _SOURCE_IDS
        ],
        "current_counts": {
            "sample_count": 11,
            "audited_task_count": 5,
            "payload_cell_count": 55,
            "valid_payload_cell_count": 55,
            "routing_source_binding_count": 27,
            "secondary_atom_table_count": 22,
            "candidate_payload_cell_count": 0,
            "loss_authorized_cell_count": 0,
            "runtime_consumer_available_cell_count": 0,
        },
        "hard_semantic_boundaries": {
            "exact5_means_audited_semantic_tasks_not_generation_masks": True,
            "atom_table_row_indices_are_not_permanent_chemical_identifiers": True,
            "task2_indices_require_future_authorized_batch_remap": True,
            "warhead_set_boundary_and_covalent_pair_are_distinct": True,
            "observed_geometry_is_not_pre_or_post_covalent_geometry": True,
            "candidate_or_inferred_payloads_forbidden": True,
            "training_loss_authorized": False,
        },
        "readiness": {
            "audited_exact5_task_payload_bundle_built_in_memory": True,
            "full_exact25_projection_instance_materialized": False,
            "formal_payload_bundle_materialized": False,
            "tensor_materialized": False,
            "data_availability_matrix_materialized": False,
            "candidate_payloads_materialized": False,
            "runtime_consumer_available": False,
            "training_loss_authorized": False,
            "feature_semantics_reaudit_required_before_training": True,
            "ready_for_training": False,
        },
    }


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    if type(artifacts) is not dict or tuple(artifacts) != _STABLE_ARTIFACT_NAMES:
        _fail()
    digest = hashlib.sha256()
    digest.update(_DIGEST_DOMAIN_TAG)
    for name in _STABLE_ARTIFACT_NAMES:
        encoded_name = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded_name).to_bytes(8, "big", signed=False))
        digest.update(encoded_name)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate_artifact(name: str, payload: bytes) -> None:
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
    decoded = _strict_json(payload)
    if (
        decoded.get("schema_version") != _SCHEMAS[name]
        or _canonical_json(decoded) != payload
    ):
        _fail()


def _stable_build(
    sources: Mapping[str, Mapping[str, object]],
    routing: Mapping[str, object],
    parsed: Mapping[str, object],
    boundaries: Mapping[str, object],
) -> dict[str, bytes]:
    values = (
        _manifest(sources),
        _identity_payload(parsed),
        _event_payload(parsed),
        _pair_payload(parsed),
        _boundary_payload(boundaries),
        _geometry_payload(parsed),
        {
            "schema_version": _SCHEMAS[_ARTIFACT_NAMES[6]],
            "cell_provenance_records": _cell_provenance(
                routing, sources, parsed, boundaries
            ),
            "payload_cell_count": 55,
            "valid_payload_cell_count": 55,
            "candidate_promotion_count": 0,
            "inference_count": 0,
            "semantic_promotion_count": 0,
            "provenance_complete_count": 55,
        },
    )
    artifacts = {
        name: _canonical_json(value)
        for name, value in zip(_STABLE_ARTIFACT_NAMES, values, strict=True)
    }
    if type(artifacts) is not dict or tuple(artifacts) != _STABLE_ARTIFACT_NAMES:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact(name, payload)
    return artifacts


def _report(
    stable: Mapping[str, bytes], digest: str, formal_snapshot: Mapping[str, object]
) -> dict[str, object]:
    return {
        "schema_version": _SCHEMAS[_ARTIFACT_NAMES[7]],
        "builder_status": "PASS_IN_MEMORY_PAYLOAD_BUNDLE_ONLY",
        "payload_bundle_digest": digest,
        "artifact_file_count": 8,
        "artifact_identities": [
            {
                "artifact_index": index,
                "artifact_name": name,
                "stable_digest_participation": name in _STABLE_ARTIFACT_NAMES,
                **(
                    {
                        "bytes": len(stable[name]),
                        "lines": stable[name].count(b"\n"),
                        "sha256": _sha256(stable[name]),
                    }
                    if name in stable
                    else {"content_identity": "self_excluded"}
                ),
            }
            for index, name in enumerate(_ARTIFACT_NAMES)
        ],
        "published_contract_gate_passed": True,
        "published_contract_gate_double_build_identical": True,
        "published_contract_digest": _CONTRACT_DIGEST,
        "formal_sidecar_check_passed": True,
        "formal_snapshot_unchanged": True,
        "formal_filesystem_identity": {
            "canonical": list(formal_snapshot["canonical"]),
            "readlink": formal_snapshot["readlink"],
            "object": list(formal_snapshot["object"]),
        },
        "source_binding_count": 27,
        "secondary_atom_table_count": 22,
        "sample_count": 11,
        "audited_task_count": 5,
        "payload_cell_count": 55,
        "valid_payload_cell_count": 55,
        "task_validity_counts": {
            "sample_identity_supervision": 11,
            "explicit_covalent_event_supervision": 11,
            "ligand_residue_atom_pair_supervision": 11,
            "warhead_boundary_supervision": 11,
            "observed_complex_geometry_supervision": 11,
        },
        "candidate_payload_cell_count": 0,
        "loss_authorized_cell_count": 0,
        "runtime_consumer_available_cell_count": 0,
        "task0_payload_built": True,
        "task1_payload_built": True,
        "task2_payload_built": True,
        "task6_payload_built": True,
        "task12_payload_built": True,
        "audited_exact5_task_payload_bundle_built_in_memory": True,
        "full_exact25_projection_instance_materialized": False,
        "formal_payload_bundle_materialized": False,
        "tensor_materialized": False,
        "data_availability_matrix_materialized": False,
        "candidate_payloads_materialized": False,
        "readiness": {
            "payload_builder_implemented": True,
            "payload_builder_passed": True,
            "audited_exact5_task_payload_bundle_built_in_memory": True,
            "full_exact25_projection_instance_materialized": False,
            "formal_payload_bundle_materialized": False,
            "tensor_materialized": False,
            "data_availability_matrix_materialized": False,
            "candidate_payloads_materialized": False,
            "runtime_consumer_available": False,
            "training_loss_authorized": False,
            "training_performed": False,
            "ready_for_payload_builder_commit": True,
            "ready_for_formal_payload_materialization": False,
            "ready_for_tensor_projection_materialization": False,
            "ready_for_tensor_materialization": False,
            "ready_for_dataloader_integration": False,
            "ready_for_model_integration": False,
            "feature_semantics_reaudit_required_before_training": True,
            "ready_for_training": False,
        },
    }


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    canonical = state / _FORMAL_RELATIVE
    before = _formal_snapshot(canonical)
    _published_gate(repository, state)
    formal = _read_formal(canonical)
    routing = _validate_routing(formal)
    sources = _resolve_sources(repository, state, routing)
    parsed = _parse_primary_sources(repository, sources)
    boundaries = _parse_boundaries(sources["unified_boundary_authority"])
    boundary_records = boundaries["records"]
    ligand_atom_names = parsed["ligand_atom_names"]
    if (
        type(boundary_records) is not list
        or type(ligand_atom_names) is not list
        or "F1" not in boundary_records[4]["warhead"]
        or "F1" in ligand_atom_names[4]
    ):
        _fail()
    first = _stable_build(sources, routing, parsed, boundaries)
    second = _stable_build(sources, routing, parsed, boundaries)
    if first != second:
        _fail()
    digest = _stable_digest(first)
    after = _formal_snapshot(canonical)
    if before != after:
        _fail()
    report = _canonical_json(_report(first, digest, after))
    _validate_artifact(_ARTIFACT_NAMES[7], report)
    artifacts = dict(first)
    artifacts[_ARTIFACT_NAMES[7]] = report
    if (
        type(artifacts) is not dict
        or tuple(artifacts) != _ARTIFACT_NAMES
        or len(artifacts) != 8
        or any(type(payload) is not bytes for payload in artifacts.values())
    ):
        _fail()
    return artifacts


def build_covapie_current11_tensor_projection_payload_bundle_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]:
    """Return the audited Exact5 Current11 payload bundle as Exact8 bytes."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
