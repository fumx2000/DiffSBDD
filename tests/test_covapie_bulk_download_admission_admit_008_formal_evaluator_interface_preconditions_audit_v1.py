from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit as gate,
)


def _load_checker() -> object:
    path = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1.py"
    spec = importlib.util.spec_from_file_location("admit008_audit_checker", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _hashes(root: Path) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.iterdir()}


def _refresh_manifest_hash(root: Path, name: str) -> None:
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output_sha256"][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_csv(root: Path, name: str, mutate: object) -> None:
    path = root / name
    reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline=""))
    assert reader.fieldnames is not None
    rows = [dict(row) for row in reader]
    result = mutate(rows)  # type: ignore[operator]
    rows = rows if result is None else result
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(stream.getvalue(), encoding="utf-8")
    _refresh_manifest_hash(root, name)


def test_production_and_checker_imports_are_silent_and_side_effect_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    importlib.reload(gate)
    _load_checker()
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""
    assert not (tmp_path / gate.DEFAULT_OUTPUT_ROOT).exists()


def test_exact_six_outputs_are_byte_deterministic(tmp_path: Path) -> None:
    first = gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    first_hashes = _hashes(tmp_path)
    second = gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    assert first["manifest"] == second["manifest"]
    assert first_hashes == _hashes(tmp_path)
    assert tuple(sorted(first_hashes)) == tuple(sorted(gate.OUTPUT_FILES))


def test_exact15_source_boundary_is_ordered_tracked_and_sha_frozen() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert len(snapshot.records) == 15
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS


def test_all_structural_checks_precede_first_explicit_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_git = gate._git
    original_read = Path.read_bytes

    def structure(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:1] == ["show"] and len(list(arguments)) == 2:
            events.append("content:git_show")
        return original_git(arguments, root, text=text)  # type: ignore[arg-type]

    def read(path: Path) -> bytes:
        if path in tuple(REPO_ROOT / item for item in gate.SOURCE_PATHS):
            events.append("content:filesystem")
        return original_read(path)

    monkeypatch.setattr(gate, "_structural_source_check", structure)
    monkeypatch.setattr(gate, "_git", git)
    monkeypatch.setattr(Path, "read_bytes", read)
    gate.build_frozen_source_snapshot()
    first_content = next(index for index, event in enumerate(events) if event.startswith("content:"))
    assert events[:first_content] == [f"structure:{path}" for path in gate.SOURCE_PATHS]


def test_lineage_failure_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._git

    def git(arguments: object, root: Path, *, text: bool = True) -> subprocess.CompletedProcess[object]:
        if list(arguments)[:2] == ["merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess([], 1, "" if text else b"", "" if text else b"")
        return original(arguments, root, text=text)  # type: ignore[arg-type]

    monkeypatch.setattr(gate, "_git", git)
    with pytest.raises(ValueError, match="not an ancestor"):
        gate.build_frozen_source_snapshot()


@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_missing_or_symlink_source_fails_before_byte_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    target = gate.SOURCE_PATHS[0]
    full = tmp_path / target
    full.parent.mkdir(parents=True)
    if failure == "symlink":
        victim = tmp_path / "victim"
        victim.write_text("victim", encoding="utf-8")
        full.symlink_to(victim)
    monkeypatch.setattr(gate, "_validate_expected_base_lineage", lambda *args, **kwargs: None)
    monkeypatch.setattr(gate, "_structural_source_check", lambda path, root: path != target)
    called = False

    def forbidden(*args: object, **kwargs: object) -> bytes:
        nonlocal called
        called = True
        raise AssertionError("content read forbidden")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot(tmp_path)
    assert called is False


def test_exact20_preconditions_truthfully_freeze_only_identity_and_field() -> None:
    rows = gate._precondition_rows()
    assert len(rows) == 20
    assert [row["precondition_id"] for row in rows] == [f"PRE_{index:03d}" for index in range(1, 21)]
    assert [row["semantics_complete"] for row in rows] == ["true", "true"] + ["false"] * 18
    assert all(row["precondition_passed"] == "true" for row in rows)
    assert all(row["blocker_id"] == gate.PRIMARY_BLOCKER for row in rows[2:16])
    assert rows[16]["blocker_id"] == "REAL_PROVIDER_TOPOLOGY_DISPOSITION_MAPPING_UNVALIDATED"
    assert rows[19]["blocker_id"] == "FEATURE_SEMANTICS_AUDIT_REQUIRED"


def test_vocabulary_inventory_forbids_every_observed_string_promotion() -> None:
    rows = gate._vocabulary_rows()
    assert len(rows) == 22
    assert [row["vocabulary_order"] for row in rows] == [str(index) for index in range(1, 23)]
    assert all(row["candidate_scalar_value_explicitly_declared"] == "false" for row in rows)
    assert all(row["canonical_enum_member_explicitly_declared"] == "false" for row in rows)
    assert all(row["safe_to_promote_to_canonical_enum_now"] == "false" for row in rows)
    assert all(row["promotion_blocker"] == gate.PRIMARY_BLOCKER for row in rows)
    observed = {row["observed_string"] for row in rows}
    assert {
        "approved_template_or_manual_review", "approved_or_manual_review",
        "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1",
        "UNKNOWN_RESIDUE_WARHEAD_PAIR_QUARANTINE", "accepted", "quarantine_only",
    }.issubset(observed)
    assert not {"candidate_scalar_value", "canonical_enum_member"}.intersection(
        row["semantic_category"] for row in rows
    )


def test_occurrence_inventory_covers_every_required_term() -> None:
    rows = gate._occurrence_rows(gate.build_frozen_source_snapshot())
    assert len(rows) == 90
    assert [row["occurrence_order"] for row in rows] == [str(index) for index in range(1, 91)]
    assert {row["matched_term"] for row in rows} == set(gate.MATCH_TERMS)
    assert all(row["occurrence_passed"] == "true" for row in rows)
    assert any(row["authoritative_for_admit008_formal_semantics"] == "true" for row in rows)
    assert all(
        row["authoritative_for_admit008_formal_semantics"] == "false"
        for row in rows if row["matched_term"] in {
            "approved_template_or_manual_review", "approved_or_manual_review",
            "topology_restoration_unapproved", "restoration_rule_id", "restoration_rule_scope",
        }
    )


def test_exact11_issue_inventory_is_byte_identical_and_admit008_stays_open() -> None:
    state = gate.build_audit_state()
    assert len(state["issue_rows"]) == 11
    assert state["issue_bytes"] == (REPO_ROOT / gate.RUNTIME_ISSUE_PATH).read_bytes()
    enum_issue = next(row for row in state["issue_rows"] if row["issue_id"] == gate.PRIMARY_BLOCKER)
    coverage = next(row for row in state["issue_rows"] if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert enum_issue["status"] == "open" and enum_issue["integration_transition"] == "unchanged_open"
    assert coverage["status"] == "open" and coverage["affected_rules"].split("|")[0] == "ADMIT_008"


def test_manifest_freezes_policy_gap_provider_and_readiness_without_overclaim(tmp_path: Path) -> None:
    manifest = gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(tmp_path)["manifest"]
    assert manifest["admission_rule_id"] == "ADMIT_008"
    assert manifest["candidate_field"] == "topology_restoration_disposition"
    assert manifest["semantics_complete_count"] == 2 and manifest["semantics_incomplete_count"] == 18
    assert manifest["real_provider_value_count"] == 0
    assert manifest["topology_disposition_enum_issue_status"] == "open"
    assert manifest["ready_for_admit_008_standalone_evaluator_interface_implementation"] is False
    assert manifest["ready_for_admit_008_topology_restoration_disposition_enum_contract_design"] is True
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is False and manifest["ready_to_train_now"] is False


def test_production_defines_no_enum_evaluator_result_adapter_or_exact8_runtime() -> None:
    tree = ast.parse(Path(gate.__file__).read_text(encoding="utf-8"))
    functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assignments = {
        target.id for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }
    assert "evaluate_admit_008" not in functions
    assert "Admit008EvaluationResult" not in classes
    assert "TOPOLOGY_RESTORATION_DISPOSITION_ENUM" not in assignments
    assert "EVALUATOR_REGISTRY" not in assignments
    assert "evaluate_all_rules" not in functions


@pytest.mark.parametrize("kind", ["extra", "missing", "symlink"])
def test_output_missing_extra_and_symlink_fail_closed(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "output"
    gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(root)
    checker = _load_checker()
    if kind == "extra":
        (root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif kind == "missing":
        (root / gate.VOCABULARY_FILENAME).unlink()
    else:
        victim = tmp_path / "victim"
        victim.write_text("unchanged", encoding="utf-8")
        (root / gate.VOCABULARY_FILENAME).unlink()
        (root / gate.VOCABULARY_FILENAME).symlink_to(victim)
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_materializer_preserves_unexpected_output_and_symlink_victim(tmp_path: Path) -> None:
    extra = tmp_path / "extra"
    extra.mkdir()
    unexpected = extra / "unexpected.txt"
    unexpected.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(extra)
    assert unexpected.read_text(encoding="utf-8") == "keep"
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("unchanged", encoding="utf-8")
    (unsafe / gate.SOURCE_BOUNDARY_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(unsafe)
    assert victim.read_text(encoding="utf-8") == "unchanged"


@pytest.mark.parametrize(
    "case",
    [
        "phrase_promoted", "rule_id_promoted", "policy_status_promoted",
        "enum_ready", "reason_outcome_ready", "oracle_ready", "blocker_resolved",
        "admit008_removed_from_coverage", "fabricated_provider_value", "raw_source",
        "checkpoint_source", "source_sha_mismatch", "semantic_tamper_rehashed",
        "readiness_mirror_drift", "manifest_unknown_key",
    ],
)
def test_semantic_tamper_with_manifest_rehash_fails_closed(tmp_path: Path, case: str) -> None:
    root = tmp_path / "output"
    gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(root)
    checker = _load_checker()
    if case in {"phrase_promoted", "rule_id_promoted", "policy_status_promoted"}:
        targets = {
            "phrase_promoted": "approved_template_or_manual_review",
            "rule_id_promoted": "CYS_SG_ACRYLAMIDE_LIKE_STEP8_MANUAL_REVIEWED_V1",
            "policy_status_promoted": "accepted",
        }
        _rewrite_csv(root, gate.VOCABULARY_FILENAME, lambda rows: [
            {
                **row,
                "candidate_scalar_value_explicitly_declared": "true",
                "canonical_enum_member_explicitly_declared": "true",
                "safe_to_promote_to_canonical_enum_now": "true",
                "promotion_blocker": "",
            } if row["observed_string"] == targets[case] else row for row in rows
        ])
    elif case in {"enum_ready", "reason_outcome_ready", "oracle_ready", "fabricated_provider_value", "readiness_mirror_drift", "manifest_unknown_key"}:
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if case == "enum_ready":
            for key in (
                "admit_008_topology_disposition_enum_contract_available",
                "admit_008_standalone_evaluator_preconditions_complete",
                "ready_for_admit_008_standalone_evaluator_interface_implementation",
            ):
                manifest[key] = True
                manifest["readiness"][key] = True
        elif case == "reason_outcome_ready":
            manifest["admit_008_reason_outcome_contract_available"] = True
            manifest["readiness"]["admit_008_reason_outcome_contract_available"] = True
        elif case == "oracle_ready":
            manifest["admit_008_independent_semantic_oracle_available"] = True
            manifest["readiness"]["admit_008_independent_semantic_oracle_available"] = True
        elif case == "fabricated_provider_value":
            manifest["real_provider_value_count"] = 1
            manifest["real_provider_topology_disposition_mapping_validated"] = True
            manifest["readiness"]["real_provider_topology_disposition_mapping_validated"] = True
        elif case == "readiness_mirror_drift":
            manifest["readiness"]["ready_for_bulk_download_now"] = True
        else:
            manifest["unexpected_semantic_claim"] = True
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif case in {"blocker_resolved", "admit008_removed_from_coverage"}:
        def mutate_issues(rows: list[dict[str, str]]) -> None:
            for row in rows:
                if case == "blocker_resolved" and row["issue_id"] == gate.PRIMARY_BLOCKER:
                    row["status"] = "resolved"
                    row["integration_transition"] = "incorrect_transition"
                if case == "admit008_removed_from_coverage" and row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE":
                    row["affected_rules"] = row["affected_rules"].replace("ADMIT_008|", "")
        _rewrite_csv(root, gate.ISSUE_FILENAME, mutate_issues)
    elif case in {"raw_source", "checkpoint_source", "source_sha_mismatch"}:
        def mutate_sources(rows: list[dict[str, str]]) -> None:
            if case == "raw_source":
                rows[0]["source_relative_path"] = "data/raw/forbidden.cif"
            elif case == "checkpoint_source":
                rows[0]["source_relative_path"] = "checkpoints/forbidden.ckpt"
            else:
                rows[0]["filesystem_sha256"] = "0" * 64
        _rewrite_csv(root, gate.SOURCE_BOUNDARY_FILENAME, mutate_sources)
    else:
        _rewrite_csv(root, gate.PRECONDITION_FILENAME, lambda rows: [
            {**row, "observed_contract": "fabricated canonical enum exists"}
            if row["precondition_id"] == "PRE_007" else row for row in rows
        ])
    with pytest.raises((AssertionError, ValueError, FileNotFoundError)):
        checker._validate_disk(root, enforce_frozen_hashes=False)


def test_materializer_preserves_frozen_sources_and_creates_no_partial_files(tmp_path: Path) -> None:
    before = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    gate.run_covapie_bulk_download_admission_admit_008_formal_evaluator_interface_preconditions_audit_v1(tmp_path)
    after = {path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest() for path in gate.SOURCE_PATHS}
    assert before == after == gate.SOURCE_SHA256
    assert not [path for path in tmp_path.iterdir() if path.suffix in (".tmp", ".part")]
