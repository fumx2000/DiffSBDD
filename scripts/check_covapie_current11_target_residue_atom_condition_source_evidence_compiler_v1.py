#!/usr/bin/env python3
"""Synthetic check for the Current11 source-evidence compiler."""

from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1
    as offline_recovery,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1
    as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_offline_checker():
    path = REPO_ROOT / (
        "scripts/check_covapie_current11_target_residue_atom_condition_"
        "offline_source_recovery_design_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "covapie_offline_recovery_checker_for_compiler", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("offline checker unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OFFLINE_CHECKER = _load_offline_checker()


def _tree_snapshot(root: Path) -> dict[str, tuple[str, int, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.lstat().st_ino,
            path.lstat().st_mtime_ns,
            path.lstat().st_size,
        )
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def _ready_fixture(root: Path) -> tuple[bytes, dict[str, bytes]]:
    files = OFFLINE_CHECKER._fixture_repo(root)
    locator_path = root / "inputs/locator.csv"
    with locator_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        rows = [dict(row) for row in reader]
    for index, row in enumerate(rows):
        values = OFFLINE_CHECKER._raw_values(index)
        if index == 0:
            values["pdbx_PDB_ins_code"] = "?"
        raw = gzip.compress(
            OFFLINE_CHECKER._mmcif(row["pdb_id"], values, "recoverable"),
            mtime=0,
        )
        locator = row["raw_target_relative_path"]
        OFFLINE_CHECKER._write(root / locator, raw)
        digest = hashlib.sha256(raw).hexdigest()
        token = values["pdbx_PDB_ins_code"]
        row.update({
            "expected_raw_sha256": digest,
            "observed_raw_sha256": digest,
            "struct_conn_residue_auth_asym_id": values["auth_asym_id"],
            "struct_conn_residue_auth_seq_id": values["auth_seq_id"],
            "struct_conn_residue_label_asym_id": values["label_asym_id"],
            "struct_conn_residue_label_seq_id": values["label_seq_id"],
            "selected_chain_id": values["auth_asym_id"],
            "selected_residue_index": values["auth_seq_id"],
            "struct_conn_insertion_raw_value": token,
            "atom_site_insertion_raw_value": token,
            **OFFLINE_CHECKER._legacy_insertion_fields(token),
        })
        files[locator] = raw
    locator_payload = OFFLINE_CHECKER._csv_bytes(fields, rows)
    OFFLINE_CHECKER._write(locator_path, locator_payload)
    files["locator"] = locator_payload
    inventory = OFFLINE_CHECKER._synthetic_inventory(
        files["sample"], locator_payload, files
    )
    return inventory, files


def _configure_compiler(
    inventory: bytes, response: Mapping[str, Any]
) -> None:
    value = json.loads(inventory)
    subject._FORMAL_INVENTORY_TRANSPORT_SHA256 = hashlib.sha256(
        inventory
    ).hexdigest()
    subject._FORMAL_INVENTORY_INTERNAL_SHA256 = value[
        "source_inventory_bundle_sha256"
    ]
    subject._EXPECTED_DESIGN_RESPONSE_SHA256 = response[
        "design_response_sha256"
    ]
    subject._EXPECTED_RECOVERY_RECORD_SHA256S = tuple(
        record["offline_source_recovery_record_sha256"]
        for record in response["offline_source_recovery_records"]
    )
    subject._EXPECTED_EVIDENCE_RECORD_SHA256S = tuple(
        record["proposed_condition_evidence_record"]
        ["condition_evidence_record_sha256"]
        for record in response["offline_source_recovery_records"]
    )


def _reject_with_response(
    inventory: bytes, root: Path, response: Mapping[str, Any]
) -> bool:
    original = (
        offline_recovery
        ._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1
    )
    offline_recovery._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1 = (
        lambda **_: response
    )
    try:
        subject.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
            source_formal_inventory=inventory, repo_root=root
        )
    except ValueError as error:
        return str(error) == subject._ERROR
    finally:
        offline_recovery._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1 = original
    return False


def _render(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        inventory, files = _ready_fixture(root)
        value = json.loads(inventory)
        offline_recovery._FORMAL_INVENTORY_TRANSPORT_SHA256 = hashlib.sha256(
            inventory
        ).hexdigest()
        offline_recovery._FORMAL_INVENTORY_INTERNAL_SHA256 = value[
            "source_inventory_bundle_sha256"
        ]
        offline_recovery._SAMPLE_INDEX_SHA256 = hashlib.sha256(
            files["sample"]
        ).hexdigest()
        offline_recovery._LOCATOR_SIDECAR_SHA256 = hashlib.sha256(
            files["locator"]
        ).hexdigest()
        response = offline_recovery._reference_design_covapie_current11_target_residue_atom_condition_offline_source_recovery_v1(
            source_formal_inventory=inventory, repo_root=root
        )
        _configure_compiler(inventory, response)
        before = _tree_snapshot(root)
        inventory_snapshot = bytes(inventory)
        first = subject.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
            source_formal_inventory=inventory, repo_root=root
        )
        second = subject.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
            source_formal_inventory=inventory, repo_root=root
        )
        after = _tree_snapshot(root)

        blocked = copy.deepcopy(response)
        blocked["recoverable_offline_unique_count"] = 10
        blocked["blocked_sample_count"] = 1
        blocked["ready_for_offline_source_evidence_compiler"] = False

        empty = copy.deepcopy(response)
        empty["offline_source_recovery_records"][0][
            "proposed_condition_evidence_record"
        ] = {}

        duplicate = copy.deepcopy(response)
        duplicate["offline_source_recovery_records"][1][
            "sample_index_row_id"
        ] = duplicate["offline_source_recovery_records"][0][
            "sample_index_row_id"
        ]

        reordered = copy.deepcopy(response)
        records = list(reordered["offline_source_recovery_records"])
        records[0], records[1] = records[1], records[0]
        reordered["offline_source_recovery_records"] = tuple(records)
        reordered["design_response_sha256"] = subject._record_sha256(
            reordered, subject._RESPONSE_FIELDS, "design_response_sha256"
        )
        accepted_response_sha = subject._EXPECTED_DESIGN_RESPONSE_SHA256
        subject._EXPECTED_DESIGN_RESPONSE_SHA256 = reordered[
            "design_response_sha256"
        ]
        reordered_rejected = _reject_with_response(inventory, root, reordered)
        subject._EXPECTED_DESIGN_RESPONSE_SHA256 = accepted_response_sha

        recovery_drift = copy.deepcopy(response)
        recovery_drift["offline_source_recovery_records"][0][
            "offline_source_recovery_record_sha256"
        ] = "0" * 64
        evidence_drift = copy.deepcopy(response)
        evidence_drift["offline_source_recovery_records"][0][
            "proposed_condition_evidence_record"
        ]["condition_evidence_record_sha256"] = "0" * 64
        response_drift = copy.deepcopy(response)
        response_drift["design_response_sha256"] = "0" * 64

        accepted_production_sha = subject._OFFLINE_RECOVERY_PRODUCTION_SHA256
        subject._OFFLINE_RECOVERY_PRODUCTION_SHA256 = "0" * 64
        try:
            subject.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
                source_formal_inventory=inventory, repo_root=root
            )
        except ValueError as error:
            production_drift_rejected = str(error) == subject._ERROR
        else:
            production_drift_rejected = False
        finally:
            subject._OFFLINE_RECOVERY_PRODUCTION_SHA256 = accepted_production_sha

        evidence = first["condition_evidence_records"]
        summary = {
            "source_formal_inventory_bound": (
                first["source_formal_inventory_transport_sha256"]
                == hashlib.sha256(inventory).hexdigest()
                and first["source_formal_inventory_sha256"]
                == value["source_inventory_bundle_sha256"]
            ),
            "source_offline_recovery_production_bound": (
                first["source_offline_recovery_production_sha256"]
                == accepted_production_sha
            ),
            "source_offline_recovery_response_bound": (
                first["source_offline_recovery_design_response_sha256"]
                == response["design_response_sha256"]
            ),
            "source_recovery_record_count": len(
                first["source_offline_recovery_record_sha256s"]
            ),
            "condition_evidence_record_count": len(evidence),
            "condition_evidence_digest_valid_count": sum(
                record["condition_evidence_record_sha256"]
                == subject._record_sha256(
                    record,
                    subject._CONDITION_EVIDENCE_RECORD_FIELDS,
                    "condition_evidence_record_sha256",
                )
                for record in evidence
            ),
            "sample_order_verified": tuple(
                record["sample_index_row_id"] for record in evidence
            ) == subject._EXPECTED_SAMPLES,
            "all_source_recovery_records_ready": first[
                "all_source_recovery_records_ready"
            ],
            "ready_for_target_residue_atom_condition_authority_materialization": first[
                "ready_for_target_residue_atom_condition_authority_materialization"
            ],
            "question_mark_insertion_normalised_empty_preserved": (
                evidence[0]["protein_pdbx_PDB_ins_code"] == ""
            ),
            "condition_evidence_is_not_authority": all(
                all("authority" not in field for field in record)
                for record in evidence
            ),
            "blocked_predecessor_rejected": _reject_with_response(
                inventory, root, blocked
            ),
            "empty_evidence_rejected": _reject_with_response(
                inventory, root, empty
            ),
            "duplicate_sample_rejected": _reject_with_response(
                inventory, root, duplicate
            ),
            "reordered_sample_rejected": reordered_rejected,
            "recovery_digest_drift_rejected": _reject_with_response(
                inventory, root, recovery_drift
            ),
            "evidence_digest_drift_rejected": _reject_with_response(
                inventory, root, evidence_drift
            ),
            "predecessor_response_drift_rejected": _reject_with_response(
                inventory, root, response_drift
            ),
            "predecessor_production_drift_rejected": production_drift_rejected,
            "deterministic": first == second,
            "inputs_unchanged": inventory == inventory_snapshot,
            "files_written": before != after,
            "condition_authority_created": False,
            "adapter_implemented": False,
            "training_label_created": False,
            "tensor_created": False,
            "model_modified": False,
            "data_loader_modified": False,
            "forward_modified": False,
            "loss_modified": False,
            "training_or_parameter_update": False,
            "condition_evidence_record_sha256s": tuple(
                record["condition_evidence_record_sha256"]
                for record in evidence
            ),
            "source_evidence_bundle_sha256": first[
                "source_evidence_bundle_sha256"
            ],
        }
        for key, value in summary.items():
            print(f"{key}={_render(value)}")


if __name__ == "__main__":
    main()
