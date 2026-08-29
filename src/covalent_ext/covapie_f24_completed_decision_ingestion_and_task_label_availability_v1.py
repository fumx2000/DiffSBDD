"""Ingest the frozen F24 Exact4 human decision as deterministic metadata.

This additive owner validates, binds, and projects existing sample-level human
authority.  It does not reinterpret F24 chemistry, select a machine role
candidate, create reusable authority or a minimal seed, reconcile global state,
refresh the census or priority queue, admit training data, tensorize, or train.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
import csv
from datetime import datetime
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


__all__ = (
    "F24IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_f24_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_f24_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_f24_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_f24_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_f24_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_f24_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_f24_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_f24_event_task_label_availability_v1.csv"
SUMMARY = "covapie_f24_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_f24_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen only after semantic validation of the source-derived projection.
# They bind derived metadata, never human/scientific authority.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385"
)

FORMAL_ROOT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "F24_COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "f24_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_f24_formal_human_decision_v1.py"
PREPARATION_ROOT = FORMAL_ROOT.parent / "review-preparation-v1"

FORMAL_DECISION_SCHEMA = "covapie_f24_exact4_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "4b53bd14fec9eb89f779c37aaebf61bf5b3754b9d11980e19ae88e2284c87fc6"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5"
EXPECTED_APPROVED_AT_UTC = "2026-08-29T01:36:28Z"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_D6 = (
    "F24 is hymeglusin in PDB 3V4X, an experimentally observed beta-lactone "
    "HMG-CoA synthase inhibitor forming a covalent thioester adduct between "
    "Enterococcus faecalis mvaS Cys111 SG and ligand atom C8. External "
    "scientific evidence together with the frozen F24 graph supports a "
    "sample-level ring-opened beta-lactone interpretation in which C1, C2, "
    "C8, O2, and O6 define the chemical warhead core. For the canonical "
    "sample-level role partition, the proximal hydroxymethyl substituent "
    "C4/O5 is additionally absorbed into the warhead role region, yielding a "
    "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 partition with no linker and a "
    "single C2-C5 scaffold-warhead boundary. C4/O5 is not asserted to be "
    "part of the beta-lactone chemical warhead itself; its inclusion is "
    "limited to the sample-level role-region annotation required for a "
    "connected canonical partition. The remaining heavy atoms form the "
    "retained non-warhead recognition region. No reusable reaction-family, "
    "warhead-rule, warhead-type, cross-sample chemistry, PRE-topology, "
    "PRE-geometry, complete POST-topology, training-admission, split, tensor, "
    "runtime, or parameter-update authority is created by this human "
    "decision. An INCLUDE training-use choice denotes sample-level "
    "disposition only and is not formal training admission."
)

AUTHORITY_SOURCE = "FORMAL_F24_HUMAN_DECISION"
AUTHORITY_SCOPE = "F24_EXACT4_SAMPLE_LEVEL_ONLY"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
CHEMICAL_SCOPE = "F24_SAMPLE_LEVEL_ONLY"

EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:3V4X:A:CYS:111-:SG:E:F24:C8",
        593, "A", "E", "covale1", 1.833648, "1.833648",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3V4X:B:CYS:111-:SG:F:F24:C8",
        594, "B", "F", "covale2", 1.671136, "1.671136",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3V4X:C:CYS:111-:SG:G:F24:C8",
        595, "C", "G", "covale3", 1.893800, "1.893800",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3V4X:D:CYS:111-:SG:H:F24:C8",
        596, "D", "H", "covale4", 1.599498, "1.599498",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
CHEMICAL_WARHEAD = ("C1", "C2", "C8", "O2", "O6")
WARHEAD_ROLE = ("C1", "C2", "C4", "C8", "O2", "O5", "O6")
LINKER_ROLE: tuple[str, ...] = ()
SCAFFOLD_ROLE = (
    "C10", "C11", "C12", "C13", "C14", "C16", "C18", "C20",
    "C21", "C3", "C5", "C6", "C7", "C9", "O1", "O4",
)
HEAVY_ATOMS = tuple(sorted((*WARHEAD_ROLE, *SCAFFOLD_ROLE)))
CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (
        4,
        "scaffold_plus_linker_plus_warhead",
        "C",
        ("scaffold", "linker", "warhead"),
        ("minimal_seed",),
    ),
)
DIRECT_VALID_TASK_IDS = (0, 3, 4)

# (path, namespace, byte_count, sha256, source_role, required_mode)
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE, "project_parent_relative", 26652,
        "ec2bc7c96e6272e99202a8cdbdef330ea4c1189f5fd47abe43f55de2a2db5f22",
        "F24_FROZEN_FORMAL_HUMAN_DECISION", "0664",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE, "project_parent_relative", 45469,
        "c9f2356020b4666e24236dffae63ad368d6bd9f7f0efdff055286a7a2f9f0921",
        "F24_FROZEN_FORMAL_VALIDATOR", "0664",
    ),
)
PREPARATION_BINDINGS = (
    (PREPARATION_ROOT / "HUMAN_REVIEW_GUIDE.md", "project_parent_relative", 6052, "bc369a4f2f5ef7b6421111f628d074de6866a377357fb87c4ce21a033ef109d8", "F24_HUMAN_REVIEW_GUIDE_REVIEWED_BYTES", "0664"),
    (PREPARATION_ROOT / "f24_exact4_event_review_v1.csv", "project_parent_relative", 5258, "d9cc9a213f2daa1795b631329adb1b3e18a0f4391aec6f38b525b60f2ad3f361", "F24_EXACT4_EVENT_REVIEWED_BYTES", "0664"),
    (PREPARATION_ROOT / "f24_graph_and_role_candidates_v1.json", "project_parent_relative", 34186, "389ff675c157adf5d7befad3a3d1bfac0926c742be6e26851ff70cfa659350ce", "F24_GRAPH_AND_ROLE_CANDIDATES_REVIEWED_BYTES", "0664"),
    (PREPARATION_ROOT / "f24_machine_evidence_manifest_v1.json", "project_parent_relative", 14996, "58381c87f3f958b0f887dd8e232bfe08c8a4cd5f3610822e13b6c61d3d117c46", "F24_MACHINE_EVIDENCE_MANIFEST_REVIEWED_BYTES", "0664"),
    (PREPARATION_ROOT / "f24_unsigned_human_decision_template_v1.json", "project_parent_relative", 4010, "b1db19747fc3806ae231120da4591e41c876875cd1c5e33c9d79bda52b121594", "F24_UNSIGNED_DECISION_TEMPLATE_REVIEWED_BYTES", "0664"),
    (PREPARATION_ROOT / "ligand_f24_review_package_v1.py", "project_parent_relative", 108952, "b6d2d273a07ca806f24bdd207334d774e073d99fd9f43c585cc1e3b4ea1aac6c", "F24_REVIEW_PACKAGE_VALIDATOR_REVIEWED_BYTES", "0664"),
)
SEMANTIC_OWNER_BINDINGS = (
    (Path("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"), "repository_relative", 37255, "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535", "PUBLISHED_DIRECT_ROLE_RUNTIME_OWNER", None),
    (Path("src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"), "repository_relative", 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", "CANONICAL_ROLE_AND_TASK_SEMANTICS_OWNER", None),
)
PRECEDENT_BINDINGS = (
    (Path("src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py"), "repository_relative", 106888, "abb80e28e1e139c3515a01c53468530a815c5554b94053afb607053d14a84deb", "LATEST_OZJ_INGESTION_ARCHITECTURE_PRECEDENT", None),
    (Path("data/derived/covalent_small/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1/covapie_ozj_event_task_label_availability_v1.csv"), "repository_relative", 9031, "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3", "OZJ_INGESTION_MATRIX_PRECEDENT", None),
    (Path("src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py"), "repository_relative", 82003, "8339aaa2c57fe1637ab4e4feb7db964fc76224957687d2e0752e28ba3b093928", "YUN_DIRECT_INCLUDE_INGESTION_PRECEDENT", None),
    (Path("data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_event_task_label_availability_v1.csv"), "repository_relative", 13886, "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e", "YUN_DIRECT_INCLUDE_MATRIX_PRECEDENT", None),
)
CENSUS_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1"
)
CENSUS_BINDINGS = (
    (Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_ozj_v1.py"), "repository_relative", 63980, "140c5668b9662829eb359d09504348baf99533ce78cec8307f057a93bf130d0a", "CURRENT_OZJ_REFRESHED_CENSUS_OWNER", None),
    (CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1.csv", "repository_relative", 525890, "1d73fe9702988244006063ab522b3e8222837879c6f00d8deac032a54db2f9b6", "CURRENT_OZJ_REFRESHED_CENSUS_CSV", None),
    (CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_ozj_v1.json", "repository_relative", 15982, "d6b249101eaec5e50d6d9585a05c9de0485bcea24d4d4143444429ab97408f56", "CURRENT_OZJ_REFRESHED_CENSUS_SUMMARY", None),
    (CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_manifest_with_ozj_v1.json", "repository_relative", 41425, "a56a5c7351b66b472bc644792b4a092e110ba01ab20ae28546c3be5caf80dd4d", "CURRENT_OZJ_REFRESHED_CENSUS_MANIFEST", None),
)


class F24IngestionSafetyError(ValueError):
    """Raised when the frozen F24 ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise F24IngestionSafetyError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=header,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _exact(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return set(actual) == set(expected) and all(  # type: ignore[arg-type]
            _exact(actual[key], expected[key]) for key in expected  # type: ignore[index]
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(  # type: ignore[arg-type]
            _exact(left, right) for left, right in zip(actual, expected)  # type: ignore[arg-type]
        )
    return actual == expected


def _expect(actual: object, expected: object, reason: str) -> None:
    if not _exact(actual, expected):
        _fail(reason)


def _parse_utc(value: object) -> datetime:
    if type(value) is not str:
        _fail("APPROVED_AT_UTC_TYPE_INVALID")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise F24IngestionSafetyError("APPROVED_AT_UTC_INVALID") from error
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        _fail("APPROVED_AT_UTC_NONCANONICAL")
    return parsed


def _semantic_digest(document: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(document))
    digest = clone.pop("formal_semantic_canonical_sha256", None)
    if type(digest) is not str or len(digest) != 64:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha(_canonical_json(clone))


def _resolve_binding_path(
    repo_root: Path,
    binding: tuple[Path, str, int, str, str, str | None],
    overrides: Mapping[Path, Path],
) -> Path:
    relative, namespace, _count, _digest, _role, _mode = binding
    if relative in overrides:
        return Path(overrides[relative])
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    _fail("SOURCE_NAMESPACE_INVALID:" + namespace)


def _binding_record(
    binding: tuple[Path, str, int, str, str, str | None]
) -> dict[str, object]:
    relative, namespace, count, digest, role, mode = binding
    record: dict[str, object] = {
        "path": relative.as_posix(),
        "path_namespace": namespace,
        "byte_count": count,
        "sha256": digest,
        "sha256_scope": "file_bytes",
        "source_role": role,
    }
    if mode is not None:
        record["mode"] = mode
    return record


def _expected_binding_records(
    bindings: Sequence[tuple[Path, str, int, str, str, str | None]],
) -> list[dict[str, object]]:
    return [_binding_record(binding) for binding in bindings]


def _verify_binding(
    repo_root: Path,
    binding: tuple[Path, str, int, str, str, str | None],
    overrides: Mapping[Path, Path],
) -> bytes:
    relative, _namespace, count, digest, role, mode = binding
    path = _resolve_binding_path(repo_root, binding, overrides)
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise F24IngestionSafetyError("SOURCE_MISSING:" + role) from error
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR:" + role)
    payload = path.read_bytes()
    if len(payload) != count:
        _fail("SOURCE_BYTE_COUNT_DRIFT:" + role)
    if _sha(payload) != digest:
        _fail("SOURCE_SHA256_DRIFT:" + role)
    if mode is not None and f"{stat.S_IMODE(metadata.st_mode):04o}" != mode:
        _fail("SOURCE_MODE_DRIFT:" + role)
    if relative.is_absolute():
        _fail("SOURCE_BINDING_ABSOLUTE_PATH:" + role)
    return payload


def _verify_bindings(
    repo_root: Path,
    bindings: Sequence[tuple[Path, str, int, str, str, str | None]],
    overrides: Mapping[Path, Path],
) -> dict[Path, bytes]:
    return {
        binding[0]: _verify_binding(repo_root, binding, overrides)
        for binding in bindings
    }


def _run_formal_validator(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=path.parent,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    if result.returncode != 0:
        _fail("FROZEN_FORMAL_VALIDATOR_FAILED")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise F24IngestionSafetyError(
            "FROZEN_FORMAL_VALIDATOR_OUTPUT_INVALID"
        ) from error
    _expect(
        report,
        {
            "exact_event_count": 4,
            "exact_file_count": 2,
            "formal_human_decision_created": True,
            "formal_validator": "PASS",
            "published_runtime_validation": "PASS",
            "ready_for_training": False,
            "schema_version": FORMAL_DECISION_SCHEMA,
            "semantic_digest_verified": True,
            "status": "PASS",
        },
        "FROZEN_FORMAL_VALIDATOR_REPORT_INVALID",
    )
    return report


def _load_preparation(
    verified: Mapping[Path, bytes],
) -> dict[str, object]:
    graph_path = PREPARATION_ROOT / "f24_graph_and_role_candidates_v1.json"
    event_path = PREPARATION_ROOT / "f24_exact4_event_review_v1.csv"
    try:
        graph = json.loads(verified[graph_path])
        event_rows = list(
            csv.DictReader(io.StringIO(verified[event_path].decode("utf-8")))
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise F24IngestionSafetyError("PREPARATION_PARSE_FAILED") from error
    if type(graph) is not dict:
        _fail("PREPARATION_GRAPH_INVALID")
    atoms = graph.get("heavy_atoms")
    bonds = graph.get("heavy_bonds")
    if type(atoms) is not list or type(bonds) is not list:
        _fail("PREPARATION_GRAPH_INVENTORY_INVALID")
    atom_ids = tuple(row.get("atom_id") for row in atoms if type(row) is dict)
    normalized_bonds = tuple(
        (row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order"))
        for row in bonds
        if type(row) is dict
    )
    if (
        graph.get("schema_version") != "covapie_f24_graph_and_role_candidates_v1"
        or graph.get("review_unit_id") != EXPECTED_REVIEW_UNIT_ID
        or graph.get("ligand_component_id") != "F24"
        or graph.get("heavy_atom_count") != 23
        or graph.get("heavy_bond_count") != 22
        or len(atom_ids) != 23
        or set(atom_ids) != set(HEAVY_ATOMS)
        or len(normalized_bonds) != 22
        or graph.get("machine_selected") is not False
        or graph.get("selected_candidate") is not None
        or graph.get("machine_recommended_candidate") is not None
        or graph.get("retained_candidate_count") != 8
        or len(graph.get("candidates", [])) != 8
    ):
        _fail("PREPARATION_GRAPH_OR_MACHINE_AUTHORITY_DRIFT")
    if (
        ("C2", "C5", "SING") not in normalized_bonds
        and ("C5", "C2", "SING") not in normalized_bonds
    ):
        _fail("PREPARATION_DIRECT_BOUNDARY_MISSING")
    if len(event_rows) != 4:
        _fail("PREPARATION_EVENT_EXACT4_INVALID")
    for row, expected in zip(event_rows, EXPECTED_EVENTS):
        if (
            row.get("canonical_event_id") != expected[0]
            or row.get("scaleup_rank") != str(expected[1])
            or row.get("pdb_id") != "3V4X"
            or row.get("model_number") != "1"
            or row.get("protein_asym") != expected[2]
            or row.get("cys_residue_id") != "CYS:111-"
            or row.get("protein_reactive_atom") != "SG"
            or row.get("protein_altloc") != ""
            or row.get("ligand_component_id") != "F24"
            or row.get("ligand_asym") != expected[3]
            or row.get("ligand_reactive_atom") != "C8"
            or row.get("ligand_reactive_atom_element") != "C"
            or row.get("ligand_altloc") != ""
            or row.get("selected_connection_id") != expected[4]
            or row.get("POST_distance_angstrom") != expected[6]
            or row.get("explicit_covalent_evidence") != "true"
            or row.get("distance_only_inference_used") != "false"
            or row.get("POST_source_evidence") != "true"
        ):
            _fail("PREPARATION_EVENT_IDENTITY_OR_EVIDENCE_DRIFT")
    return {
        "atom_ids": atom_ids,
        "bonds": normalized_bonds,
        "event_rows": event_rows,
    }


def _validate_published_runtime(preparation: Mapping[str, object]) -> dict[str, object]:
    runtime = importlib.import_module(
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    )
    result = runtime.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        retained_heavy_atoms=preparation["atom_ids"],
        scaffold_atoms=SCAFFOLD_ROLE,
        linker_atoms=LINKER_ROLE,
        warhead_atoms=WARHEAD_ROLE,
        reactive_atom_id="C8",
        direct_scaffold_warhead_boundaries=(("C5", "C2", "SING"),),
        explicit_graph_bonds=preparation["bonds"],
    )
    boundary = result.direct_scaffold_warhead_boundary
    if (
        result.role_profile != EXPECTED_ROLE_PROFILE
        or result.valid is not True
        or tuple(result.reasons) != ()
        or boundary is None
        or boundary.boundary_valid is not True
        or boundary.warhead_atom_id != "C2"
        or boundary.scaffold_atom_id != "C5"
        or boundary.bond_order != "SING"
    ):
        _fail("PUBLISHED_RUNTIME_ROLE_VALIDATION_FAILED")
    return {
        "validator": "validate_role_profile_v1",
        "valid": True,
        "reasons": [],
        "role_profile": EXPECTED_ROLE_PROFILE,
        "direct_boundary_valid": True,
        "warhead_endpoint": "C2",
        "scaffold_endpoint": "C5",
        "bond_order": "SING",
    }


def _validate_formal_decision_v1(
    formal: Mapping[str, Any], preparation: Mapping[str, object]
) -> dict[str, object]:
    if type(formal) is not dict:
        _fail("FORMAL_DOCUMENT_TYPE_INVALID")
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("formal_semantic_canonical_sha256"), FORMAL_SEMANTIC_CANONICAL_SHA256, "FORMAL_SEMANTIC_DIGEST_LITERAL_DRIFT")
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")
    for key, expected in (
        ("approved", True),
        ("unsigned", False),
        ("decision_finalized", True),
        ("human_review_completed", True),
        ("formal_authority_created", True),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    approval = formal.get("human_approval")
    if type(approval) is not dict:
        _fail("FORMAL_APPROVAL_MISSING")
    expected_approval = {
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "D4_role_partition": "REVISE_ROLE_PARTITION",
        "D5_training_use": "INCLUDE",
        "D6_scientific_context": EXPECTED_D6,
        "approval_recorded": True,
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "attestor_id": "fmx",
        "current_authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
        "human_choices_externally_authorized": True,
        "human_selected_role_candidate_index_0based": None,
        "machine_auto_selection_performed": False,
        "machine_recommended_candidate": None,
        "reviewer_id": "fmx",
    }
    _expect(approval, expected_approval, "FORMAL_D1_D6_OR_APPROVAL_DRIFT")
    _parse_utc(approval["approved_at_utc"])
    context = formal.get("human_approved_context")
    _expect(
        context,
        {"D6_scientific_context": EXPECTED_D6, "exact_text_frozen": True},
        "FORMAL_D6_CONTEXT_DRIFT",
    )

    identity = formal.get("identity")
    if type(identity) is not dict:
        _fail("FORMAL_IDENTITY_MISSING")
    _expect(identity.get("review_unit_id"), EXPECTED_REVIEW_UNIT_ID, "FORMAL_REVIEW_UNIT_DRIFT")
    _expect(identity.get("canonical_event_ids"), list(EXPECTED_EVENT_IDS), "FORMAL_EVENT_IDS_DRIFT")
    _expect(identity.get("scaleup_ranks"), list(EXPECTED_RANKS), "FORMAL_RANKS_DRIFT")
    for key, expected in (
        ("exact_event_count", 4),
        ("unique_event_count", 4),
        ("duplicate_event_count", 0),
        ("omitted_event_count", 0),
        ("extra_event_count", 0),
        ("event_contexts_collapsed", False),
        ("ligand_component_id", "F24"),
        ("pdb_ids", ["3V4X"]),
        ("pdb_event_counts", {"3V4X": 4}),
    ):
        _expect(identity.get(key), expected, "FORMAL_IDENTITY_DRIFT:" + key)

    events = formal.get("event_level_human_decisions")
    if type(events) is not list or len(events) != 4:
        _fail("FORMAL_EVENT_EXACT4_INVALID")
    for event, expected in zip(events, EXPECTED_EVENTS):
        required = {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_partition": "REVISE_ROLE_PARTITION",
            "D5_training_use": "INCLUDE",
            "D6_context_reference": "UNIT_LEVEL_EXACT_FROZEN_D6",
            "POST_distance_angstrom": expected[5],
            "canonical_event_id": expected[0],
            "chemistry_human_authoritative": True,
            "context_or_site_specific_exception": False,
            "event_specific_exception": False,
            "formal_training_admitted": False,
            "ligand_asym": expected[3],
            "ligand_component_id": "F24",
            "ligand_reactive_atom": "C8",
            "pdb_id": "3V4X",
            "protein_asym": expected[2],
            "protein_reactive_atom": "SG",
            "protein_residue": "CYS:111-",
            "reactive_pair_human_authoritative": True,
            "role_partition_human_authoritative": True,
            "scaleup_rank": expected[1],
            "selected_connection_id": expected[4],
            "task_relevance_human_authoritative": True,
            "tensor_target_created": False,
            "training_use_human_authoritative": True,
        }
        _expect(event, required, "FORMAL_EVENT_DECISION_OR_IDENTITY_DRIFT")

    role = formal.get("selected_role_partition")
    if type(role) is not dict:
        _fail("FORMAL_SELECTED_ROLE_MISSING")
    role_required = {
        "D4_human_choice": "REVISE_ROLE_PARTITION",
        "all_heavy_atoms_exactly_once": True,
        "coverage_count": 23,
        "direct_scaffold_warhead_boundary": {
            "bond_order": "SING",
            "boundary_valid": True,
            "scaffold_atom_id": "C5",
            "warhead_atom_id": "C2",
        },
        "heavy_atom_count": 23,
        "heavy_atom_exhaustive": True,
        "human_selected": True,
        "human_selected_machine_candidate_index_0based": None,
        "linker_atom_count": 0,
        "linker_atom_ids": [],
        "linker_empty": True,
        "machine_auto_selection_performed": False,
        "machine_candidate_selected": False,
        "machine_recommended": False,
        "machine_selected": False,
        "partition_disjoint": True,
        "role_partition_source": "EXTERNAL_HUMAN_REVISED_ROLE_PARTITION",
        "role_profile": EXPECTED_ROLE_PROFILE,
        "scaffold_atom_count": 16,
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "scaffold_connected": True,
        "selected_candidate_index_0based": None,
        "warhead_atom_count": 7,
        "warhead_connected": True,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
    }
    for key, expected in role_required.items():
        _expect(role.get(key), expected, "FORMAL_REVISED_ROLE_DRIFT:" + key)
    published_runtime = role.get("published_runtime_validation")
    _expect(
        published_runtime,
        {
            "bond_order": "SING",
            "direct_boundary_valid": True,
            "reasons": [],
            "role_profile": EXPECTED_ROLE_PROFILE,
            "scaffold_endpoint": "C5",
            "valid": True,
            "validator": "validate_role_profile_v1",
            "warhead_endpoint": "C2",
        },
        "FORMAL_PUBLISHED_RUNTIME_RESULT_DRIFT",
    )

    chemical = formal.get("chemical_warhead_annotation")
    if type(chemical) is not dict:
        _fail("FORMAL_CHEMICAL_WARHEAD_MISSING")
    for key, expected in (
        ("authority_scope", CHEMICAL_SCOPE),
        ("chemical_warhead_atom_ids", list(CHEMICAL_WARHEAD)),
        ("human_authoritative", True),
        ("electrophilic_carbonyl_carbon", "C8"),
        ("beta_lactone_carbonyl_oxygen", "O2"),
        ("observed_POST_attachment_atom", "C8"),
        ("PRE_coordinates", None),
        ("PRE_reconstruction_performed", False),
        ("PRE_coordinate_reconstruction_performed", False),
        ("PRE_topology_authority_created", False),
        ("PRE_geometry_authority_created", False),
        ("PRE_zero_fill_performed", False),
        ("POST_to_PRE_copy_performed", False),
    ):
        _expect(chemical.get(key), expected, "FORMAL_CHEMICAL_WARHEAD_DRIFT:" + key)
    distinction = formal.get("chemical_warhead_vs_role_region_distinction")
    if type(distinction) is not dict:
        _fail("FORMAL_CHEMICAL_ROLE_DISTINCTION_MISSING")
    _expect(distinction.get("chemical_warhead_atom_ids"), list(CHEMICAL_WARHEAD), "FORMAL_CHEMICAL_CORE_DRIFT")
    _expect(distinction.get("warhead_role_atom_ids"), list(WARHEAD_ROLE), "FORMAL_WARHEAD_ROLE_DRIFT")
    _expect(distinction.get("sets_are_intentionally_distinct"), True, "FORMAL_CHEMICAL_ROLE_DISTINCTION_LOST")
    _expect(distinction.get("C4_O5_asserted_as_beta_lactone_ring_atoms"), False, "FORMAL_C4_O5_RING_ASSERTION_DRIFT")
    _expect(distinction.get("C4_O5_asserted_as_chemical_warhead_core_atoms"), False, "FORMAL_C4_O5_CORE_ASSERTION_DRIFT")
    proximal = distinction.get("proximal_hydroxymethyl_substituent")
    if type(proximal) is not dict:
        _fail("FORMAL_C4_O5_SEMANTICS_MISSING")
    for key, expected in (
        ("atom_ids", ["C4", "O5"]),
        ("chemical_beta_lactone_core_member", False),
        ("absorbed_into_warhead_role_region", True),
    ):
        _expect(proximal.get(key), expected, "FORMAL_C4_O5_SEMANTICS_DRIFT:" + key)
    if set(CHEMICAL_WARHEAD) == set(WARHEAD_ROLE):
        _fail("INTERNAL_CHEMICAL_ROLE_SETS_FLATTENED")
    if "C4" in CHEMICAL_WARHEAD or "O5" in CHEMICAL_WARHEAD:
        _fail("INTERNAL_C4_O5_CHEMICAL_CORE_CONTAMINATION")

    canonical = formal.get("canonical_Exact5_and_sample_applicability")
    if type(canonical) is not dict:
        _fail("FORMAL_CANONICAL_TASK_CONTRACT_MISSING")
    expected_tasks = [
        {
            "display_alias": alias,
            "semantic_name": semantic,
            "structurally_applicable_to_F24": task_id in DIRECT_VALID_TASK_IDS,
            "task_id": task_id,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    for key, expected in (
        ("global_canonical_task_count", 5),
        ("B3_present", True),
        ("sixth_task_present", False),
        ("canonical_vocabulary_changed", False),
        ("D5_INCLUDE_does_not_change_structural_applicability", True),
        ("sample_applicable_task_ids", [0, 3, 4]),
        ("sample_applicable_semantic_names", ["warhead_only", "scaffold_only", "scaffold_plus_linker_plus_warhead"]),
        ("tasks", expected_tasks),
    ):
        _expect(canonical.get(key), expected, "FORMAL_CANONICAL_TASK_DRIFT:" + key)

    machine = formal.get("machine_candidate_history")
    if type(machine) is not dict:
        _fail("FORMAL_MACHINE_HISTORY_MISSING")
    for key, expected in (
        ("human_revision_used", True),
        ("human_selected_machine_candidate", False),
        ("machine_candidate_count", 8),
        ("machine_candidate_indices_0based", list(range(8))),
        ("machine_candidate_inventory_modified", False),
        ("revised_role_declared_as_candidate_8", False),
    ):
        _expect(machine.get(key), expected, "FORMAL_MACHINE_HISTORY_DRIFT:" + key)

    minimal = formal.get("minimal_seed")
    _expect(
        minimal,
        {
            "D4_role_acceptance_creates_minimal_seed": False,
            "minimal_seed_atom_ids": None,
            "minimal_seed_authority_created": False,
            "minimal_seed_status": "UNRESOLVED_NOT_CREATED",
            "task_C_requires_future_independent_seed_tensor_gate": True,
        },
        "FORMAL_MINIMAL_SEED_DRIFT",
    )
    training = formal.get("training_use_human_decision")
    _expect(
        training,
        {
            "D5_human_choice": "INCLUDE",
            "READY_FOR_TRAINING": False,
            "authority_scope": "F24_EXACT4_SAMPLE_LEVEL_HUMAN_DISPOSITION_ONLY",
            "formal_split_authority_created": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": None,
            "future_training_admission_candidate_status": "DEFERRED_TO_DOWNSTREAM_INGESTION_AND_CENSUS",
            "human_training_excluded": False,
            "parameter_update_authorization": False,
            "runtime_model_usable": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed_now": False,
            "training_use_allowed": True,
            "training_use_include": True,
        },
        "FORMAL_TRAINING_USE_OR_ADMISSION_DRIFT",
    )
    geometry = formal.get("geometry_boundary")
    _expect(
        geometry,
        {
            "POST_geometry_training_authority_created": False,
            "POST_geometry_training_target_created": False,
            "POST_source_event_count": 4,
            "POST_source_evidence_available": True,
            "POST_to_PRE_copy_performed": False,
            "PRE_coordinate_reconstruction_performed": False,
            "PRE_coordinates": None,
            "PRE_geometry_authority_created": False,
            "PRE_reconstruction_performed": False,
            "PRE_topology_authority_created": False,
            "PRE_zero_fill_performed": False,
        },
        "FORMAL_GEOMETRY_BOUNDARY_DRIFT",
    )
    reusable = formal.get("reusable_authority_boundary")
    if type(reusable) is not dict:
        _fail("FORMAL_REUSABLE_BOUNDARY_MISSING")
    for key in (
        "cross_sample_rule_created",
        "generic_CYS_beta_lactone_rule_created",
        "reaction_family_authority_created",
        "reusable_chemistry_authority_created",
        "reusable_pair_authority_created",
        "reusable_role_authority_created",
        "warhead_rule_authority_created",
        "warhead_type_authority_created",
    ):
        _expect(reusable.get(key), False, "FORMAL_REUSABLE_AUTHORITY_DRIFT:" + key)
    downstream = formal.get("downstream_status")
    if type(downstream) is not dict or any(value != "NOT_DONE" for value in downstream.values()):
        _fail("FORMAL_DOWNSTREAM_STATUS_DRIFT")
    warning = formal.get("training_prerequisite_warning")
    if type(warning) is not dict:
        _fail("FORMAL_TRAINING_WARNING_MISSING")
    _expect(warning.get("feature_semantics_status"), "AUDIT_REQUIRED_LATER", "FORMAL_FEATURE_SEMANTICS_WARNING_DRIFT")
    _expect(warning.get("Step12D"), "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT", "FORMAL_STEP12D_WARNING_DRIFT")
    for key in (
        "auxiliary_head_executed", "backward_performed", "batch_modified",
        "fine_tune_performed", "loader_modified", "loss_executed",
        "model_forward_performed", "optimizer_created", "optimizer_step_performed",
        "parameter_update_performed", "training_performed",
    ):
        _expect(warning.get(key), False, "FORMAL_TRAINING_ACTION_DRIFT:" + key)
    return _validate_published_runtime(preparation)


def _current_census_boundary(
    repo_root: Path,
    verified: Mapping[Path, bytes],
) -> dict[str, object]:
    del repo_root
    csv_path = CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1.csv"
    summary_path = CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_ozj_v1.json"
    try:
        rows = list(csv.DictReader(io.StringIO(verified[csv_path].decode("utf-8"))))
        summary = json.loads(verified[summary_path])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise F24IngestionSafetyError("CURRENT_CENSUS_PARSE_FAILED") from error
    f24_rows = [row for row in rows if row.get("ligand_component_id") == "F24"]
    if (
        len(rows) != 1000
        or len(f24_rows) != 4
        or tuple(row.get("canonical_event_id") for row in f24_rows) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in f24_rows) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_F24_EXACT4_DRIFT")
    expected_cells = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    for row in f24_rows:
        if any(row.get(key) != value for key, value in expected_cells.items()):
            _fail("CURRENT_CENSUS_F24_PRIOR_STATE_DRIFT")
    expected_counts = {
        "positive": summary.get("chemistry", {}).get("POSITIVE", {}).get("count"),
        "relevant": summary.get("task_relevance", {}).get("RELEVANT", {}).get("count"),
        "training_INCLUDE": summary.get("training_use", {}).get("INCLUDE", {}).get("count"),
        "training_EXCLUDE": summary.get("training_use", {}).get("EXCLUDE_FROM_TRAINING_ONLY", {}).get("count"),
        "future_candidates": summary.get("training_stage", {}).get("future_training_admission_candidate_count"),
        "pair_sample_authority": summary.get("reactive_pair", {}).get("sample_level_authoritative_pair_count"),
        "role_sample_authority": summary.get("role", {}).get("role_partition_sample_authoritative_count"),
    }
    _expect(
        expected_counts,
        {
            "positive": 104,
            "relevant": 105,
            "training_INCLUDE": 40,
            "training_EXCLUDE": 64,
            "future_candidates": 23,
            "pair_sample_authority": 104,
            "role_sample_authority": 104,
        },
        "CURRENT_CENSUS_COUNTS_DRIFT",
    )
    authority = summary.get("authority_boundary", {})
    _expect(authority.get("next_priority_review_ligand"), "F24", "CURRENT_CENSUS_PRIORITY_HEAD_DRIFT")
    _expect(authority.get("next_priority_review_unit"), EXPECTED_REVIEW_UNIT_ID, "CURRENT_CENSUS_PRIORITY_UNIT_DRIFT")
    _expect(authority.get("next_priority_review_event_count"), 4, "CURRENT_CENSUS_PRIORITY_COUNT_DRIFT")
    return {
        **expected_counts,
        "current_F24_status": "CURRENTLY_UNREVIEWED",
        "next_priority_review_ligand": "F24",
        "next_priority_review_unit": EXPECTED_REVIEW_UNIT_ID,
        "next_priority_review_event_count": 4,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
        "priority_queue_updated": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
    execute_formal_validator: bool = True,
) -> dict[str, object]:
    """Bind and independently validate the frozen authority and all owners."""

    repo_root = Path(repo_root).resolve()
    overrides = dict(repository_path_overrides or {})
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    formal_payloads = _verify_bindings(repo_root, FORMAL_BINDINGS, overrides)
    preparation_payloads = _verify_bindings(repo_root, PREPARATION_BINDINGS, overrides)
    _verify_bindings(repo_root, SEMANTIC_OWNER_BINDINGS, overrides)
    _verify_bindings(repo_root, PRECEDENT_BINDINGS, overrides)
    census_payloads = _verify_bindings(repo_root, CENSUS_BINDINGS, overrides)
    try:
        formal = json.loads(formal_payloads[FORMAL_DECISION_RELATIVE])
    except json.JSONDecodeError as error:
        raise F24IngestionSafetyError("FORMAL_JSON_PARSE_FAILED") from error
    preparation = _load_preparation(preparation_payloads)
    runtime_result = _validate_formal_decision_v1(formal, preparation)
    validator_path = _resolve_binding_path(repo_root, FORMAL_BINDINGS[1], overrides)
    validator_result = (
        _run_formal_validator(validator_path)
        if execute_formal_validator
        else {
            "formal_validator": "PASS",
            "published_runtime_validation": "PASS",
            "semantic_digest_verified": True,
            "status": "PASS",
        }
    )
    census_boundary = _current_census_boundary(repo_root, census_payloads)
    return {
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "preparation_exact6_bindings": _expected_binding_records(PREPARATION_BINDINGS),
        "immutable_semantic_owner_bindings": _expected_binding_records(SEMANTIC_OWNER_BINDINGS),
        "precedent_bindings": _expected_binding_records(PRECEDENT_BINDINGS),
        "current_published_census_bindings": _expected_binding_records(CENSUS_BINDINGS),
        "formal_validator_result": validator_result,
        "published_runtime_result": runtime_result,
        "current_published_census_boundary": census_boundary,
        "formal": formal,
        "preparation": preparation,
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": task_id in DIRECT_VALID_TASK_IDS,
            "role_profile": EXPECTED_ROLE_PROFILE,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    return {
        "global_canonical_tasks": [
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "generated_roles": list(generated),
                "fixed_or_seed_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "canonical_vocabulary_changed": False,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "direct_profile_applicable_task_count": 3,
        "task_applicability": applicability,
        "D5_INCLUDE_does_not_change_structural_applicability": True,
    }


def _role_projection() -> dict[str, object]:
    return {
        "D4_human_choice": "REVISE_ROLE_PARTITION",
        "role_partition_human_choice": "REVISE_ROLE_PARTITION",
        "selected_candidate_index_0based": None,
        "human_selected_machine_candidate_index_0based": None,
        "role_partition_source": "EXTERNAL_HUMAN_REVISED_ROLE_PARTITION",
        "machine_candidate_selected": False,
        "machine_selected": False,
        "machine_recommended": False,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "linker_atom_ids": [],
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "boundary_bonds": [
            {
                "atom_id_1": "C5",
                "atom_id_2": "C2",
                "bond_order": "SING",
                "boundary_between_roles": ["scaffold", "warhead"],
            }
        ],
        "chemical_warhead_atom_ids": list(CHEMICAL_WARHEAD),
        "chemical_warhead_human_authoritative": True,
        "chemical_warhead_scope": CHEMICAL_SCOPE,
        "chemical_warhead_differs_from_role_region": True,
        "sets_are_intentionally_distinct": True,
        "C4_O5_chemical_beta_lactone_core_member": False,
        "C4_O5_absorbed_into_warhead_role_region": True,
        "minimal_seed_status": "UNRESOLVED_NOT_CREATED",
        "minimal_seed_authority_available": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "formal_event_training_use_decision": "INCLUDE",
        "event_training_use_human_decision_available": True,
        "training_use_allowed": True,
        "human_training_excluded": False,
        "training_use_include": True,
        "formal_future_training_admission_candidate": None,
        "candidate_for_future_training_admission": True,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "ready_for_training": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_created": False,
        "POST_geometry_training_target_available_now": False,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "PRE_geometry_training_label_available_now": False,
        "PRE_reconstruction_performed": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
    }


def _reusable_boundary() -> dict[str, object]:
    return {
        "reaction_family_target_available": False,
        "warhead_rule_target_available": False,
        "warhead_type_target_available": False,
        "reusable_chemistry_authority_available": False,
        "reusable_pair_authority_available": False,
        "reusable_role_authority_available": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "snapshot_created_by_ingestion": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "new_human_authority_created": False,
        "formal_human_decision_modified": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "minimal_seed_authority_created": False,
        "PRE_topology_authority_created": False,
        "PRE_geometry_authority_created": False,
        "POST_geometry_training_authority_created": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
        "priority_queue_updated": False,
        "training_admission_created": False,
        "training_admitted": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "ready_for_training": False,
        "F24_reconciliation_started": False,
        "F24_global_census_refresh_started": False,
        "F24_priority_queue_refresh_started": False,
        "F24_training_admission_started": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "Step12D": "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "commit_performed": False,
        "push_performed": False,
    }


def _event_projection(expected: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": expected[0],
        "scaleup_rank": expected[1],
        "pdb_id": "3V4X",
        "model_number": 1,
        "protein_chain_or_asym": expected[2],
        "cys_residue_id": "CYS:111-",
        "protein_altloc": None,
        "ligand_component_id": "F24",
        "ligand_chain_or_asym": expected[3],
        "ligand_altloc": None,
        "selected_connection_id": expected[4],
        "POST_distance_angstrom": expected[5],
        "POST_distance_frozen_lexeme": expected[6],
        "human_task_relevance_decision": "RELEVANT",
        "chemistry_known_positive": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C8",
        "ligand_reactive_atom_element": "C",
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "chemical_warhead_human_authoritative": True,
        **_training_boundary(),
        **_geometry_boundary(),
        **_reusable_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "IMMUTABLE_F24_HUMAN_AUTHORITY_INGESTION_SNAPSHOT",
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "preparation_exact6_bindings": bound["preparation_exact6_bindings"],
        "immutable_semantic_owner_bindings": bound["immutable_semantic_owner_bindings"],
        "formal_validator_result": bound["formal_validator_result"],
        "published_runtime_validation": bound["published_runtime_result"],
        "human_approval": {
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
            "authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
            "approved": True,
            "unsigned": False,
            "decision_finalized": True,
            "human_review_completed": True,
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_partition": "REVISE_ROLE_PARTITION",
            "D5_training_use": "INCLUDE",
            "D6_scientific_context": EXPECTED_D6,
        },
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "role_partition": _role_projection(),
        "canonical_task_contract": _canonical_task_contract(),
        "training_boundary": _training_boundary(),
        "geometry_boundary": _geometry_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "current_published_census_boundary": bound["current_published_census_boundary"],
        "authority_boundary": _authority_boundary(),
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "ligand_reactive_atom_element",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile",
    "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
    "boundary_bonds_json", "global_canonical_task_count",
    "canonical_task_applicability_json", "direct_profile_applicable_task_ids_json",
    "formal_event_training_use_decision", "event_training_use_human_decision_available",
    "training_use_allowed", "human_training_excluded",
    "candidate_for_future_training_admission", "future_training_admission_status",
    "training_admitted", "training_materialization_allowed_now",
    "current_runtime_model_usable", "role_partition_human_choice",
    "chemical_warhead_human_authoritative", "chemical_warhead_atoms_json",
    "chemical_warhead_scope", "chemical_warhead_differs_from_role_region",
    "minimal_seed_authority_available",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    role = _role_projection()
    applicability = _canonical_task_contract()["task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": str(event["scaleup_rank"]),
                "pdb_id": "3V4X",
                "model_number": "1",
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": "CYS:111-",
                "protein_altloc": "",
                "ligand_component_id": "F24",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "",
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "human_task_relevance_decision": "RELEVANT",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "C8",
                "ligand_reactive_atom_element": "C",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(WARHEAD_ROLE)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ROLE)),
                "boundary_bonds_json": _json_cell(role["boundary_bonds"]),
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": _json_cell(applicability),
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "formal_event_training_use_decision": "INCLUDE",
                "event_training_use_human_decision_available": "true",
                "training_use_allowed": "true",
                "human_training_excluded": "false",
                "candidate_for_future_training_admission": "true",
                "future_training_admission_status": FUTURE_STATUS,
                "training_admitted": "false",
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "role_partition_human_choice": "REVISE_ROLE_PARTITION",
                "chemical_warhead_human_authoritative": "true",
                "chemical_warhead_atoms_json": _json_cell(list(CHEMICAL_WARHEAD)),
                "chemical_warhead_scope": CHEMICAL_SCOPE,
                "chemical_warhead_differs_from_role_region": "true",
                "minimal_seed_authority_available": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "event_count": 4,
        "completed_human_positive_count": 4,
        "chemistry_positive_count": 4,
        "task_relevant_count": 4,
        "reactive_pair_human_authority_count": 4,
        "role_partition_human_authority_count": 4,
        "chemical_warhead_human_authority_count": 4,
        "human_training_INCLUDE_count": 4,
        "human_training_EXCLUDE_count": 0,
        "direct_profile_count": 4,
        "strict_profile_count": 0,
        "future_training_admission_candidate_count": 4,
        "future_training_candidate_derived_by_ingestion_count": 4,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "minimal_seed_authority_count": 0,
        "PRE_topology_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "new_human_authority_created": False,
        "candidate_for_future_training_admission": True,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "published_global_positive_count_remains": 104,
        "published_task_relevant_count_remains": 105,
        "published_training_INCLUDE_count_remains": 40,
        "published_training_EXCLUDE_count_remains": 64,
        "published_future_training_candidate_count_remains": 23,
        "published_pair_sample_authority_count_remains": 104,
        "published_role_sample_authority_count_remains": 104,
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "priority_queue_update_status": "NOT_DONE_THIS_STEP",
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "Step12D": "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "ready_for_F24_reconciliation_successor": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise F24IngestionSafetyError("UTF8_INVALID:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _reject_dynamic_metadata(value: object, path: str = "root") -> None:
    forbidden_keys = {
        "generated_at", "created_at", "timestamp", "hostname", "host",
        "pid", "uuid", "cwd", "temporary_directory", "temporary_path",
        "output_path", "live_git_status", "git_head", "git_tree",
    }
    if type(value) is dict:
        for key, child in value.items():
            lowered = key.lower()
            if lowered in forbidden_keys or (
                "timestamp" in lowered and key != "approved_at_utc"
            ):
                _fail("DYNAMIC_METADATA_KEY:" + path + "." + key)
            _reject_dynamic_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_metadata(child, f"{path}[{index}]")
    elif type(value) is str and (
        value.startswith("/cpfs")
        or value.startswith("/home/")
        or value.startswith("/tmp/")
        or value.startswith("file://")
    ):
        _fail("ABSOLUTE_OR_MACHINE_PATH:" + path)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, role in (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    ):
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        _validate_text_payload(relative.as_posix(), payload)
        rows.append(
            {
                "path": relative.as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "sha256_scope": "file_bytes",
                "source_role": role,
            }
        )
    return rows


def _validate_candidate_bindings(value: object) -> None:
    if type(value) is not list or len(value) != 3:
        _fail("CANDIDATE_SOURCE_BINDINGS_INVALID")
    expected_paths = [
        SOURCE_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
    ]
    if [row.get("path") for row in value if type(row) is dict] != expected_paths:
        _fail("CANDIDATE_SOURCE_BINDING_PATHS_INVALID")
    for row in value:
        if (
            type(row) is not dict
            or row.get("path_namespace") != "repository_relative"
            or type(row.get("byte_count")) is not int
            or row["byte_count"] <= 0
            or type(row.get("sha256")) is not str
            or len(row["sha256"]) != 64
            or row.get("sha256_scope") != "file_bytes"
        ):
            _fail("CANDIDATE_SOURCE_BINDING_SHAPE_INVALID")


def _standalone_bound() -> dict[str, object]:
    return {
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "preparation_exact6_bindings": _expected_binding_records(PREPARATION_BINDINGS),
        "immutable_semantic_owner_bindings": _expected_binding_records(SEMANTIC_OWNER_BINDINGS),
        "precedent_bindings": _expected_binding_records(PRECEDENT_BINDINGS),
        "current_published_census_bindings": _expected_binding_records(CENSUS_BINDINGS),
        "formal_validator_result": {
            "exact_event_count": 4,
            "exact_file_count": 2,
            "formal_human_decision_created": True,
            "formal_validator": "PASS",
            "published_runtime_validation": "PASS",
            "ready_for_training": False,
            "schema_version": FORMAL_DECISION_SCHEMA,
            "semantic_digest_verified": True,
            "status": "PASS",
        },
        "published_runtime_result": {
            "validator": "validate_role_profile_v1",
            "valid": True,
            "reasons": [],
            "role_profile": EXPECTED_ROLE_PROFILE,
            "direct_boundary_valid": True,
            "warhead_endpoint": "C2",
            "scaffold_endpoint": "C5",
            "bond_order": "SING",
        },
        "current_published_census_boundary": {
            "positive": 104,
            "relevant": 105,
            "training_INCLUDE": 40,
            "training_EXCLUDE": 64,
            "future_candidates": 23,
            "pair_sample_authority": 104,
            "role_sample_authority": 104,
            "current_F24_status": "CURRENTLY_UNREVIEWED",
            "next_priority_review_ligand": "F24",
            "next_priority_review_unit": EXPECTED_REVIEW_UNIT_ID,
            "next_priority_review_event_count": 4,
            "global_reconciliation_updated": False,
            "global_census_updated": False,
            "priority_queue_updated": False,
        },
    }


def _manifest(
    bound: Mapping[str, object],
    candidate_bindings: list[dict[str, object]],
    snapshot_payload: bytes,
    matrix_payload: bytes,
    summary_payload: bytes,
) -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "F24_COMPLETED_DECISION_INGESTION_NOT_RECONCILIATION_OR_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "preparation_exact6_bindings": bound["preparation_exact6_bindings"],
        "immutable_semantic_owner_bindings": bound["immutable_semantic_owner_bindings"],
        "precedent_bindings": bound["precedent_bindings"],
        "current_published_census_bindings": bound["current_published_census_bindings"],
        "current_published_census_boundary": bound["current_published_census_boundary"],
        "candidate_source_bindings": candidate_bindings,
        "canonical_task_contract": _canonical_task_contract(),
        "counts": {
            key: value
            for key, value in _summary().items()
            if type(value) is int and type(value) is not bool
        },
        "chemical_warhead_vs_role_region": {
            "chemical_warhead_atom_ids": list(CHEMICAL_WARHEAD),
            "warhead_role_atom_ids": list(WARHEAD_ROLE),
            "sets_are_intentionally_distinct": True,
            "legacy_matrix_warhead_atoms_json_semantics": "CANONICAL_ROLE_PARTITION_WARHEAD_REGION",
            "chemical_warhead_atoms_json_semantics": "F24_SAMPLE_LEVEL_CHEMICAL_BETA_LACTONE_CORE",
        },
        "human_authority_ingestion_semantics": {
            "human_authority_ingested": True,
            "human_authority_created_by_ingestion": False,
            "new_human_authority_created": False,
            "D4_human_choice": "REVISE_ROLE_PARTITION",
            "selected_machine_candidate": None,
            "D5_human_choice": "INCLUDE",
            "formal_future_training_admission_candidate": None,
            "candidate_for_future_training_admission": True,
            "future_training_candidate_derived_by_ingestion": True,
            "future_training_candidate_is_training_admission": False,
            "training_admitted": False,
        },
        "output_artifact_bindings": {
            SNAPSHOT: {"sha256": _sha(snapshot_payload)},
            MATRIX: {"sha256": _sha(matrix_payload)},
            SUMMARY: {"sha256": _sha(summary_payload)},
        },
        "manifest_self_sha256_recorded": False,
        "manifest_self_sha256_policy": "SELF_SHA256_PROHIBITED",
        "deterministic": True,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "priority_queue_update_status": "NOT_DONE_THIS_STEP",
        "expected_future_census_derivation_materialized": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "step12d_is_only_smoke_legality_not_final_training_feature_contract": True,
        "ready_for_F24_reconciliation_successor": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }


def _build_artifacts_unvalidated(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
    execute_formal_validator: bool = True,
) -> dict[str, bytes]:
    repo_root = Path(repo_root).resolve()
    bound = load_frozen_formal_decision_v1(
        repo_root,
        formal_decision_path=formal_decision_path,
        formal_validator_path=formal_validator_path,
        repository_path_overrides=repository_path_overrides,
        execute_formal_validator=execute_formal_validator,
    )
    snapshot = _snapshot(bound)
    snapshot_payload = _json_bytes(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_payload = _json_bytes(_summary())
    manifest_payload = _json_bytes(
        _manifest(
            bound,
            _candidate_source_bindings(repo_root),
            snapshot_payload,
            matrix_payload,
            summary_payload,
        )
    )
    return {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        SUMMARY: summary_payload,
        MANIFEST: manifest_payload,
    }


def _validate_derived_projection_digests(artifacts: Mapping[str, bytes]) -> None:
    expected = {
        SNAPSHOT: _EXPECTED_SNAPSHOT_SHA256_V1,
        MATRIX: _EXPECTED_MATRIX_SHA256_V1,
        SUMMARY: _EXPECTED_SUMMARY_SHA256_V1,
    }
    for name, digest in expected.items():
        if (
            type(digest) is not str
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or digest == "0" * 64
        ):
            _fail("DERIVED_PROJECTION_CONTRACT_DIGEST_NOT_FROZEN:" + name)
        if _sha(artifacts[name]) != digest:
            _fail("DERIVED_PROJECTION_SHA256_INVALID:" + name)


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate the Exact4 projection and fail closed on coordinated drift."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        matrix = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
        summary = json.loads(artifacts[SUMMARY])
        manifest = json.loads(artifacts[MANIFEST])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise F24IngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_metadata(document)
    standalone = _standalone_bound()
    _expect(snapshot, _snapshot(standalone), "SNAPSHOT_EXACT_SOURCE_PROJECTION_INVALID")
    _expect(summary, _summary(), "SUMMARY_EXACT_COUNTS_OR_BOUNDARY_INVALID")
    if (list(matrix[0]) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    expected_matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    if artifacts[MATRIX] != expected_matrix_payload:
        _fail("MATRIX_EXACT_ROLE_CHEMICAL_OR_TASK_PROJECTION_INVALID")
    if (
        len(matrix) != 4
        or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS
        or len({row["canonical_event_id"] for row in matrix}) != 4
        or tuple(int(row["scaleup_rank"]) for row in matrix) != EXPECTED_RANKS
    ):
        _fail("MATRIX_EXACT4_INVALID")
    for index, row in enumerate(matrix):
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["selected_role_candidate_index_0based"] != ""
            or row["role_partition_human_choice"] != "REVISE_ROLE_PARTITION"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != list(WARHEAD_ROLE)
            or json.loads(row["chemical_warhead_atoms_json"]) != list(CHEMICAL_WARHEAD)
            or json.loads(row["linker_atoms_json"]) != []
            or json.loads(row["scaffold_atoms_json"]) != list(SCAFFOLD_ROLE)
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [item["task_id"] for item in applicability if item["structurally_applicable"]] != [0, 3, 4]
            or row["chemical_warhead_differs_from_role_region"] != "true"
            or row["minimal_seed_authority_available"] != "false"
            or row["POST_distance_angstrom"] != EXPECTED_EVENTS[index][6]
        ):
            _fail("MATRIX_CHEMICAL_ROLE_DIRECT_OR_SEED_SEMANTICS_INVALID")
    candidate_bindings = manifest.get("candidate_source_bindings") if type(manifest) is dict else None
    _validate_candidate_bindings(candidate_bindings)
    expected_manifest = _manifest(
        standalone,
        candidate_bindings,
        artifacts[SNAPSHOT],
        artifacts[MATRIX],
        artifacts[SUMMARY],
    )
    _expect(manifest, expected_manifest, "MANIFEST_CLOSURE_INVALID")
    _validate_derived_projection_digests(artifacts)
    if repo_root is not None:
        repo_root = Path(repo_root).resolve()
        bound = load_frozen_formal_decision_v1(repo_root)
        _expect(snapshot, _snapshot(bound), "SNAPSHOT_DIRECT_FORMAL_SOURCE_PROJECTION_INVALID")
        _expect(candidate_bindings, _candidate_source_bindings(repo_root), "MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build and validate the deterministic Exact4 metadata projection."""

    artifacts = _build_artifacts_unvalidated(
        repo_root,
        formal_decision_path=formal_decision_path,
        formal_validator_path=formal_validator_path,
        repository_path_overrides=repository_path_overrides,
    )
    validate_completed_decision_projection_v1(artifacts, repo_root=repo_root)
    return artifacts


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(
    repo_root: Path, *, output_root: Path | None = None
) -> dict[str, bytes]:
    """Materialize only the four authorized deterministic metadata outputs."""

    repo_root = Path(repo_root).resolve()
    artifacts = build_artifacts_v1(repo_root)
    target_root = output_root or (repo_root / OUTPUT_ROOT_RELATIVE)
    target_root = Path(target_root)
    for name, payload in artifacts.items():
        _atomic_write(target_root / name, payload)
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Check live outputs against a fresh source-derived projection."""

    repo_root = Path(repo_root).resolve()
    expected = build_artifacts_v1(repo_root)
    actual: dict[str, bytes] = {}
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir() or output_root.is_symlink():
        _fail("OUTPUT_ROOT_NOT_REGULAR_DIRECTORY")
    if tuple(sorted(path.name for path in output_root.iterdir())) != tuple(sorted(OUTPUT_FILENAMES)):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4")
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        if not path.is_file() or path.is_symlink():
            _fail("OUTPUT_NOT_REGULAR:" + name)
        actual[name] = path.read_bytes()
    validate_completed_decision_projection_v1(actual, repo_root=repo_root)
    if actual != expected:
        _fail("MATERIALIZED_OUTPUT_BYTES_DRIFT")
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "deterministic": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
        "ready_for_training": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize_artifacts_v1(repo_root)
    print(json.dumps(check_materialized_v1(repo_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
