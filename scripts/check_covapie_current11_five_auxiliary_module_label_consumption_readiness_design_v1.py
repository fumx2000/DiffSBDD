#!/usr/bin/env python3
"""Check the in-memory five-auxiliary-module readiness design."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from covalent_ext import (
    covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1
    as subject,
)


def _load_unified_checker(repo_root: Path):
    path = (
        repo_root
        / "scripts/check_covapie_current11_unified_effective_authority_view_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "unified_checker_for_auxiliary_readiness_checker", path
    )
    if specification is None or specification.loader is None:
        raise AssertionError("unified checker unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _synthetic_view(repo_root: Path) -> bytes:
    checker = _load_unified_checker(repo_root)
    inputs = checker._synthetic_inputs(repo_root)
    return checker._build(repo_root, inputs)


def _evaluate(repo_root: Path, payload: bytes) -> dict[str, Any]:
    return subject._reference_design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1(
        source_unified_effective_authority_view=payload,
        repo_root=repo_root,
    )


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _check(repo_root: Path) -> dict[str, Any]:
    # Synthetic predecessor construction is deliberately outside evaluator calls.
    source = _synthetic_view(repo_root)
    source_value = json.loads(source)
    source_snapshot = bytes(source)
    source_object_snapshot = json.loads(source)
    source_sha = hashlib.sha256(source).hexdigest()
    internal_sha = source_value["unified_effective_authority_view_sha256"]

    tracked_files = tuple(sorted(
        path
        for directory in ("src", "tests", "scripts", "docs")
        for path in (repo_root / directory).rglob("*")
        if path.is_file()
    ))
    file_snapshot = tuple(
        (path, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in tracked_files
    )
    model_paths = (
        repo_root / "lightning_modules.py",
        repo_root / "equivariant_diffusion/dynamics.py",
        repo_root / "equivariant_diffusion/en_diffusion.py",
    )
    loader_paths = (
        repo_root / "dataset.py",
        repo_root / "data/prepare_crossdocked.py",
    )
    model_snapshot = tuple(path.read_bytes() for path in model_paths)
    loader_snapshot = tuple(path.read_bytes() for path in loader_paths)
    writes = 0
    original_identity = (
        subject._FORMAL_VIEW_FILESYSTEM_SHA256,
        subject._FORMAL_VIEW_INTERNAL_SHA256,
    )
    path_writes = {
        name: getattr(Path, name)
        for name in ("write_bytes", "write_text", "touch", "mkdir")
    }

    def forbidden_write(*_args: object, **_kwargs: object) -> None:
        nonlocal writes
        writes += 1
        raise AssertionError("filesystem write attempted")

    try:
        # The production evaluator remains pinned to the formal identity.  The
        # checker substitutes only the independently constructed synthetic one.
        subject._FORMAL_VIEW_FILESYSTEM_SHA256 = source_sha
        subject._FORMAL_VIEW_INTERNAL_SHA256 = internal_sha
        for name in path_writes:
            setattr(Path, name, forbidden_write)
        first = _evaluate(repo_root, source)
        second = _evaluate(repo_root, source)
    finally:
        (
            subject._FORMAL_VIEW_FILESYSTEM_SHA256,
            subject._FORMAL_VIEW_INTERNAL_SHA256,
        ) = original_identity
        for name, method in path_writes.items():
            setattr(Path, name, method)

    signals = first["signal_readiness_records"]
    modules = first["module_readiness_records"]
    signal_by_name = {record["signal_name"]: record for record in signals}
    source_records = source_value["effective_authority_records"]
    legacy_count = sum(
        record["effective_authority_namespace"] == subject._LEGACY_NAMESPACE
        for record in source_records
    )
    multi_count = sum(
        record["effective_authority_namespace"] == subject._MULTI_NAMESPACE
        for record in source_records
    )
    current_files = tuple(sorted(
        path
        for directory in ("src", "tests", "scripts", "docs")
        for path in (repo_root / directory).rglob("*")
        if path.is_file()
    ))
    files_written = writes != 0 or file_snapshot != tuple(
        (path, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in current_files
    )
    model_modified = model_snapshot != tuple(
        path.read_bytes() for path in model_paths
    )
    loader_modified = loader_snapshot != tuple(
        path.read_bytes() for path in loader_paths
    )
    deterministic = first == second
    inputs_unchanged = (
        source == source_snapshot and json.loads(source) == source_object_snapshot
    )

    assert tuple(source_value) == subject.unified_view.EXACT16_VIEW_FIELDS
    assert len(source_records) == 11 and (legacy_count, multi_count) == (6, 5)
    assert len(signals) == 8 and len(modules) == 5
    assert tuple(record["signal_name"] for record in signals) == (
        subject._SIGNAL_NAMES
    )
    assert tuple(record["module_name"] for record in modules) == (
        subject._MODULE_NAMES
    )
    assert all(record["implementation_allowed"] is False for record in modules)
    assert all(record["training_allowed"] is False for record in modules)
    assert first["implementation_ready_module_count"] == 0
    assert first["ready_for_model_module_implementation"] is False
    assert deterministic and inputs_unchanged
    assert not files_written and not model_modified and not loader_modified
    assert signal_by_name["warhead_type_identity"][
        "authoritative_sample_coverage"
    ] == "11/11"
    assert signal_by_name["warhead_atom_set"][
        "authoritative_sample_coverage"
    ] == "11/11"
    assert signal_by_name["ligand_internal_warhead_boundary"][
        "authoritative_sample_coverage"
    ] == "11/11"
    assert "ligand_atom_to_residue_atom_pair" in signal_by_name[
        "ligand_internal_warhead_boundary"
    ]["forbidden_interpretations"]

    return {
        "source_view_field_count": len(source_value),
        "source_effective_record_count": len(source_records),
        "source_legacy_count": legacy_count,
        "source_multi_count": multi_count,
        "warhead_type_coverage": 11,
        "warhead_atom_set_coverage": 11,
        "ligand_internal_boundary_coverage": 11,
        "target_residue_atom_condition_status": signal_by_name[
            "target_residue_atom_condition"
        ]["readiness_status"],
        "ligand_residue_pair_status": signal_by_name[
            "ligand_atom_to_residue_atom_pair"
        ]["readiness_status"],
        "pre_post_geometry_status": signal_by_name[
            "pre_post_covalent_geometry"
        ]["readiness_status"],
        "scaffold_linker_anchor_status": signal_by_name[
            "scaffold_linker_anchor_atom_roles"
        ]["readiness_status"],
        "contrastive_sampling_status": signal_by_name[
            "contrastive_negative_sampling_policy"
        ]["readiness_status"],
        "canonical_mask_contract_source_path": str(
            subject._MASK_CONTRACT_SOURCE_PATH
        ),
        "canonical_mask_contract_source_sha256": (
            subject._MASK_CONTRACT_SOURCE_SHA256
        ),
        "canonical_mask_names": first["canonical_mask_names"],
        "canonical_mask_aliases": first["canonical_mask_aliases"],
        "ligand_internal_boundary_is_not_ligand_residue_covalent_pair": True,
        "lineage_only_field_paths": subject._LINEAGE_ONLY_FIELD_PATHS,
        "module_count": len(modules),
        "partial_foundation_module_count": sum(
            record["readiness_status"] == "partial_foundation_only"
            for record in modules
        ),
        "blocked_module_count": sum(
            record["readiness_status"] == "blocked_missing_canonical_labels"
            for record in modules
        ),
        "implementation_ready_module_count": first[
            "implementation_ready_module_count"
        ],
        "ready_for_model_module_implementation": first[
            "ready_for_model_module_implementation"
        ],
        "deterministic": deterministic,
        "inputs_unchanged": inputs_unchanged,
        "files_written": files_written,
        "model_files_modified": model_modified,
        "data_loader_modified": loader_modified,
        "forward_modified": model_modified,
        "loss_modified": model_modified,
        "training_label_created": False,
        "signal_record_sha256s": tuple(
            record["signal_readiness_record_sha256"] for record in signals
        ),
        "module_record_sha256s": tuple(
            record["module_readiness_record_sha256"] for record in modules
        ),
        "design_response_sha256": first["design_response_sha256"],
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    result = _check(repo_root)
    for key, value in result.items():
        if type(value) is bool:
            rendered = _bool(value)
        elif isinstance(value, tuple):
            rendered = json.dumps(value, separators=(",", ":"))
        else:
            rendered = str(value)
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
