from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from covalent_ext import (
    covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1
    as subject,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_unified_checker():
    path = (
        REPO_ROOT
        / "scripts/check_covapie_current11_unified_effective_authority_view_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "unified_checker_for_auxiliary_readiness_tests", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def synthetic_view() -> bytes:
    checker = _load_unified_checker()
    inputs = checker._synthetic_inputs(REPO_ROOT)
    return checker._build(REPO_ROOT, inputs)


@pytest.fixture(autouse=True)
def synthetic_identity(monkeypatch: pytest.MonkeyPatch, synthetic_view: bytes):
    value = json.loads(synthetic_view)
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(synthetic_view).hexdigest(),
    )
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_INTERNAL_SHA256",
        value["unified_effective_authority_view_sha256"],
    )


def _evaluate(payload: bytes) -> dict[str, Any]:
    return subject._reference_design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1(
        source_unified_effective_authority_view=payload,
        repo_root=REPO_ROOT,
    )


def _ordered_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _rehash_view(value: dict[str, Any]) -> bytes:
    for record in value["effective_authority_records"]:
        record["unified_effective_authority_record_sha256"] = (
            subject._record_sha256(
                record,
                subject.unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS,
                "unified_effective_authority_record_sha256",
            )
        )
    value["unified_effective_authority_view_sha256"] = subject._record_sha256(
        value,
        subject.unified_view.EXACT16_VIEW_FIELDS,
        "unified_effective_authority_view_sha256",
    )
    return _ordered_bytes(value)


def _accept_test_identity(
    monkeypatch: pytest.MonkeyPatch, payload: bytes
) -> None:
    value = json.loads(payload)
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_INTERNAL_SHA256",
        value["unified_effective_authority_view_sha256"],
    )


def test_private_module_import_is_silent_and_exports_nothing() -> None:
    assert subject.__all__ == ()
    assert not hasattr(
        subject,
        "design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1",
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "from covalent_ext import "
                "covapie_current11_five_auxiliary_module_label_consumption_"
                "readiness_design_v1"
            ),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_exact_response_records_and_digests(synthetic_view: bytes) -> None:
    response = _evaluate(synthetic_view)
    assert tuple(response) == subject._RESPONSE_FIELDS
    assert len(response) == 10
    assert response["design_response_sha256"] == subject._record_sha256(
        response, subject._RESPONSE_FIELDS, "design_response_sha256"
    )
    signals = response["signal_readiness_records"]
    modules = response["module_readiness_records"]
    assert type(signals) is tuple and len(signals) == 8
    assert type(modules) is tuple and len(modules) == 5
    for record in signals:
        assert tuple(record) == subject._SIGNAL_FIELDS
        assert len(record) == 10
        assert record["signal_readiness_record_sha256"] == (
            subject._record_sha256(
                record,
                subject._SIGNAL_FIELDS,
                "signal_readiness_record_sha256",
            )
        )
    for record in modules:
        assert tuple(record) == subject._MODULE_FIELDS
        assert len(record) == 11
        assert record["module_readiness_record_sha256"] == (
            subject._record_sha256(
                record,
                subject._MODULE_FIELDS,
                "module_readiness_record_sha256",
            )
        )


def test_source_profile_and_strict_embedded_validation(
    synthetic_view: bytes,
) -> None:
    view = subject._validate_unified_view(synthetic_view)
    records = view["effective_authority_records"]
    assert tuple(view) == subject.unified_view.EXACT16_VIEW_FIELDS
    assert all(
        tuple(record) == subject.unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS
        for record in records
    )
    assert tuple(record["sample_index_row_id"] for record in records) == (
        subject._EXPECTED_SAMPLES
    )
    assert sum(
        record["effective_authority_namespace"] == subject._LEGACY_NAMESPACE
        for record in records
    ) == 6
    assert sum(
        record["effective_authority_namespace"] == subject._MULTI_NAMESPACE
        for record in records
    ) == 5
    assert all(
        record["source_authority_record_sha256"]
        in {
            record["effective_authority_record"].get(
                "authority_record_sha256", ""
            ),
            record["effective_authority_record"].get(
                "multi_boundary_authority_record_sha256", ""
            ),
        }
        for record in records
    )


def test_canonical_mask_contract_includes_exactly_b3(
    synthetic_view: bytes,
) -> None:
    response = _evaluate(synthetic_view)
    assert response["canonical_mask_names"] == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    assert response["canonical_mask_aliases"] == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
    source = REPO_ROOT / subject._MASK_CONTRACT_SOURCE_PATH
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        subject._MASK_CONTRACT_SOURCE_SHA256
    )


def test_signal_order_coverage_and_readiness(synthetic_view: bytes) -> None:
    signals = _evaluate(synthetic_view)["signal_readiness_records"]
    assert tuple(record["signal_name"] for record in signals) == (
        subject._SIGNAL_NAMES
    )
    by_name = {record["signal_name"]: record for record in signals}
    assert by_name["warhead_type_identity"]["authoritative_sample_coverage"] == (
        "11/11"
    )
    assert by_name["warhead_type_identity"]["readiness_status"] == (
        "authority_ready_requires_vocabulary_audit"
    )
    assert by_name["warhead_atom_set"]["authoritative_sample_coverage"] == (
        "11/11"
    )
    assert by_name["warhead_atom_set"]["readiness_status"] == "authority_ready"
    boundary = by_name["ligand_internal_warhead_boundary"]
    assert boundary["authoritative_sample_coverage"] == "11/11"
    assert boundary["readiness_status"] == "authority_ready"
    assert "ligand_atom_to_residue_atom_pair" in boundary[
        "forbidden_interpretations"
    ]
    assert by_name["target_residue_atom_condition"]["readiness_status"] == (
        "partial_requires_additional_contract"
    )
    assert by_name["ligand_atom_to_residue_atom_pair"]["readiness_status"] == (
        "absent_requires_new_authority"
    )
    assert by_name["pre_post_covalent_geometry"]["readiness_status"] == (
        "absent_requires_new_authority"
    )
    assert by_name["scaffold_linker_anchor_atom_roles"]["readiness_status"] == (
        "partial_requires_additional_contract"
    )
    assert by_name["contrastive_negative_sampling_policy"][
        "readiness_status"
    ] == "absent_requires_new_authority"


def test_module_order_dependencies_and_all_implementation_blocked(
    synthetic_view: bytes,
) -> None:
    response = _evaluate(synthetic_view)
    modules = response["module_readiness_records"]
    assert tuple(record["module_name"] for record in modules) == (
        subject._MODULE_NAMES
    )
    assert tuple(record["readiness_status"] for record in modules) == (
        "partial_foundation_only",
        "partial_foundation_only",
        "blocked_missing_canonical_labels",
        "blocked_missing_canonical_labels",
        "blocked_missing_canonical_labels",
    )
    assert tuple(record["next_required_contract"] for record in modules) == (
        "design_covapie_target_residue_atom_condition_contract_v1",
        "design_covapie_scaffold_linker_anchor_role_authority_contract_v1",
        "design_covapie_ligand_residue_covalent_pair_label_contract_v1",
        "design_covapie_pre_post_covalent_geometry_label_contract_v1",
        "design_covapie_covalent_pair_contrastive_sampling_contract_v1",
    )
    contrastive = modules[-1]
    assert contrastive["required_signals"] == (
        "ligand_atom_to_residue_atom_pair",
        "contrastive_negative_sampling_policy",
    )
    assert all(record["implementation_allowed"] is False for record in modules)
    assert all(record["training_allowed"] is False for record in modules)
    assert all(
        record["feature_semantics_audit_required"] is True for record in modules
    )
    assert response["implementation_ready_module_count"] == 0
    assert response["ready_for_model_module_implementation"] is False


def test_lineage_only_paths_are_frozen_and_never_signal_sources(
    synthetic_view: bytes,
) -> None:
    assert type(subject._LINEAGE_ONLY_FIELD_PATHS) is tuple
    joined = "\n".join(subject._LINEAGE_ONLY_FIELD_PATHS)
    for category in (
        "source_*_sha256",
        "reviewer_id",
        "reviewer_provenance_attestor_id",
        "review_rationale_sha256",
        "review_notes_sha256",
        "review_decision",
        "authority_disposition",
        "precedence_reason",
        "authority_record_sha256",
        "resolution_record_sha256",
        "view_sha256",
        "submission_source_label",
    ):
        assert category in joined
    signals = _evaluate(synthetic_view)["signal_readiness_records"]
    assert all(record["source_is_audit_only"] is False for record in signals)
    assert not any(
        "precedence_reason" in path
        for record in signals
        for path in record["source_field_paths"]
    )


def test_deterministic_inputs_unchanged_and_zero_writes(
    synthetic_view: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = bytes(synthetic_view)
    writes: list[str] = []

    def forbidden_write(*_args: object, **_kwargs: object) -> None:
        writes.append("write")
        raise AssertionError("filesystem write attempted")

    for name in ("write_bytes", "write_text", "touch", "mkdir"):
        monkeypatch.setattr(Path, name, forbidden_write)
    first = _evaluate(synthetic_view)
    second = _evaluate(synthetic_view)
    assert first == second
    assert synthetic_view == snapshot
    assert writes == []


def test_model_loader_forward_loss_and_training_artifacts_are_untouched(
    synthetic_view: bytes,
) -> None:
    protected = (
        REPO_ROOT / "lightning_modules.py",
        REPO_ROOT / "dataset.py",
        REPO_ROOT / "equivariant_diffusion/dynamics.py",
        REPO_ROOT / "equivariant_diffusion/en_diffusion.py",
    )
    snapshots = tuple(path.read_bytes() for path in protected)
    label_paths_before = tuple(
        sorted(REPO_ROOT.glob("**/*training*label*.json"))
    )
    _evaluate(synthetic_view)
    assert snapshots == tuple(path.read_bytes() for path in protected)
    assert label_paths_before == tuple(
        sorted(REPO_ROOT.glob("**/*training*label*.json"))
    )
    subject_path = REPO_ROOT / "src/covalent_ext" / (
        "covapie_current11_five_auxiliary_module_label_consumption_"
        "readiness_design_v1.py"
    )
    tree = ast.parse(subject_path.read_text(encoding="utf-8"))
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not any(
        name.startswith(("torch", "numpy", "lightning_modules", "dataset"))
        or name.startswith("equivariant_diffusion")
        for name in imported_modules
    )
    assert called_attributes.isdisjoint(
        {"forward", "backward", "optimizer_step", "training_step"}
    )


@pytest.mark.parametrize(
    "malformed",
    (
        b"",
        b"{\"x\":1,\"x\":2}",
        b"\xef\xbb\xbf{}",
        b"{}\n",
        b"{\"x\":NaN}",
        b"{\"x\":\"\\u0000\"}",
        b"[]",
    ),
)
def test_malformed_source_view_rejected(
    malformed: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(malformed).hexdigest(),
    )
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        _evaluate(malformed)


def test_source_digest_drift_rejected(synthetic_view: bytes) -> None:
    drifted = bytearray(synthetic_view)
    drifted[-2] = ord("0") if drifted[-2] != ord("0") else ord("1")
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        _evaluate(bytes(drifted))


@pytest.mark.parametrize(
    "field",
    ("warhead_type_candidate_class_id", "reviewed_warhead_atom_ids"),
)
def test_required_authority_signal_field_missing_fails_closed(
    field: str,
    synthetic_view: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = json.loads(synthetic_view)
    authority = value["effective_authority_records"][0][
        "effective_authority_record"
    ]
    authority.pop(field)
    payload = _rehash_view(value)
    _accept_test_identity(monkeypatch, payload)
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        _evaluate(payload)


def test_internal_view_digest_mismatch_fails_closed(
    synthetic_view: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = json.loads(synthetic_view)
    value["effective_authority_record_count"] = 12
    payload = _ordered_bytes(value)
    monkeypatch.setattr(
        subject,
        "_FORMAL_VIEW_FILESYSTEM_SHA256",
        hashlib.sha256(payload).hexdigest(),
    )
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        _evaluate(payload)


def test_illegal_sixth_mask_fails_closed(
    synthetic_view: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        subject,
        "_CANONICAL_MASK_TASKS",
        (*subject._CANONICAL_MASK_TASKS, (5, "illegal_sixth", "D")),
    )
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        _evaluate(synthetic_view)


def test_canonical_serialization_failure_fails_closed(
    synthetic_view: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_args: object, **_kwargs: object) -> str:
        raise TypeError("synthetic serialization failure")

    monkeypatch.setattr(subject.json, "dumps", fail)
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        _evaluate(synthetic_view)


def test_exact_keyword_only_types_fail_closed(synthetic_view: bytes) -> None:
    with pytest.raises(TypeError):
        subject._reference_design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1(  # type: ignore[misc]
            synthetic_view, REPO_ROOT
        )
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._reference_design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1(
            source_unified_effective_authority_view=bytearray(synthetic_view),  # type: ignore[arg-type]
            repo_root=REPO_ROOT,
        )
    with pytest.raises(ValueError, match=f"^{subject._ERROR}$"):
        subject._reference_design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1(
            source_unified_effective_authority_view=synthetic_view,
            repo_root=str(REPO_ROOT),  # type: ignore[arg-type]
        )
