"""Build the additive batch-001 completed-decision successor snapshot V1.

This module is metadata-only.  It binds the frozen external batch workspace,
copies exactly the nine completed human decisions, and describes event-level
label availability.  It does not mutate the predecessor human overlay, create
chemistry authority, tensorize samples, or execute training.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any


SCHEMA_VERSION = (
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_batch001_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_batch001_event_task_label_availability_v1"
MANIFEST_SCHEMA_VERSION = "covapie_batch001_task_label_availability_manifest_v1"
SUMMARY_SCHEMA_VERSION = "covapie_batch001_task_label_availability_summary_v1"

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_batch001_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_batch001_event_task_label_availability_v1.csv"
MANIFEST = "covapie_batch001_task_label_availability_manifest_v1.json"
SUMMARY = "covapie_batch001_task_label_availability_summary_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, MANIFEST, SUMMARY)

SOURCE_PATH = (
    "src/covalent_ext/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_PATH = (
    "scripts/"
    "check_covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_PATH = (
    "tests/"
    "test_covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1.py"
)
AUTHORIZED_PUBLICATION_PATHS = frozenset(
    {
        SOURCE_PATH,
        CHECKER_PATH,
        TEST_PATH,
        *((OUTPUT_ROOT_RELATIVE / name).as_posix() for name in OUTPUT_FILENAMES),
    }
)

BATCH_ROOT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review/"
    "cumulative500-post-only-human-review-v1/batch-001"
)
BATCH_TOP_LEVEL_BINDINGS = {
    "README.md": "565ddf6e1eaf2778af5f973afe509b2c7bf98d941bd980acc75430e91402ef04",
    "batch_selection_v1.json": (
        "d3724773e603acc8983e168309212d40e387a238169da2aa1b5cff6140b34c61"
    ),
    "batch_worklist_v1.csv": (
        "757fb5f8fe74e2dce9c64d038d3f9fc0ca390cb395950cecddd0e44b545b20ac"
    ),
}

EXPECTED_SELECTION_ORDER = (
    "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74",
    "COVAPIE_BULK_REVIEW_UNIT_BE9EC76A77B78516",
    "COVAPIE_BULK_REVIEW_UNIT_5720D0B933DA07F1",
    "COVAPIE_BULK_REVIEW_UNIT_EBAE6C684690C8C9",
    "COVAPIE_BULK_REVIEW_UNIT_F02164FD5061B6D5",
    "COVAPIE_BULK_REVIEW_UNIT_FF0D6AE54C3F23F4",
    "COVAPIE_BULK_REVIEW_UNIT_3F001AD5FD754F45",
    "COVAPIE_BULK_REVIEW_UNIT_5A97818B52C80D18",
    "COVAPIE_BULK_REVIEW_UNIT_ECD4EA720B433528",
    "COVAPIE_BULK_REVIEW_UNIT_E29582A478EC4247",
)

TEMPLATE_SHA256 = {
    "COVAPIE_BULK_REVIEW_UNIT_3F001AD5FD754F45": (
        "d99bfb48d54432dd64f62ebf4b9619af76f9b6a9791ff1bb577a1f4ee62e6c47"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_5720D0B933DA07F1": (
        "75414a6a30a03530128cbc189c49273b6363eace65cdd4db81a1fdc7978ab2e0"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_5A97818B52C80D18": (
        "fa796e4013d0156aacbc3ff9215b2577ba685142f592128efecabbf542335e73"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_BE9EC76A77B78516": (
        "6c6ccf480f233695ed40a97773fa17f4ada9c3c264ae62d7ca58dc3515a8a4c7"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_E29582A478EC4247": (
        "9a88e0ce5d82f5a9fa0998f9b675306e8addfcf0a34013aafc5fa9de72336163"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_EBAE6C684690C8C9": (
        "14926cdf5fc1917743270122a06253dbf6c801820cb40137eeb320ba0ce1280a"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_ECD4EA720B433528": (
        "dc55ffb78987c770f4e8aaaba9487ef1adc220a7f6524c6fdf0ffd6c3f7ef23b"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_F02164FD5061B6D5": (
        "df9c14bd64f12e2d290ee79fdb1288e0600d79d015291e3dd176e2353bb08ab9"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74": (
        "17eba9aca390682c18fa65dc06de98ea44057f2ca280d3604f143e4cc3b202a3"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_FF0D6AE54C3F23F4": (
        "ab9711bb7a4c71764444dd66cc3ba461421ba218190c44cae529ae1e2786a445"
    ),
}

PACKET_SHA256 = {
    "COVAPIE_BULK_REVIEW_UNIT_3F001AD5FD754F45": (
        "18777e46f4d856aecac44915e16d3fc7bbb89686212eec2f39ec7f75e1181ccb"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_5720D0B933DA07F1": (
        "7e9c60fa69905c35d9c776bdb4c0fb46417c6cfe49e66c50613973d970949bee"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_5A97818B52C80D18": (
        "4f881b1f875e1f173cba91dec6a27f824b0af7654e0ecbe9ec2c372ae4c354c0"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_BE9EC76A77B78516": (
        "c72965448b8bcc09fa991db7ec37ee37c9acc41559c2f3a3f3ac156a65336548"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_E29582A478EC4247": (
        "177c1e543fefc0060d18a33085015ed9c5e8ab4e6a4a0cc5d8e7b8506b6d58e1"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_EBAE6C684690C8C9": (
        "24ff636bbb4a32ba63d1b4252f3458ad1446dce2fcc7193769d058a4b0f832a0"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_ECD4EA720B433528": (
        "b54e9b0cd2ead34d77685231676c4ce5b37387ffa887c09ec56965ed5938a913"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_F02164FD5061B6D5": (
        "df8629905697e4727d7cd6cf8746d6a545d4d7574169e832e61a0e9eaf4cf2e1"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74": (
        "57783d8a02bf3124b0b28b12c1233a79507bd9c13cf2667905298a970ea400f5"
    ),
    "COVAPIE_BULK_REVIEW_UNIT_FF0D6AE54C3F23F4": (
        "c7fb9614542913e4ece7b7245ef31f2fa23ac1147cca9550185475732a26018a"
    ),
}

POSITIVE_UNITS = {
    "COVAPIE_BULK_REVIEW_UNIT_5720D0B933DA07F1": {
        "ligand_component_id": "DJK",
        "ligand_reactive_atom": "C51",
        "roles": {
            "linker_atom_ids": ["N11"],
            "scaffold_atom_ids": [
                "BR", "C13", "C17", "C18", "C19", "C20", "C21", "C22",
                "C3", "C4", "C5", "C6", "C7", "C8", "C9", "N1", "N2", "N3",
            ],
            "warhead_atom_ids": ["C10", "C11", "C51", "O61"],
        },
    },
    "COVAPIE_BULK_REVIEW_UNIT_EBAE6C684690C8C9": {
        "ligand_component_id": "LN5",
        "ligand_reactive_atom": "CZ",
        "roles": {
            "linker_atom_ids": ["CB", "CD", "CG"],
            "scaffold_atom_ids": ["C", "CA", "N", "OA1", "OA2"],
            "warhead_atom_ids": ["CH1", "CT1", "CZ", "NE", "NH2"],
        },
    },
    "COVAPIE_BULK_REVIEW_UNIT_F02164FD5061B6D5": {
        "ligand_component_id": "PX5",
        "ligand_reactive_atom": "C15",
        "roles": {
            "linker_atom_ids": [],
            "scaffold_atom_ids": ["C1", "C2", "C3", "C4", "C5", "C6", "C8", "N9", "S7"],
            "warhead_atom_ids": ["C10", "C11", "C12", "C13", "C14", "C15", "O16", "O17"],
        },
    },
    "COVAPIE_BULK_REVIEW_UNIT_3F001AD5FD754F45": {
        "ligand_component_id": "NDU",
        "ligand_reactive_atom": "C6",
        "roles": {
            "linker_atom_ids": ["C1'"],
            "scaffold_atom_ids": [
                "C2'", "C3'", "C4'", "C5'", "O3'", "O4'", "O5'",
                "OP1", "OP2", "OP3", "P",
            ],
            "warhead_atom_ids": ["C2", "C4", "C5", "C6", "N1", "N3", "N5", "O2", "O4", "O51", "O52"],
        },
    },
    "COVAPIE_BULK_REVIEW_UNIT_E29582A478EC4247": {
        "ligand_component_id": "PTG",
        "ligand_reactive_atom": "C8",
        "roles": {
            "linker_atom_ids": ["C16", "C5"],
            "scaffold_atom_ids": ["C1", "C17", "C18", "C19", "C2", "C20", "C21", "C22", "C3", "C4", "O23", "O24"],
            "warhead_atom_ids": ["C10", "C11", "C13", "C14", "C15", "C6", "C7", "C8", "O12"],
        },
    },
}

NEGATIVE_UNITS = frozenset(
    {
        "COVAPIE_BULK_REVIEW_UNIT_BE9EC76A77B78516",
        "COVAPIE_BULK_REVIEW_UNIT_FF0D6AE54C3F23F4",
        "COVAPIE_BULK_REVIEW_UNIT_5A97818B52C80D18",
        "COVAPIE_BULK_REVIEW_UNIT_ECD4EA720B433528",
    }
)
HELD_OUT_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74"
HELD_OUT_REASON = "CHEMISTRY_LABEL_INCOMPLETE_PARENT_POST_MAPPING"

RELEVANT = "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
NOT_RELEVANT = "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"

PUBLISHED_REPOSITORY_BINDINGS = {
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/"
    "covapie_post_only_human_review_decisions_v1.json": (
        "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441"
    ),
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/"
    "covapie_post_only_human_review_progress_v1.json": (
        "e1e93ff28e823c1f52b306623bbf20c06f2c0c95cca90bb1e61ee4d1b7cea216"
    ),
    "src/covalent_ext/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1.py": (
        "f82a949e4df6522720df133d02f41104226b20845de1fc8bb4b0d93d558d2241"
    ),
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1/"
    "covapie_cumulative_500_event_routing_inventory_v1.csv": (
        "ea4ec17fed58d2a7100173ada17a0956a5c37ef4690899f415a9b497c8508173"
    ),
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1/"
    "covapie_cumulative_500_review_unit_inventory_v1.csv": (
        "8988f8e577df51883444ecda9a3274741421249feed7c38b7ae3c56b36ddabb9"
    ),
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1/"
    "covapie_cumulative_500_two_rule_routing_manifest_v1.json": (
        "da382f8ab6fe42c7be4607ba4d16b59443cb944984d386ae12f7b4e89d2f8942"
    ),
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1/"
    "covapie_cumulative_500_two_rule_routing_summary_v1.json": (
        "24f5621c75110e461de2a657ccd7404fd2352e44b44d0dbc23e8613454e56496"
    ),
}

MASK_CONTRACT_BINDINGS = {
    "src/covalent_ext/"
    "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1.py": (
        "71e70349fd9f9db754e255dbcf1059734a0c3ce2e04e973b14b1e3edd2ab45e1"
    ),
    "data/derived/covalent_small/"
    "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/"
    "covapie_canonical_task_truth_table.csv": (
        "586d483f67b9108af1af820b892b477329a1b6de24b0ad0b9ee46cebbaba20e5"
    ),
    "data/derived/covalent_small/"
    "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/"
    "covapie_role_task_mask_contract_manifest.json": (
        "f5f51d77b2bc347fc9eaf36b61fb9ab1561fb8542cb1a80df54f1474daf33f9f"
    ),
}

WARHEAD_TYPE_CONTRACT_BINDINGS = {
    "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py": (
        "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac"
    ),
    "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/"
    "covapie_tensor_label_and_loss_mask_contract_design_manifest.json": (
        "c0611d39074321744156c7ac3a527c54d4a84bd76c798a74fdbc1260b1bc6bcc"
    ),
    "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/"
    "covapie_tensor_label_loss_mask_contract_registry.csv": (
        "dde4a96d1b38f1aa095fb8285616ff2877f91b2274be8bbf7a2e53e1250ec933"
    ),
}

CURRENT_FEATURE_SEMANTICS_RESOLUTION_BINDINGS = {
    "src/covalent_ext/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py": (
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241"
    ),
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json": (
        "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0"
    ),
}

LABEL_SNAPSHOT_BASELINE_COMMIT = "a2c47314eea20bdadf93c20faf08b3c1c68d4bd6"
LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH = "src/covalent_ext/masking.py"
LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_SHA256 = (
    "a11ac211cedf14168c2866be960aa99703082b207234b016db0b8929c895c3c6"
)
MASK_RUNTIME_OBSERVATION_AT_LABEL_SNAPSHOT_BASELINE = {
    "baseline_commit": LABEL_SNAPSHOT_BASELINE_COMMIT,
    "path": LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH,
    "sha256": LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_SHA256,
    "observed_function": "build_long_form_mask",
    "observed_partition_validator": "_validate_partition",
    "require_nonempty_regions": True,
    "provenance_scope": "IMMUTABLE_BASELINE_GIT_BLOB_NOT_LIVE_WORKING_TREE_INPUT",
}

CURRENT_FEATURE_SEMANTICS_RESOLUTION = {
    "feature_semantics_audit_completed": True,
    "feature_semantics_known": True,
    "unknown_atom_feature_policy_resolved": True,
    "unknown_atom_policy_contract_resolved": True,
    "effective_open_issue_count": 0,
    "effective_open_issues": [],
    "protein_unknown_atom_policy": (
        "fail_closed_rejection_required_for_checkpoint_compatibility"
    ),
    "ligand_unknown_atom_policy": (
        "fail_closed_rejection_required_for_checkpoint_compatibility"
    ),
    "unsupported_nonhydrogen_handling": "reject_sample_fail_closed",
    "silent_zero_vector_fallback_allowed": False,
    "checkpoint_categorical_width": 10,
}

STALE_FEATURE_SEMANTICS_CLAIMS = (
    "feature_semantics_audit_required_before_formal_training",
    "Step12D_was_smoke_legality_not_final_training_feature_contract",
    "UNKNOWN_ATOM_FEATURE_POLICY_and_feature_semantics_known_must_be_formally_audited",
    "feature_semantics_unresolved",
    "unknown_atom_policy_unresolved",
    "feature_semantics_known=false",
    "unknown_atom_feature_policy_resolved=false",
    '"feature_semantics_known":false',
    '"unknown_atom_feature_policy_resolved":false',
)

CANONICAL_TASKS = (
    ("warhead_only", "A", ("warhead",)),
    ("linker_plus_warhead", "B", ("linker", "warhead")),
    ("scaffold_plus_warhead", "B2", ("scaffold", "warhead")),
    ("scaffold_only", "B3", ("scaffold",)),
    ("scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead")),
)
MASK_CONTRACT_SOURCE_SHA256 = MASK_CONTRACT_BINDINGS[
    "src/covalent_ext/"
    "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1.py"
]
EVENT_INVENTORY_SHA256 = PUBLISHED_REPOSITORY_BINDINGS[
    "data/derived/covalent_small/"
    "covapie_cumulative_500_supported_post_only_two_rule_routing_v1/"
    "covapie_cumulative_500_event_routing_inventory_v1.csv"
]
PRE_REVISION_SNAPSHOT_SHA256 = (
    "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200"
)
PRE_REVISION_MATRIX_SHA256 = (
    "f8481147babbad02215c3c3f767fe22ba6a511b8a076482a9635fec5d5cf8e82"
)

MATRIX_HEADER = (
    "canonical_event_id",
    "review_unit_id",
    "source_template_sha256",
    "published_event_inventory_sha256",
    "canonical_five_mask_contract_sha256",
    "completed_lane",
    "task_domain_relevance_label_available",
    "task_domain_relevance_label",
    "positive_generative_supervision_eligible",
    "reactive_atom_pair_label_available",
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "warhead_atom_set_label_available",
    "warhead_atom_ids_json",
    "role_partition_label_available",
    "scaffold_atom_ids_json",
    "linker_atom_ids_json",
    "role_warhead_atom_ids_json",
    "post_geometry_usability_label_available",
    "post_geometry_training_usable",
    "post_geometry_supervision_available",
    "event_training_use_label_available",
    "event_training_use_decision",
    "approved_canonical_reaction_family_target_available",
    "canonical_reaction_family_id",
    "proposed_family_label_non_authoritative",
    "proposed_family_label_is_training_class_target",
    "warhead_type_classification_target_available",
    "warhead_type_classification_target_id",
    "warhead_type_classification_availability_status",
    "production_family_authority_created",
    "experimental_pre_geometry_target_available",
    "experimental_pre_geometry_target",
    "experimental_pre_geometry_availability_status",
    "mask_A_warhead_only_available",
    "mask_A_warhead_only_target_atom_ids_json",
    "mask_B_linker_plus_warhead_available",
    "mask_B_linker_plus_warhead_target_atom_ids_json",
    "mask_B2_scaffold_plus_warhead_available",
    "mask_B2_scaffold_plus_warhead_target_atom_ids_json",
    "mask_B3_scaffold_only_available",
    "mask_B3_scaffold_only_target_atom_ids_json",
    "mask_C_scaffold_plus_linker_plus_warhead_available",
    "mask_C_scaffold_plus_linker_plus_warhead_target_atom_ids_json",
    "five_mask_derivation_status",
    "label_availability_status",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(header),
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(header):
            raise ValueError("MATRIX_ROW_SCHEMA_OR_ORDER_INVALID")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except Exception as error:
        raise ValueError("INVALID_JSON:" + path.name) from error
    if type(value) is not dict:
        raise ValueError("JSON_ROOT_NOT_OBJECT:" + path.name)
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV_HEADER_MISSING")
            rows = list(reader)
    except Exception as error:
        raise ValueError("INVALID_CSV:" + path.name) from error
    if any(None in row.values() for row in rows):
        raise ValueError("CSV_ROW_MALFORMED:" + path.name)
    return rows


def _verify_sha(path: Path, expected: str, label: str) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError("BOUND_INPUT_MISSING:" + label) from error
    if _sha256(payload) != expected:
        raise ValueError("BOUND_INPUT_SHA256_MISMATCH:" + label)
    return payload


def _stable_binding(path: str, sha256: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256}


def _verify_repository_bindings(
    repo_root: Path, bindings: Mapping[str, str]
) -> dict[str, dict[str, str]]:
    stable: dict[str, dict[str, str]] = {}
    for relative, expected in bindings.items():
        _verify_sha(repo_root / relative, expected, relative)
        stable[relative] = _stable_binding(relative, expected)
    return stable


def snapshot_external_workspace_v1(batch_root: Path) -> dict[str, str]:
    """Return a deterministic content snapshot without recording mtimes."""

    return {
        path.relative_to(batch_root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(batch_root.rglob("*"))
        if path.is_file()
    }


def _validate_current_feature_semantics_resolution(repo_root: Path) -> None:
    manifest = _read_json(
        repo_root
        / "data/derived/covalent_small/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
    )
    observed = {
        field: manifest.get(field)
        for field in CURRENT_FEATURE_SEMANTICS_RESOLUTION
    }
    if observed != CURRENT_FEATURE_SEMANTICS_RESOLUTION:
        raise ValueError("CURRENT_FEATURE_SEMANTICS_RESOLUTION_INVALID")


def validate_mask_runtime_observation_blob_v1(payload: bytes) -> None:
    """AST-validate frozen baseline runtime bytes without executing them."""

    if type(payload) is not bytes:
        raise ValueError("LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_BLOB_INVALID")
    try:
        tree = ast.parse(
            payload.decode("utf-8", errors="strict"),
            filename=LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH,
        )
    except Exception as error:
        raise ValueError("LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_BLOB_INVALID") from error
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    function = functions.get("build_long_form_mask")
    if function is None:
        raise ValueError("LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_BLOB_INVALID")
    partition_calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_validate_partition"
    ]
    if len(partition_calls) != 1:
        raise ValueError("LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_BLOB_INVALID")
    keywords = {keyword.arg: keyword.value for keyword in partition_calls[0].keywords}
    required = keywords.get("require_nonempty_regions")
    if not isinstance(required, ast.Constant) or required.value is not True:
        raise ValueError(
            "LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_NONEMPTY_REGION_GUARD_MISSING"
        )


def reject_stale_feature_semantics_claims_v1(value: object) -> None:
    """Reject stale or equivalent unresolved-feature claims in an artifact."""

    text = _json_bytes(value).decode("utf-8")
    stale = [claim for claim in STALE_FEATURE_SEMANTICS_CLAIMS if claim in text]
    if stale:
        raise ValueError("STALE_FEATURE_SEMANTICS_CLAIM_PRESENT:" + stale[0])


def _validate_mask_and_warhead_type_contracts(repo_root: Path) -> None:
    mask_manifest_path = repo_root / (
        "data/derived/covalent_small/"
        "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/"
        "covapie_role_task_mask_contract_manifest.json"
    )
    mask_manifest = _read_json(mask_manifest_path)
    if (
        mask_manifest.get("canonical_role_count") != 3
        or mask_manifest.get("canonical_task_count") != 5
        or mask_manifest.get("semantic_resolutions", {}).get(
            "primary_role_regions_nonempty"
        )
        is not True
        or mask_manifest.get("semantic_resolutions", {}).get(
            "primary_role_vocabulary"
        )
        != "0=scaffold|1=linker|2=warhead"
    ):
        raise ValueError("CANONICAL_FIVE_MASK_CONTRACT_INVALID")

    truth_path = repo_root / (
        "data/derived/covalent_small/"
        "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/"
        "covapie_canonical_task_truth_table.csv"
    )
    rows = _read_csv(truth_path)
    observed = tuple(
        (
            row["semantic_name"],
            row["display_alias"],
            tuple(filter(None, row["generated_primary_roles"].split(";"))),
        )
        for row in rows
    )
    if observed != CANONICAL_TASKS:
        raise ValueError("CANONICAL_FIVE_MASK_TRUTH_TABLE_INVALID")

    warhead_manifest = _read_json(
        repo_root
        / "data/derived/covalent_small/"
        "covapie_tensor_label_and_loss_mask_contract_design_v1/"
        "covapie_tensor_label_and_loss_mask_contract_design_manifest.json"
    )
    if (
        warhead_manifest.get("warhead_type_vocabulary") != []
        or warhead_manifest.get("warhead_type_vocabulary_frozen") is not False
        or warhead_manifest.get("warhead_type_valid_sample_count") != 0
    ):
        raise ValueError("WARHEAD_TYPE_CLASSIFICATION_CONTRACT_CHANGED")


def _validate_common_template(
    unit_id: str,
    template: Mapping[str, Any],
    packet: Mapping[str, Any],
    selected: Mapping[str, Any],
) -> None:
    if (
        template.get("schema_version")
        != "covapie_cumulative_500_human_review_template_v1"
        or template.get("review_unit_id") != unit_id
        or packet.get("review_unit_id") != unit_id
        or selected.get("review_unit_id") != unit_id
        or template.get("machine_evidence_packet") != "review_packet_v1.json"
        or not template.get("reviewer_id")
        or not template.get("reviewed_at_utc")
        or not template.get("review_rationale")
        or template.get("authority_flags")
        != {
            "chemistry_authority_created": False,
            "human_decision_recorded": True,
            "production_authority_created": False,
            "training_label_committed": False,
        }
    ):
        raise ValueError("HUMAN_TEMPLATE_COMMON_CONTRACT_INVALID:" + unit_id)

    events = template.get("events")
    if type(events) is not list or not events:
        raise ValueError("HUMAN_TEMPLATE_EVENTS_INVALID:" + unit_id)
    event_ids = [event.get("canonical_event_id") for event in events]
    if (
        len(event_ids) != len(set(event_ids))
        or event_ids != packet.get("all_event_ids")
        or event_ids != selected.get("canonical_event_ids")
        or event_ids != [event.get("canonical_event_id") for event in packet.get("events", [])]
    ):
        raise ValueError("HUMAN_TEMPLATE_EVENT_IDENTITY_INVALID:" + unit_id)


def _validate_positive_template(
    unit_id: str,
    template: Mapping[str, Any],
    packet: Mapping[str, Any],
    event_inventory: Mapping[str, Mapping[str, str]],
) -> None:
    expected = POSITIVE_UNITS[unit_id]
    roles = template.get("roles")
    family = template.get("warhead_family_decision")
    reactive = template.get("reactive_atom_confirmation")
    if (
        template.get("workflow_status") != "COMPLETED"
        or template.get("training_domain_relevance_decision") != RELEVANT
        or reactive
        != {
            "confirmed_atom_id": expected["ligand_reactive_atom"],
            "status": "CONFIRMED",
        }
        or roles != expected["roles"]
        or template.get("warhead_atom_ids") != expected["roles"]["warhead_atom_ids"]
        or type(family) is not dict
        or family.get("decision")
        != "NEW_WARHEAD_FAMILY_REQUIRES_AUTHORITY_REVIEW"
        or family.get("canonical_reaction_family_id") != ""
        or not family.get("proposed_warhead_family_label")
    ):
        raise ValueError("COMPLETED_POSITIVE_TEMPLATE_INVALID:" + unit_id)

    role_sets = [
        set(roles["scaffold_atom_ids"]),
        set(roles["linker_atom_ids"]),
        set(roles["warhead_atom_ids"]),
    ]
    all_ids = [atom for atoms in roles.values() for atom in atoms]
    if (
        len(all_ids) != len(set(all_ids))
        or any(role_sets[left] & role_sets[right] for left in range(3) for right in range(left + 1, 3))
        or expected["ligand_reactive_atom"] not in role_sets[2]
    ):
        raise ValueError("POSITIVE_ROLE_PARTITION_INVALID:" + unit_id)

    if packet.get("reactive_atom") != expected["ligand_reactive_atom"]:
        raise ValueError("PACKET_REACTIVE_ATOM_MISMATCH:" + unit_id)
    for decision, evidence in zip(template["events"], packet["events"]):
        event_id = decision["canonical_event_id"]
        inventory = event_inventory.get(event_id)
        protein = evidence.get("protein_cys_identity")
        if (
            decision.get("post_geometry_training_usable") != "YES"
            or decision.get("event_training_use_decision") != "INCLUDE"
            or decision.get("event_exclusion_reason") != ""
            or evidence.get("ligand_reactive_atom") != expected["ligand_reactive_atom"]
            or type(protein) is not dict
            or protein.get("protein_reactive_atom") != "SG"
            or inventory is None
            or inventory.get("canonical_event_id") != event_id
            or inventory.get("ligand_component_id") != expected["ligand_component_id"]
            or inventory.get("ligand_reactive_atom") != expected["ligand_reactive_atom"]
            or inventory.get("workload_review_unit_id") != unit_id
        ):
            raise ValueError("POSITIVE_EVENT_EVIDENCE_INVALID:" + event_id)


def _validate_negative_template(
    unit_id: str,
    template: Mapping[str, Any],
    packet: Mapping[str, Any],
    event_inventory: Mapping[str, Mapping[str, str]],
) -> None:
    roles = template.get("roles")
    if (
        template.get("workflow_status") != "COMPLETED"
        or template.get("training_domain_relevance_decision") != NOT_RELEVANT
        or template.get("reactive_atom_confirmation") is not None
        or template.get("warhead_family_decision") is not None
        or template.get("warhead_atom_ids") != []
        or roles
        != {
            "linker_atom_ids": [],
            "scaffold_atom_ids": [],
            "warhead_atom_ids": [],
        }
    ):
        raise ValueError("COMPLETED_NEGATIVE_TEMPLATE_INVALID:" + unit_id)
    for event in template["events"]:
        event_id = event["canonical_event_id"]
        if (
            event.get("event_exclusion_reason") is not None
            or event.get("event_training_use_decision") is not None
            or event.get("post_geometry_training_usable") is not None
            or event_inventory.get(event_id, {}).get("workload_review_unit_id") != unit_id
            or event_id not in {item.get("canonical_event_id") for item in packet["events"]}
        ):
            raise ValueError("NEGATIVE_EVENT_FIELDS_NOT_BLANK:" + event_id)


def _validate_held_out_template(template: Mapping[str, Any]) -> None:
    if (
        template.get("review_unit_id") != HELD_OUT_UNIT_ID
        or template.get("workflow_status") != "IN_PROGRESS"
        or template.get("training_domain_relevance_decision") != RELEVANT
        or len(template.get("events", [])) != 9
        or template.get("reactive_atom_confirmation") is not None
        or template.get("warhead_family_decision") is not None
        or template.get("warhead_atom_ids") != []
    ):
        raise ValueError("HELD_OUT_ONL_CONTRACT_INVALID")


def verify_bound_inputs_v1(
    repo_root: Path, *, batch_root: Path | None = None
) -> dict[str, Any]:
    """Fail closed on every source, predecessor, and task-contract binding."""

    repo_root = repo_root.resolve()
    batch_root = (
        batch_root.resolve()
        if batch_root is not None
        else repo_root.parent / BATCH_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    expected_files = set(BATCH_TOP_LEVEL_BINDINGS)
    for unit_id in EXPECTED_SELECTION_ORDER:
        expected_files.add(f"{unit_id}/review_packet_v1.json")
        expected_files.add(f"{unit_id}/review_template_v1.json")
    observed_files = set(snapshot_external_workspace_v1(batch_root))
    if observed_files != expected_files:
        raise ValueError("EXTERNAL_BATCH_EXACT_FILE_SET_INVALID")

    for name, expected in BATCH_TOP_LEVEL_BINDINGS.items():
        _verify_sha(batch_root / name, expected, name)
    templates: dict[str, dict[str, Any]] = {}
    packets: dict[str, dict[str, Any]] = {}
    for unit_id in EXPECTED_SELECTION_ORDER:
        template_path = batch_root / unit_id / "review_template_v1.json"
        packet_path = batch_root / unit_id / "review_packet_v1.json"
        _verify_sha(template_path, TEMPLATE_SHA256[unit_id], unit_id + ":template")
        _verify_sha(packet_path, PACKET_SHA256[unit_id], unit_id + ":packet")
        templates[unit_id] = _read_json(template_path)
        packets[unit_id] = _read_json(packet_path)

    selection = _read_json(batch_root / "batch_selection_v1.json")
    selected_units = selection.get("selected_units")
    if (
        selection.get("batch_id") != "batch-001"
        or type(selected_units) is not list
        or tuple(row.get("review_unit_id") for row in selected_units)
        != EXPECTED_SELECTION_ORDER
    ):
        raise ValueError("BATCH_SELECTION_IDENTITY_INVALID")
    selected_by_id = {row["review_unit_id"]: row for row in selected_units}

    worklist = _read_csv(batch_root / "batch_worklist_v1.csv")
    if (
        tuple(row.get("review_unit_id") for row in worklist)
        != EXPECTED_SELECTION_ORDER
        or [int(row["selection_order"]) for row in worklist] != list(range(1, 11))
    ):
        raise ValueError("BATCH_WORKLIST_IDENTITY_INVALID")

    predecessor = _verify_repository_bindings(
        repo_root, PUBLISHED_REPOSITORY_BINDINGS
    )
    mask_contract = _verify_repository_bindings(repo_root, MASK_CONTRACT_BINDINGS)
    warhead_type_contract = _verify_repository_bindings(
        repo_root, WARHEAD_TYPE_CONTRACT_BINDINGS
    )
    feature_semantics_resolution = _verify_repository_bindings(
        repo_root, CURRENT_FEATURE_SEMANTICS_RESOLUTION_BINDINGS
    )
    _validate_mask_and_warhead_type_contracts(repo_root)
    _validate_current_feature_semantics_resolution(repo_root)

    inventory_path = repo_root / (
        "data/derived/covalent_small/"
        "covapie_cumulative_500_supported_post_only_two_rule_routing_v1/"
        "covapie_cumulative_500_event_routing_inventory_v1.csv"
    )
    inventory_rows = _read_csv(inventory_path)
    if len(inventory_rows) != 500:
        raise ValueError("PUBLISHED_EVENT_INVENTORY_COUNT_INVALID")
    inventory = {row["canonical_event_id"]: row for row in inventory_rows}
    if len(inventory) != 500:
        raise ValueError("PUBLISHED_EVENT_INVENTORY_DUPLICATE_ID")

    for unit_id in EXPECTED_SELECTION_ORDER:
        _validate_common_template(
            unit_id,
            templates[unit_id],
            packets[unit_id],
            selected_by_id[unit_id],
        )
        if unit_id in POSITIVE_UNITS:
            _validate_positive_template(
                unit_id, templates[unit_id], packets[unit_id], inventory
            )
        elif unit_id in NEGATIVE_UNITS:
            _validate_negative_template(
                unit_id, templates[unit_id], packets[unit_id], inventory
            )
        elif unit_id == HELD_OUT_UNIT_ID:
            _validate_held_out_template(templates[unit_id])
        else:
            raise ValueError("UNCLASSIFIED_BATCH_UNIT:" + unit_id)

    workflows = Counter(template["workflow_status"] for template in templates.values())
    completed_event_count = sum(
        len(template["events"])
        for template in templates.values()
        if template["workflow_status"] == "COMPLETED"
    )
    if workflows != {"COMPLETED": 9, "IN_PROGRESS": 1} or completed_event_count != 37:
        raise ValueError("EXACT_COMPLETED_INGESTION_POPULATION_INVALID")

    batch_binding = {
        "batch_id": "batch-001",
        "source_root_relative_to_repository_parent": (
            BATCH_ROOT_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        ),
        "top_level_files": {
            name: _stable_binding(name, sha)
            for name, sha in sorted(BATCH_TOP_LEVEL_BINDINGS.items())
        },
        "review_packet_bindings": {
            unit_id: _stable_binding(
                f"{unit_id}/review_packet_v1.json", PACKET_SHA256[unit_id]
            )
            for unit_id in EXPECTED_SELECTION_ORDER
        },
        "review_template_bindings": {
            unit_id: _stable_binding(
                f"{unit_id}/review_template_v1.json", TEMPLATE_SHA256[unit_id]
            )
            for unit_id in EXPECTED_SELECTION_ORDER
        },
        "exact_file_count": 23,
        "review_packet_count": 10,
        "review_template_count": 10,
    }
    return {
        "batch_root": batch_root,
        "batch_binding": batch_binding,
        "templates": templates,
        "packets": packets,
        "selected_by_id": selected_by_id,
        "inventory": inventory,
        "predecessor_bindings": predecessor,
        "mask_contract_bindings": mask_contract,
        "warhead_type_contract_bindings": warhead_type_contract,
        "current_feature_semantics_resolution_bindings": (
            feature_semantics_resolution
        ),
    }


def _mask_targets(roles: Mapping[str, list[str]]) -> dict[str, list[str]]:
    role_atoms = {
        "scaffold": roles["scaffold_atom_ids"],
        "linker": roles["linker_atom_ids"],
        "warhead": roles["warhead_atom_ids"],
    }
    return {
        alias: [atom for role in generated for atom in role_atoms[role]]
        for _semantic, alias, generated in CANONICAL_TASKS
    }


def _matrix_row(
    unit_id: str, template: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, str]:
    positive = unit_id in POSITIVE_UNITS
    if positive:
        roles = template["roles"]
        exact3_nonempty = all(
            roles[field]
            for field in (
                "scaffold_atom_ids",
                "linker_atom_ids",
                "warhead_atom_ids",
            )
        )
        mask_targets = _mask_targets(roles)
        masks_available = exact3_nonempty
        mask_status = (
            "AVAILABLE_EXACT_HUMAN_ROLE_PARTITION"
            if exact3_nonempty
            else "UNAVAILABLE_CURRENT_EXACT3_CONTRACT_REQUIRES_EACH_PRIMARY_ROLE_NONEMPTY"
        )
        family = template["warhead_family_decision"]
        scaffold_cell = _json_cell(roles["scaffold_atom_ids"])
        linker_cell = _json_cell(roles["linker_atom_ids"])
        warhead_cell = _json_cell(roles["warhead_atom_ids"])
        proposed_family = family["proposed_warhead_family_label"]
        event_use = event["event_training_use_decision"]
        post_usable = event["post_geometry_training_usable"]
        ligand_atom = template["reactive_atom_confirmation"]["confirmed_atom_id"]
        lane = "COMPLETED_POSITIVE_CHEMISTRY"
        label_status = "AVAILABLE_POSITIVE_POST_ONLY_SUPERVISION"
        family_status = "UNAVAILABLE_MISSING_APPROVED_FAMILY_AND_FROZEN_WARHEAD_TYPE_VOCABULARY"
        pre_status = "UNAVAILABLE_EXPERIMENTAL_PRE_NOT_REQUIRED_FOR_POST_ONLY_V1"
    else:
        masks_available = False
        mask_targets = {alias: [] for _semantic, alias, _generated in CANONICAL_TASKS}
        mask_status = "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE"
        scaffold_cell = linker_cell = warhead_cell = ""
        proposed_family = event_use = post_usable = ligand_atom = ""
        lane = "COMPLETED_TASK_DOMAIN_NEGATIVE"
        label_status = "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE"
        family_status = "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE"
        pre_status = "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE"

    available = "true" if positive else "false"
    mask_available = "true" if masks_available else "false"
    mask_cell = lambda alias: _json_cell(mask_targets[alias]) if masks_available else ""
    return {
        "canonical_event_id": event["canonical_event_id"],
        "review_unit_id": unit_id,
        "source_template_sha256": TEMPLATE_SHA256[unit_id],
        "published_event_inventory_sha256": EVENT_INVENTORY_SHA256,
        "canonical_five_mask_contract_sha256": MASK_CONTRACT_SOURCE_SHA256,
        "completed_lane": lane,
        "task_domain_relevance_label_available": "true",
        "task_domain_relevance_label": template["training_domain_relevance_decision"],
        "positive_generative_supervision_eligible": available,
        "reactive_atom_pair_label_available": available,
        "protein_reactive_atom": "SG" if positive else "",
        "ligand_reactive_atom": ligand_atom,
        "warhead_atom_set_label_available": available,
        "warhead_atom_ids_json": warhead_cell,
        "role_partition_label_available": available,
        "scaffold_atom_ids_json": scaffold_cell,
        "linker_atom_ids_json": linker_cell,
        "role_warhead_atom_ids_json": warhead_cell,
        "post_geometry_usability_label_available": available,
        "post_geometry_training_usable": post_usable,
        "post_geometry_supervision_available": available,
        "event_training_use_label_available": available,
        "event_training_use_decision": event_use,
        "approved_canonical_reaction_family_target_available": "false",
        "canonical_reaction_family_id": "",
        "proposed_family_label_non_authoritative": proposed_family,
        "proposed_family_label_is_training_class_target": "false",
        "warhead_type_classification_target_available": "false",
        "warhead_type_classification_target_id": "",
        "warhead_type_classification_availability_status": family_status,
        "production_family_authority_created": "false",
        "experimental_pre_geometry_target_available": "false",
        "experimental_pre_geometry_target": "",
        "experimental_pre_geometry_availability_status": pre_status,
        "mask_A_warhead_only_available": mask_available,
        "mask_A_warhead_only_target_atom_ids_json": mask_cell("A"),
        "mask_B_linker_plus_warhead_available": mask_available,
        "mask_B_linker_plus_warhead_target_atom_ids_json": mask_cell("B"),
        "mask_B2_scaffold_plus_warhead_available": mask_available,
        "mask_B2_scaffold_plus_warhead_target_atom_ids_json": mask_cell("B2"),
        "mask_B3_scaffold_only_available": mask_available,
        "mask_B3_scaffold_only_target_atom_ids_json": mask_cell("B3"),
        "mask_C_scaffold_plus_linker_plus_warhead_available": mask_available,
        "mask_C_scaffold_plus_linker_plus_warhead_target_atom_ids_json": mask_cell("C"),
        "five_mask_derivation_status": mask_status,
        "label_availability_status": label_status,
    }


def build_artifacts_v1(
    repo_root: Path, *, batch_root: Path | None = None
) -> dict[str, bytes]:
    """Return four deterministic artifact payloads from bound evidence."""

    bound = verify_bound_inputs_v1(repo_root, batch_root=batch_root)
    templates = bound["templates"]
    completed_unit_ids = tuple(
        unit_id
        for unit_id in EXPECTED_SELECTION_ORDER
        if templates[unit_id]["workflow_status"] == "COMPLETED"
    )
    decisions = []
    matrix_rows = []
    all_event_ids: list[str] = []
    for unit_id in completed_unit_ids:
        template = templates[unit_id]
        lane = (
            "COMPLETED_POSITIVE_CHEMISTRY"
            if unit_id in POSITIVE_UNITS
            else "COMPLETED_TASK_DOMAIN_NEGATIVE"
        )
        decisions.append(
            {
                "review_unit_id": unit_id,
                "source_template_relative_path": (
                    f"{unit_id}/review_template_v1.json"
                ),
                "source_template_sha256": TEMPLATE_SHA256[unit_id],
                "completed_lane": lane,
                "human_decision": template,
            }
        )
        for event in template["events"]:
            matrix_rows.append(_matrix_row(unit_id, template, event))
            all_event_ids.append(event["canonical_event_id"])

    if (
        len(completed_unit_ids) != 9
        or len(matrix_rows) != 37
        or len(all_event_ids) != len(set(all_event_ids))
        or HELD_OUT_UNIT_ID in completed_unit_ids
        or any(":ONL:" in event_id for event_id in all_event_ids)
    ):
        raise ValueError("BUILT_INGESTION_POPULATION_INVALID")

    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_COMPLETED_HUMAN_DECISION_SUCCESSOR",
        "source_batch_binding": bound["batch_binding"],
        "published_predecessor_bindings": bound["predecessor_bindings"],
        "completed_human_decisions": decisions,
        "counts": {
            "unit_count": 9,
            "event_count": 37,
            "completed_positive_unit_count": 5,
            "completed_positive_event_count": 13,
            "completed_negative_unit_count": 4,
            "completed_negative_event_count": 24,
            "in_progress_units_ingested": 0,
            "duplicate_unit_count": 0,
            "duplicate_event_count": 0,
        },
        "held_out_in_progress": {
            "review_unit_id": HELD_OUT_UNIT_ID,
            "source_template_sha256": TEMPLATE_SHA256[HELD_OUT_UNIT_ID],
            "workflow_status": "IN_PROGRESS",
            "task_domain_relevance_decision_preserved_externally": RELEVANT,
            "held_out_in_progress_unit_count": 1,
            "held_out_in_progress_event_count": 9,
            "held_out_reason": HELD_OUT_REASON,
            "ONL_ingested": False,
        },
        "authority_boundary": {
            "family_authority_created": False,
            "production_authority_created": False,
            "proposed_family_labels_are_non_authoritative": True,
            "proposed_family_labels_are_training_class_targets": False,
        },
    }
    snapshot_payload = _json_bytes(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, matrix_rows)
    if _sha256(snapshot_payload) != PRE_REVISION_SNAPSHOT_SHA256:
        raise ValueError("PRE_REVISION_SNAPSHOT_BYTES_CHANGED")
    if _sha256(matrix_payload) != PRE_REVISION_MATRIX_SHA256:
        raise ValueError("PRE_REVISION_MATRIX_BYTES_CHANGED")

    positive_rows = [
        row
        for row in matrix_rows
        if row["completed_lane"] == "COMPLETED_POSITIVE_CHEMISTRY"
    ]
    negative_rows = [
        row
        for row in matrix_rows
        if row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    ]
    mask_counts = {
        "mask_A_available_event_count": sum(
            row["mask_A_warhead_only_available"] == "true" for row in matrix_rows
        ),
        "mask_B_available_event_count": sum(
            row["mask_B_linker_plus_warhead_available"] == "true"
            for row in matrix_rows
        ),
        "mask_B2_available_event_count": sum(
            row["mask_B2_scaffold_plus_warhead_available"] == "true"
            for row in matrix_rows
        ),
        "mask_B3_available_event_count": sum(
            row["mask_B3_scaffold_only_available"] == "true"
            for row in matrix_rows
        ),
        "mask_C_available_event_count": sum(
            row["mask_C_scaffold_plus_linker_plus_warhead_available"] == "true"
            for row in matrix_rows
        ),
    }
    if set(mask_counts.values()) != {11}:
        raise ValueError("FIVE_MASK_AVAILABILITY_COUNT_INVALID")

    availability = {
        "row_count": 37,
        "unique_event_count": 37,
        "positive_rows": 13,
        "negative_rows": 24,
        "positive_generative_supervision_eligible_rows": 13,
        "reactive_pair_available_rows": 13,
        "warhead_atom_set_available_rows": 13,
        "role_partition_available_rows": 13,
        "post_geometry_available_rows": 13,
        "event_training_use_available_rows": 13,
        "approved_canonical_reaction_family_available_rows": 0,
        "warhead_type_classification_available_rows": 0,
        "negative_rows_with_fabricated_chemistry_label": 0,
        **mask_counts,
    }
    if len(positive_rows) != 13 or len(negative_rows) != 24:
        raise ValueError("MATRIX_LANE_COUNTS_INVALID")

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "EVENT_LEVEL_TASK_LABEL_AVAILABILITY_CONTRACT_NOT_TENSORIZATION",
        "source_batch_binding": bound["batch_binding"],
        "published_predecessor_bindings": bound["predecessor_bindings"],
        "canonical_five_mask_contract_bindings": bound["mask_contract_bindings"],
        "warhead_type_classification_contract_bindings": bound[
            "warhead_type_contract_bindings"
        ],
        "current_feature_semantics_resolution_bindings": bound[
            "current_feature_semantics_resolution_bindings"
        ],
        "mask_runtime_observation_at_label_snapshot_baseline": (
            MASK_RUNTIME_OBSERVATION_AT_LABEL_SNAPSHOT_BASELINE
        ),
        "current_feature_semantics_resolution": {
            **CURRENT_FEATURE_SEMANTICS_RESOLUTION,
            "feature_semantics_reopened": False,
        },
        "canonical_five_mask_semantics": [
            {
                "semantic_name": semantic,
                "display_alias": alias,
                "generated_primary_roles": list(generated),
            }
            for semantic, alias, generated in CANONICAL_TASKS
        ],
        "mask_derivation_interpretation": {
            "primary_role_regions_nonempty_required_at_label_snapshot_baseline": True,
            "label_snapshot_baseline_build_long_form_mask_require_nonempty_regions": True,
            "PX5_human_role_partition_valid_for_chemistry_snapshot": True,
            "PX5_linker_atom_ids": [],
            "PX5_five_mask_runtime_compatible_at_label_snapshot": False,
            "PX5_failure_reason": (
                "LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_REQUIRES_ALL_PRIMARY_ROLE_REGIONS_NONEMPTY"
            ),
            "PX5_human_role_labels_modified": False,
            "PX5_mask_unavailable_event_count": 2,
            "other_positive_event_all_five_mask_targets_available_at_label_snapshot_count": 11,
            "future_mask_runtime_may_legitimately_support_empty_linker": True,
            "historical_snapshot_dictates_future_runtime_semantics": False,
        },
        "warhead_type_classification_interpretation": {
            "approved_family_target_available_event_count": 0,
            "current_warhead_type_vocabulary_frozen": False,
            "proposed_family_label_is_sufficient_training_class_authority": False,
            "new_class_ids_created": False,
        },
        "stage_local_unavailable_target_accounting": [
            {
                "status_id": (
                    "FAMILY_DEPENDENT_CLASSIFICATION_AUTHORITY_UNAVAILABLE"
                ),
                "positive_event_count": 13,
                "positive_events_with_proposed_family_labels_only": 13,
                "approved_family_target_available_event_count": 0,
                "warhead_type_classification_available_event_count": 0,
                "handled_by_per_task_masking": True,
                "other_positive_supervision_blocked": False,
            },
            {
                "status_id": (
                    "PX5_LABEL_SNAPSHOT_BASELINE_FIVE_MASK_RUNTIME_REQUIRES_NONEMPTY_LINKER_REGION"
                ),
                "ligand_component_id": "PX5",
                "event_count": 2,
                "scaffold_region_nonempty": True,
                "linker_atom_ids": [],
                "warhead_region_nonempty": True,
                "human_role_partition_valid": True,
                "all_five_masks_available_at_label_snapshot": False,
                "gap_type": "MODEL_CONTRACT_EMPTY_LINKER_COMPATIBILITY_GAP",
                "chemistry_invalid": False,
                "training_domain_invalid": False,
                "family_problem": False,
                "ONL_problem": False,
            },
        ],
        "ingestion_counts": snapshot["counts"],
        "availability_counts": availability,
        "held_out_in_progress": snapshot["held_out_in_progress"],
        "artifact_bindings": {
            SNAPSHOT: {"sha256": _sha256(snapshot_payload)},
            MATRIX: {"sha256": _sha256(matrix_payload)},
        },
        "model_integration_contract": {
            "next_step_must_consume_only_targets_marked_available": True,
            "missing_family_class_authority_handled_by_per_task_masking": True,
            "valid_positive_post_samples_removed_for_missing_family_authority": False,
            "valid_positive_post_samples_removed_for_missing_experimental_PRE": False,
            "valid_positive_post_only_model_integration_design_input_count": 13,
            "all_five_mask_runtime_compatible_at_label_snapshot_event_count": 11,
            "empty_linker_runtime_gap_at_label_snapshot_event_count": 2,
            "future_live_masking_runtime_may_change_without_invalidating_snapshot": True,
            "batch_002_required_before_model_integration_design": False,
            "tensorization_performed": False,
            "dataloader_created": False,
            "loss_computation_performed": False,
            "training_authorized": False,
        },
        "safety": {
            "predecessor_human_overlay_modified": False,
            "predecessor_human_progress_modified": False,
            "external_batch_workspace_modified": False,
            "canonical_cache_modified": False,
            "attempt_001_modified": False,
            "family_authority_created": False,
            "production_authority_created": False,
            "batch_002_created": False,
            "tensorization_performed": False,
            "training_performed": False,
            "network_performed": False,
            "GPU_used": False,
            "checkpoint_read": False,
            "model_forward_performed": False,
            "loss_computation_performed": False,
            "optimizer_step_performed": False,
        },
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "feature_semantics_reopened": False,
        "stale_feature_semantics_blocker_count": 0,
        "global_training_readiness_adjudicated_by_this_stage": False,
        "family_dependent_classification_target_available_event_count": 0,
        "PX5_empty_linker_human_label_preserved": True,
        "PX5_five_mask_runtime_compatible_at_label_snapshot": False,
        "PX5_mask_unavailable_event_count": 2,
        "batch001_successor_mask_runtime_binding_is_snapshot_scoped": True,
        "future_masking_runtime_successor_can_change_without_invalidating_snapshot": True,
        **mask_counts,
        "ready_for_gpt_review": True,
        "ready_for_model_integration_design": True,
        "ready_for_training": False,
        "ready_for_training_reason": (
            "THIS_LABEL_AVAILABILITY_STAGE_DOES_NOT_AUTHORIZE_TRAINING"
        ),
        "recommended_next_step_exactly": (
            "new_codex_conversation_design_empty_linker_compatible_five_module_"
            "model_integration_v1"
        ),
    }
    reject_stale_feature_semantics_claims_v1(manifest)
    manifest_payload = _json_bytes(manifest)
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "batch001_completed_decision_successor_built": True,
        "predecessor_human_overlay_modified": False,
        "predecessor_human_progress_modified": False,
        "completed_unit_snapshot_count": 9,
        "completed_event_snapshot_count": 37,
        "completed_positive_unit_count": 5,
        "completed_positive_event_count": 13,
        "completed_negative_unit_count": 4,
        "completed_negative_event_count": 24,
        "ONL_ingested": False,
        "ONL_held_out_event_count": 9,
        "task_label_matrix_row_count": 37,
        "positive_generative_supervision_eligible_event_count": 13,
        "reactive_pair_label_available_event_count": 13,
        "warhead_atom_set_label_available_event_count": 13,
        "role_partition_label_available_event_count": 13,
        "post_geometry_label_available_event_count": 13,
        "approved_canonical_reaction_family_target_available_event_count": 0,
        "approved_family_target_available_event_count": 0,
        "family_dependent_classification_target_available_event_count": 0,
        "warhead_type_classification_available_event_count": 0,
        "proposed_family_label_used_as_training_target": False,
        "stale_feature_semantics_blockers_removed": True,
        "current_feature_semantics_resolution_bound": True,
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "feature_semantics_reopened": False,
        "stale_feature_semantics_blocker_count": 0,
        "global_training_readiness_adjudicated_by_this_stage": False,
        "snapshot_byte_identical_to_pre_revision": True,
        "matrix_byte_identical_to_pre_revision": True,
        "PX5_empty_linker_human_label_preserved": True,
        "PX5_five_mask_runtime_compatible_at_label_snapshot": False,
        "PX5_mask_unavailable_event_count": 2,
        "PX5_mask_incompatible_at_label_snapshot_event_count": 2,
        "batch001_successor_mask_runtime_binding_is_snapshot_scoped": True,
        "future_masking_runtime_successor_can_change_without_invalidating_snapshot": True,
        "snapshot_mask_A_available_event_count": mask_counts[
            "mask_A_available_event_count"
        ],
        "snapshot_mask_B_available_event_count": mask_counts[
            "mask_B_available_event_count"
        ],
        "snapshot_mask_B2_available_event_count": mask_counts[
            "mask_B2_available_event_count"
        ],
        "snapshot_mask_B3_available_event_count": mask_counts[
            "mask_B3_available_event_count"
        ],
        "snapshot_mask_C_available_event_count": mask_counts[
            "mask_C_available_event_count"
        ],
        **mask_counts,
        "family_authority_created": False,
        "production_authority_created": False,
        "batch_002_created": False,
        "tensorization_performed": False,
        "training_performed": False,
        "repository_existing_files_modified": False,
        "network_performed": False,
        "artifact_sha256_excluding_summary": {
            SNAPSHOT: _sha256(snapshot_payload),
            MATRIX: _sha256(matrix_payload),
            MANIFEST: _sha256(manifest_payload),
        },
        "ready_for_gpt_review": True,
        "ready_for_model_integration_design": True,
        "ready_for_training": False,
        "ready_for_training_reason": (
            "THIS_LABEL_AVAILABILITY_STAGE_DOES_NOT_AUTHORIZE_TRAINING"
        ),
        "precommit_candidate_profile_supported": True,
        "published_clean_descendant_profile_supported": True,
        "recommended_next_step_exactly": manifest["recommended_next_step_exactly"],
    }
    reject_stale_feature_semantics_claims_v1(summary)
    return {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        MANIFEST: manifest_payload,
        SUMMARY: _json_bytes(summary),
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_v1(
    repo_root: Path, *, batch_root: Path | None = None
) -> dict[str, bytes]:
    artifacts = build_artifacts_v1(repo_root, batch_root=batch_root)
    output_root = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    if output_root.exists():
        unexpected = {
            path.name for path in output_root.iterdir() if path.name not in OUTPUT_FILENAMES
        }
        if unexpected:
            raise ValueError("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
    for name in OUTPUT_FILENAMES:
        _atomic_write(output_root / name, artifacts[name])
    return artifacts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    arguments = parser.parse_args(argv)
    artifacts = materialize_v1(arguments.repo_root)
    print("batch001_completed_decision_successor_built=true")
    print("completed_unit_snapshot_count=9")
    print("completed_event_snapshot_count=37")
    print("task_label_matrix_row_count=37")
    print("artifact_count=" + str(len(artifacts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
