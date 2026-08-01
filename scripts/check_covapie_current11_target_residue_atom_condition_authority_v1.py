#!/usr/bin/env python3
"""Synthetic fail-closed check for the Current11 condition authority."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from covalent_ext import (
    covapie_current11_target_residue_atom_condition_offline_source_recovery_design_v1
    as offline_recovery,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_source_evidence_compiler_v1
    as evidence_compiler,
)
from covalent_ext import (
    covapie_current11_target_residue_atom_condition_authority_v1 as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_source_checker():
    path = REPO_ROOT / (
        "scripts/check_covapie_current11_target_residue_atom_condition_"
        "source_evidence_compiler_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "source_evidence_checker_for_authority", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("source-evidence checker unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE_CHECKER = _load_source_checker()
OFFLINE_CHECKER = SOURCE_CHECKER.OFFLINE_CHECKER


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


def _configure_authority(
    inventory: bytes,
    evidence: Mapping[str, Any],
    response: Mapping[str, Any],
) -> None:
    inventory_value = json.loads(inventory)
    evidence_bytes = evidence_compiler._bundle_bytes(evidence)
    subject._FORMAL_INVENTORY_TRANSPORT_SHA256 = hashlib.sha256(
        inventory
    ).hexdigest()
    subject._FORMAL_INVENTORY_INTERNAL_SHA256 = inventory_value[
        "source_inventory_bundle_sha256"
    ]
    subject._SOURCE_EVIDENCE_BUNDLE_TRANSPORT_SHA256 = hashlib.sha256(
        evidence_bytes
    ).hexdigest()
    subject._SOURCE_EVIDENCE_BUNDLE_INTERNAL_SHA256 = evidence[
        "source_evidence_bundle_sha256"
    ]
    subject._OFFLINE_RECOVERY_RESPONSE_SHA256 = response["design_response_sha256"]
    subject._EXPECTED_RECOVERY_RECORD_SHA256S = tuple(
        record["offline_source_recovery_record_sha256"]
        for record in response["offline_source_recovery_records"]
    )
    subject._EXPECTED_EVIDENCE_RECORD_SHA256S = tuple(
        record["condition_evidence_record_sha256"]
        for record in evidence["condition_evidence_records"]
    )
    subject._CONTRACT_DESIGN_VERSION = inventory_value[
        "source_contract_design_version"
    ]
    subject._CONTRACT_DESIGN_PRODUCTION_SHA256 = inventory_value[
        "source_contract_design_production_sha256"
    ]
    subject._CONTRACT_DESIGN_RESPONSE_SHA256 = inventory_value[
        "source_contract_design_response_sha256"
    ]


def _ready_fixture(
    root: Path,
) -> tuple[bytes, dict[str, Any], bytes, dict[str, Any]]:
    inventory, files = SOURCE_CHECKER._ready_fixture(root)
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
    SOURCE_CHECKER._configure_compiler(inventory, response)
    evidence = evidence_compiler.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
        source_formal_inventory=inventory, repo_root=root
    )
    evidence_bytes = evidence_compiler._bundle_bytes(evidence)
    _configure_authority(inventory, evidence, response)
    return inventory, evidence, evidence_bytes, response


def _build(inventory: bytes, evidence_bytes: bytes, root: Path) -> dict[str, Any]:
    return subject.build_covapie_current11_target_residue_atom_condition_authority_v1(
        source_formal_inventory=inventory,
        source_evidence_bundle=evidence_bytes,
        repo_root=root,
    )


def _canonical_rejected(call: Callable[[], object]) -> bool:
    try:
        call()
    except ValueError as error:
        return str(error) == subject._ERROR
    return False


def _first_raw_path(root: Path, response: Mapping[str, Any]) -> Path:
    locator = response["offline_source_recovery_records"][0]["selected_raw_locator"]
    return root / locator


def _rewrite_first_raw(
    root: Path,
    response: Mapping[str, Any],
    *,
    changes: Mapping[str, str] | None = None,
    scenario: str = "recoverable",
) -> None:
    values = OFFLINE_CHECKER._raw_values(0)
    values["pdbx_PDB_ins_code"] = "?"
    values.update(changes or {})
    raw = gzip.compress(
        OFFLINE_CHECKER._mmcif("T001", values, scenario), mtime=0
    )
    _first_raw_path(root, response).write_bytes(raw)


def _raw_rejected(
    mutation: Callable[[Path, Mapping[str, Any]], None],
) -> bool:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        inventory, _, evidence_bytes, response = _ready_fixture(root)
        mutation(root, response)
        return _canonical_rejected(lambda: _build(inventory, evidence_bytes, root))


def _missing_raw(root: Path, response: Mapping[str, Any]) -> None:
    _first_raw_path(root, response).unlink()


def _sha_drift(root: Path, response: Mapping[str, Any]) -> None:
    path = _first_raw_path(root, response)
    path.write_bytes(path.read_bytes() + b"drift")


def _atom_missing(root: Path, response: Mapping[str, Any]) -> None:
    _rewrite_first_raw(root, response, changes={"id": "999999"})


def _atom_ambiguous(root: Path, response: Mapping[str, Any]) -> None:
    _rewrite_first_raw(root, response, scenario="ambiguous")


def _auth_drift(root: Path, response: Mapping[str, Any]) -> None:
    _rewrite_first_raw(root, response, changes={"auth_asym_id": "B"})


def _type_drift(root: Path, response: Mapping[str, Any]) -> None:
    _rewrite_first_raw(root, response, changes={"type_symbol": "C"})


def _label_drift(root: Path, response: Mapping[str, Any]) -> None:
    _rewrite_first_raw(root, response, changes={"label_comp_id": "MSE"})


def _altloc_source_token_rejected(
    evidence: Mapping[str, Any],
    root: Path,
    response: Mapping[str, Any],
    raw_altloc: str,
) -> bool:
    recovery = response["offline_source_recovery_records"][0]
    locator = recovery["selected_raw_locator"]
    path = _first_raw_path(root, response)
    _, _, rows = offline_recovery._parse_atom_site(
        offline_recovery._decode_raw(path.read_bytes(), locator)
    )
    row = dict(next(row for row in rows if row["_atom_site.id"] == "1000"))
    row["_atom_site.label_alt_id"] = raw_altloc
    return _canonical_rejected(
        lambda: subject._authority_record(
            evidence["condition_evidence_records"][0], row
        )
    )


def _render(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        inventory, evidence, evidence_bytes, response = _ready_fixture(root)
        before = _tree_snapshot(root)
        inventory_snapshot = bytes(inventory)
        evidence_snapshot = bytes(evidence_bytes)
        first = _build(inventory, evidence_bytes, root)
        second = _build(inventory, evidence_bytes, root)
        after = _tree_snapshot(root)
        records = first["target_residue_atom_condition_records"]

        source_drift = _canonical_rejected(
            lambda: _build(inventory, evidence_bytes[:-1] + b"0", root)
        )
        original_contract = subject._CONTRACT_DESIGN_PRODUCTION_SHA256
        subject._CONTRACT_DESIGN_PRODUCTION_SHA256 = "0" * 64
        try:
            contract_drift = _canonical_rejected(
                lambda: _build(inventory, evidence_bytes, root)
            )
        finally:
            subject._CONTRACT_DESIGN_PRODUCTION_SHA256 = original_contract

        output = {
            "source_formal_inventory_bound": first[
                "source_formal_inventory_transport_sha256"
            ]
            == hashlib.sha256(inventory).hexdigest(),
            "source_evidence_compiler_production_bound": first[
                "source_evidence_compiler_production_sha256"
            ]
            == subject._SOURCE_EVIDENCE_COMPILER_PRODUCTION_SHA256,
            "source_evidence_bundle_transport_bound": first[
                "source_evidence_bundle_transport_sha256"
            ]
            == hashlib.sha256(evidence_bytes).hexdigest(),
            "source_evidence_bundle_internal_bound": first[
                "source_evidence_bundle_sha256"
            ]
            == evidence["source_evidence_bundle_sha256"],
            "source_evidence_bundle_recompiled_exact": evidence_compiler._bundle_bytes(
                evidence_compiler.compile_covapie_current11_target_residue_atom_condition_source_evidence_v1(
                    source_formal_inventory=inventory, repo_root=root
                )
            )
            == evidence_bytes,
            "source_offline_recovery_response_bound": first[
                "source_offline_recovery_design_response_sha256"
            ]
            == response["design_response_sha256"],
            "source_condition_contract_production_bound": first[
                "source_condition_contract_design_production_sha256"
            ]
            == json.loads(inventory)["source_contract_design_production_sha256"],
            "source_condition_contract_response_bound": first[
                "source_condition_contract_design_response_sha256"
            ]
            == json.loads(inventory)["source_contract_design_response_sha256"],
            "raw_structure_sha_revalidated_count": sum(
                bool(record["source_structure_filesystem_sha256"])
                for record in records
            ),
            "source_atom_site_unique_match_count": len(records),
            "evidence_auth_identity_match_count": len(records),
            "protein_type_symbol_observed_count": sum(
                record["protein_type_symbol"] == "S" for record in records
            ),
            "protein_label_alt_id_observed_count": len(records),
            "protein_label_crosswalk_observed_count": sum(
                all(
                    record[field]
                    for field in (
                        "protein_label_asym_id",
                        "protein_label_comp_id",
                        "protein_label_seq_id",
                        "protein_label_atom_id",
                    )
                )
                for record in records
            ),
            "target_residue_atom_condition_record_count": len(records),
            "resolved_authoritative_count": first["resolved_authoritative_count"],
            "authority_record_digest_valid_count": sum(
                record["target_residue_atom_condition_record_sha256"]
                == subject._record_sha256(
                    record,
                    subject.TARGET_RESIDUE_ATOM_CONDITION_RECORD_FIELDS,
                    "target_residue_atom_condition_record_sha256",
                )
                for record in records
            ),
            "all_records_resolved_authoritative": first[
                "all_records_resolved_authoritative"
            ],
            "ready_for_target_residue_atom_condition_adapter_design": first[
                "ready_for_target_residue_atom_condition_adapter_design"
            ],
            "missing_raw_rejected": _raw_rejected(_missing_raw),
            "raw_sha_drift_rejected": _raw_rejected(_sha_drift),
            "atom_site_missing_rejected": _raw_rejected(_atom_missing),
            "atom_site_ambiguous_rejected": _raw_rejected(_atom_ambiguous),
            "auth_identity_drift_rejected": _raw_rejected(_auth_drift),
            "type_symbol_drift_rejected": _raw_rejected(_type_drift),
            "label_crosswalk_drift_rejected": _raw_rejected(_label_drift),
            "source_evidence_drift_rejected": source_drift,
            "contract_production_drift_rejected": contract_drift,
            "partial_authority_rejected": _raw_rejected(_missing_raw),
            "empty_altloc_source_token_rejected": _altloc_source_token_rejected(
                evidence, root, response, ""
            ),
            "whitespace_altloc_source_token_rejected": _altloc_source_token_rejected(
                evidence, root, response, " "
            ),
            "deterministic": first == second,
            "inputs_unchanged": inventory == inventory_snapshot
            and evidence_bytes == evidence_snapshot,
            "files_written": before != after,
            "adapter_implemented": False,
            "training_label_created": False,
            "tensor_created": False,
            "model_modified": False,
            "data_loader_modified": False,
            "forward_modified": False,
            "loss_modified": False,
            "training_or_parameter_update": False,
            "target_residue_atom_condition_record_sha256s": tuple(
                record["target_residue_atom_condition_record_sha256"]
                for record in records
            ),
            "target_residue_atom_condition_authority_bundle_sha256": first[
                "target_residue_atom_condition_authority_bundle_sha256"
            ],
        }
        required_true = tuple(
            key
            for key, value in output.items()
            if key not in {
                "files_written",
                "adapter_implemented",
                "training_label_created",
                "tensor_created",
                "model_modified",
                "data_loader_modified",
                "forward_modified",
                "loss_modified",
                "training_or_parameter_update",
                "target_residue_atom_condition_record_sha256s",
                "target_residue_atom_condition_authority_bundle_sha256",
            }
            and isinstance(value, bool)
        )
        if (
            not all(output[key] is True for key in required_true)
            or output["files_written"] is not False
            or any(
                output[key] is not False
                for key in (
                    "adapter_implemented",
                    "training_label_created",
                    "tensor_created",
                    "model_modified",
                    "data_loader_modified",
                    "forward_modified",
                    "loss_modified",
                    "training_or_parameter_update",
                )
            )
            or any(
                output[key] != 11
                for key in (
                    "raw_structure_sha_revalidated_count",
                    "source_atom_site_unique_match_count",
                    "evidence_auth_identity_match_count",
                    "protein_type_symbol_observed_count",
                    "protein_label_alt_id_observed_count",
                    "protein_label_crosswalk_observed_count",
                    "target_residue_atom_condition_record_count",
                    "resolved_authoritative_count",
                    "authority_record_digest_valid_count",
                )
            )
        ):
            raise RuntimeError("authority checker invariant failed")
        for key, value in output.items():
            print(f"{key}={_render(value)}")


if __name__ == "__main__":
    main()
