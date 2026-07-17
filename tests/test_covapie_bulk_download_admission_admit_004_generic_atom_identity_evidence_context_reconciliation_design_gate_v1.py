from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import importlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate as gate,
)


CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1.py"


def _checker_module():
    spec = importlib.util.spec_from_file_location("covapie_e1e1_checker_test", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _materialize(root: Path) -> Path:
    result = gate.run_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1(root)
    assert result["manifest"]["all_checks_passed"] is True
    return root


def _replace_snapshot_bytes(snapshot: gate.FrozenSourceSnapshot, path: Path, content: bytes) -> gate.FrozenSourceSnapshot:
    return gate.FrozenSourceSnapshot(tuple(
        gate.FrozenSourceRecord(
            record.relative_path, record.expected_sha256, record.base_tree_sha256,
            record.filesystem_sha256, content if record.relative_path == path else record.content_bytes,
        )
        for record in snapshot.records
    ))


def test_exact16_source_order_structure_sha_and_base_tree_agreement() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert len(gate.SOURCE_PATHS) == len(set(gate.SOURCE_PATHS)) == 16
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert all(
        record.expected_sha256 == record.base_tree_sha256 == record.filesystem_sha256
        == hashlib.sha256(record.content_bytes).hexdigest()
        == gate.SOURCE_SHA256[record.relative_path]
        for record in snapshot.records
    )


def test_all_structural_checks_precede_first_source_content_read(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    original_structure = gate._structural_source_check
    original_read = Path.read_bytes

    def structural(path: Path, root: Path) -> bool:
        events.append(f"structure:{path}")
        return original_structure(path, root)

    def read(path: Path) -> bytes:
        events.append(f"read:{path}")
        return original_read(path)

    monkeypatch.setattr(gate, "_structural_source_check", structural)
    monkeypatch.setattr(Path, "read_bytes", read)
    gate.build_frozen_source_snapshot()
    first_read = next(index for index, event in enumerate(events) if event.startswith("read:"))
    assert first_read == 16
    assert all(event.startswith("structure:") for event in events[:16])


def test_structure_rejects_missing_symlink_unsafe_raw_and_checkpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        returncode = 0
        stdout = "100644 blob 0123456789012345678901234567890123456789\tregular.csv\n"

    monkeypatch.setattr(gate, "_git", lambda *_args, **_kwargs: Result())
    regular = tmp_path / "regular.csv"
    regular.write_text("x\n", encoding="utf-8")
    assert gate._structural_source_check(Path("regular.csv"), tmp_path) is True
    assert gate._structural_source_check(Path("missing.csv"), tmp_path) is False
    symlink = tmp_path / "symlink.csv"
    symlink.symlink_to(regular)
    assert gate._structural_source_check(Path("symlink.csv"), tmp_path) is False
    assert gate._safe_relative_path(Path("../escape")) is False
    assert gate._safe_relative_path(Path("/absolute")) is False
    assert gate._safe_relative_path(Path("data/raw/example.cif")) is False
    assert gate._safe_relative_path(Path("checkpoints/example.ckpt")) is False


def test_hash_and_base_tree_drift_fail_closed_with_zero_success_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = gate.build_frozen_source_snapshot()
    bad = _replace_snapshot_bytes(snapshot, gate.E1D_RULE_PATH, snapshot.records[0].content_bytes + b"drift")
    assert gate.validate_frozen_source_snapshot(bad) is False
    state = gate.build_design_state(bad)
    assert state["design_readiness"] is state["all_checks_passed"] is False
    assert state["contract_pass_count"] == state["truth_pass_count"] == 0

    original_git = gate._git

    def drift_git(arguments, repo_root, *, text=True):
        if arguments[:1] == ["show"] and arguments[1].endswith(gate.SOURCE_PATHS[0].as_posix()):
            return subprocess.CompletedProcess(["git", *arguments], 0, stdout=b"drift\n", stderr=b"")
        return original_git(arguments, repo_root, text=text)

    monkeypatch.setattr(gate, "_git", drift_git)
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        gate.build_frozen_source_snapshot()


def test_source_failure_creates_no_success_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "build_frozen_source_snapshot", lambda *_a, **_k: (_ for _ in ()).throw(ValueError("failed")))
    root = tmp_path / "must-not-exist"
    with pytest.raises(RuntimeError, match="failed closed"):
        gate.run_covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate_v1(root)
    assert not root.exists()


def test_direct_historical_conflict_and_rule_registry_separation() -> None:
    state = gate.build_design_state()
    assert state["all_checks_passed"] is True
    historical = state["historical"]
    rules = {row["admission_rule_id"]: row for row in historical["rules"]}
    fields = {row["field_name"]: row for row in historical["fields"]}
    assert rules["ADMIT_004"]["candidate_field_dependencies"] == "|".join(gate.CANDIDATE_FIELDS)
    assert rules["ADMIT_004"]["implementation_disposition"] == "rule_logic_ready"
    assert rules["ADMIT_004"]["evaluation_context_dependencies"] == "covalent_residue_identity_contract"
    assert rules["ADMIT_005"]["admission_rule_name"] == "cys_sg_scope_only_v1"
    assert rules["ADMIT_005"]["candidate_field_dependencies"] == "covalent_residue_name|covalent_residue_atom_name"
    assert fields["covalent_residue_atom_name"]["source_value_contract"] == "must be SG for v1 Cys scope"
    assert fields["covalent_residue_atom_name"]["dependent_rules"] == "ADMIT_004|ADMIT_005"


def test_e1a_exact_sg_leakage_and_p4_generic_ascii_source_evidence() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    e1a = gate._function_source(snapshot, gate.E1A_SOURCE_PATH, "validate_covalent_residue_atom_name")
    provider = gate._function_source(snapshot, gate.E1A_SOURCE_PATH, "validate_provider_identity_atom_evidence")
    p4 = gate._function_source(snapshot, gate.P4_SOURCE_PATH, "validate_matched_atom_site_row_identity")
    assert 'value != "SG"' in e1a and 'LexicalResult(True, "SG", "")' in e1a
    assert "validate_covalent_residue_atom_name(candidate_atom_name)" in provider
    assert "type(residue_atom_name) is not str" in p4
    assert "not value.isascii()" in p4 and '"SG"' not in p4


def test_generic_atom_valid_exact_preserve_no_arbitrary_max() -> None:
    for value in ("SG", "CA", "ca", "N1", "OXT", "C1'", "A.B", "+", "X" * 10000):
        result = gate.validate_generic_covalent_residue_atom_name(value)
        assert result == gate.GenericAtomNameResult(True, value, "")


def test_generic_atom_invalid_reasons_and_no_repair() -> None:
    class StrSubclass(str):
        pass

    cases = (
        (1, "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID"),
        (StrSubclass("SG"), "COVALENT_RESIDUE_ATOM_NAME_TYPE_INVALID"),
        ("", "COVALENT_RESIDUE_ATOM_NAME_EMPTY"),
        ("SÉ", "COVALENT_RESIDUE_ATOM_NAME_NON_ASCII"),
        (" S", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        ("S G", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        ("S\tG", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        ("S\nG", "COVALENT_RESIDUE_ATOM_NAME_WHITESPACE_FORBIDDEN"),
        (".", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
        ("?", "COVALENT_RESIDUE_ATOM_NAME_MARKER_FORBIDDEN"),
    )
    for value, reason in cases:
        result = gate.validate_generic_covalent_residue_atom_name(value)
        assert result == gate.GenericAtomNameResult(False, None, reason)
    assert gate.validate_generic_covalent_residue_atom_name("ca").canonical_value == "ca"
    assert gate.validate_generic_covalent_residue_atom_name("ｃａ").valid is False


def test_e1c_insertion_present_value_grammar_reused_without_backslash_drift() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    contract = gate._csv_document(snapshot, gate.E1C_CONTRACT_PATH)
    contract_map = {row["contract_id"]: row for row in contract.rows}
    e1c_pattern = contract_map["INSERTION_GRAMMAR_005"]["observed_value"]
    assert contract_map["INSERTION_GRAMMAR_005"]["expected_value"] == e1c_pattern
    assert gate.INSERTION_PRESENT_VALUE_PATTERN == e1c_pattern
    assert gate._INSERTION_RE.fullmatch("A/B") is not None
    assert gate._validate_insertion_state_value("present", "A/B") == ""
    assert gate._INSERTION_RE.fullmatch("A\\B") is None
    assert gate._validate_insertion_state_value("present", "A\\B") == "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID"
    assert gate._INSERTION_RE.fullmatch("A=B") is None
    assert gate._validate_insertion_state_value("present", "A=B") == "COVALENT_RESIDUE_INSERTION_PRESENT_CHARACTER_GRAMMAR_INVALID"
    assert gate._validate_insertion_state_value("present", "A{B") == ""
    assert gate._validate_insertion_state_value("present", "A}B") == ""
    absent = gate._base_candidate(state="absent", value="")
    assert gate.classify_admit_004_identity_evidence_context_design(absent, gate._base_context(absent)).outcome == "passed"
    unknown = gate._base_candidate(state="unknown", value="")
    assert gate.classify_admit_004_identity_evidence_context_design(unknown, gate._base_context(unknown)) == gate.EvidenceContextDesignResult("blocked", gate.UNKNOWN_REASON)


def test_admit_004_admit_005_scope_truth_and_no_admit_004_rejected() -> None:
    cases = (
        ("CYS", "SG", "CYS", "passed", "passed"),
        ("cys", "SG", "CYS", "passed", "passed"),
        ("CYS", "CA", "CYS", "passed", "rejected"),
        ("SER", "SG", "SER", "passed", "rejected"),
        ("SER", "CA", "SER", "passed", "rejected"),
        ("CYS", "ca", "CYS", "passed", "rejected"),
        ("C-Y", "SG", None, "invalid", "invalid"),
        ("CYS", "?", "CYS", "invalid", "invalid"),
    )
    for residue, atom, canonical, admit4, admit5 in cases:
        result = gate.classify_admit_004_admit_005_atom_scope_design(residue, atom)
        assert (result.canonical_residue_name, result.admit_004_outcome, result.admit_005_outcome) == (canonical, admit4, admit5)
        assert result.admit_004_outcome != "rejected"


def test_context_mapping_subclass_proxy_extra_keys_and_no_mutation() -> None:
    class MappingSubclass(dict):
        pass

    candidate_dict = gate._base_candidate()
    candidate_dict["unrelated_candidate_field"] = "ignored"
    nested = gate._base_context(candidate_dict)[gate.EVIDENCE_CONTEXT_KEY]
    proxy_nested = MappingProxyType({
        **nested,
        "attested_candidate_fields": MappingProxyType(dict(nested["attested_candidate_fields"])),
    })
    context = MappingSubclass({gate.EVIDENCE_CONTEXT_KEY: proxy_nested, "unified_engine_extra": object()})
    candidate = MappingProxyType(candidate_dict)
    before_candidate = dict(candidate_dict)
    before_attested = dict(nested["attested_candidate_fields"])
    result = gate.classify_admit_004_identity_evidence_context_design(candidate, context)
    assert result == gate.EvidenceContextDesignResult("passed", "")
    assert candidate_dict == before_candidate
    assert nested["attested_candidate_fields"] == before_attested


def test_nested_schema_keysets_attested_keysets_and_exact_value_types() -> None:
    candidate = gate._base_candidate()
    schema = gate._base_context(candidate)
    schema[gate.EVIDENCE_CONTEXT_KEY]["schema_version"] = "wrong"
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, schema).outcome == "invalid"
    missing = gate._base_context(candidate)
    del missing[gate.EVIDENCE_CONTEXT_KEY]["provider_evidence_reason"]
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, missing).reason == "ADMIT_004_IDENTITY_EVIDENCE_CONTEXT_KEYSET_INVALID"
    extra = gate._base_context(candidate)
    extra[gate.EVIDENCE_CONTEXT_KEY]["extra"] = "x"
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, extra).outcome == "invalid"
    attested_missing = gate._base_context(candidate)
    del attested_missing[gate.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][gate.CANDIDATE_FIELDS[0]]
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, attested_missing).reason == "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID"
    attested_extra = gate._base_context(candidate)
    attested_extra[gate.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"]["extra"] = "x"
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, attested_extra).reason == "ADMIT_004_ATTESTED_CANDIDATE_FIELDSET_INVALID"
    bad_type = gate._base_context(candidate)
    bad_type[gate.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][gate.CANDIDATE_FIELDS[0]] = 1
    assert "VALUE_TYPE_INVALID" in gate.classify_admit_004_identity_evidence_context_design(candidate, bad_type).reason


def test_all_nine_candidate_fields_bind_raw_before_canonicalization() -> None:
    candidate = gate._base_candidate()
    candidate["covalent_residue_name"] = "cys"
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, gate._base_context(candidate)).outcome == "passed"
    for field in gate.CANDIDATE_FIELDS:
        context = gate._base_context(candidate)
        context[gate.EVIDENCE_CONTEXT_KEY]["attested_candidate_fields"][field] = "DIFFERENT"
        result = gate.classify_admit_004_identity_evidence_context_design(candidate, context)
        assert result == gate.EvidenceContextDesignResult("invalid", f"ADMIT_004_ATTESTED_CANDIDATE_BINDING_MISMATCH:{field}")


def test_missing_context_blocked_malformed_invalid_and_provider_reason_contract() -> None:
    candidate = gate._base_candidate()
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, {}) == gate.EvidenceContextDesignResult("blocked", gate.MISSING_CONTEXT_REASON)
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, 1).outcome == "invalid"
    assert gate.classify_admit_004_identity_evidence_context_design(candidate, {gate.EVIDENCE_CONTEXT_KEY: []}).outcome == "invalid"
    for outcome, reason, expected in (
        ("passed", "", "passed"), ("passed", "NONEMPTY", "invalid"),
        ("blocked", "", "invalid"), ("blocked", "BLOCK", "blocked"),
        ("invalid", "INVALID", "invalid"), ("rejected", "X", "invalid"),
    ):
        result = gate.classify_admit_004_identity_evidence_context_design(candidate, gate._base_context(candidate, outcome=outcome, reason=reason))
        assert result.outcome == expected


def test_exact_bool_present_attestations_absent_nonpromotion_and_unknown_priority() -> None:
    present = gate._base_candidate(state="present", value="A")
    four = gate._base_context(present, four_way=False)
    quote = gate._base_context(present, quote=False)
    assert gate.classify_admit_004_identity_evidence_context_design(present, four) == gate.EvidenceContextDesignResult("blocked", gate.FOUR_WAY_REASON)
    assert gate.classify_admit_004_identity_evidence_context_design(present, quote) == gate.EvidenceContextDesignResult("blocked", gate.QUOTE_CLASS_REASON)
    non_bool = gate._base_context(present)
    non_bool[gate.EVIDENCE_CONTEXT_KEY]["four_way_present_value_exact_equality_attested"] = 1
    assert gate.classify_admit_004_identity_evidence_context_design(present, non_bool).outcome == "invalid"
    absent = gate._base_candidate()
    assert gate.classify_admit_004_identity_evidence_context_design(absent, gate._base_context(absent, four_way=False, quote=False)).outcome == "passed"
    unknown = gate._base_candidate(state="unknown", value="")
    assert gate.classify_admit_004_identity_evidence_context_design(unknown, gate._base_context(unknown)).reason == gate.UNKNOWN_REASON


def test_invalid_precedence_over_unknown_and_blocked_order() -> None:
    unknown = gate._base_candidate(state="unknown", value="")
    malformed = gate._base_context(unknown)
    malformed[gate.EVIDENCE_CONTEXT_KEY]["schema_version"] = "wrong"
    assert gate.classify_admit_004_identity_evidence_context_design(unknown, malformed).outcome == "invalid"
    provider_invalid = gate._base_context(unknown, outcome="invalid", reason="PROVIDER_INVALID")
    assert gate.classify_admit_004_identity_evidence_context_design(unknown, provider_invalid) == gate.EvidenceContextDesignResult("invalid", "PROVIDER_INVALID")
    provider_blocked = gate._base_context(unknown, outcome="blocked", reason="PROVIDER_BLOCKED")
    assert gate.classify_admit_004_identity_evidence_context_design(unknown, provider_blocked) == gate.EvidenceContextDesignResult("blocked", gate.UNKNOWN_REASON)
    assert gate.classify_admit_004_identity_evidence_context_design(unknown, {}) == gate.EvidenceContextDesignResult("blocked", gate.UNKNOWN_REASON)


def test_candidate_validation_fixed_missing_and_syntax_order() -> None:
    candidate = gate._base_candidate()
    for index, field in enumerate(gate.CANDIDATE_FIELDS):
        partial = {name: candidate[name] for name in gate.CANDIDATE_FIELDS if name != field}
        result = gate.classify_admit_004_identity_evidence_context_design(partial, {})
        assert result == gate.EvidenceContextDesignResult("invalid", f"ADMIT_004_CANDIDATE_FIELD_MISSING:{field}")
        if index == 0:
            break
    broken = gate._base_candidate()
    broken["covalent_residue_name"] = "C-Y"
    broken["covalent_residue_atom_name"] = "?"
    assert gate.classify_admit_004_identity_evidence_context_design(broken, []).reason == "COVALENT_RESIDUE_NAME_SYNTAX_INVALID"


def test_exact36_truth_contract_issues_provider_and_readiness() -> None:
    state = gate.build_design_state()
    assert len(state["contract_rows"]) == state["contract_pass_count"] == 28
    assert len(state["truth_rows"]) == state["truth_pass_count"] == 36
    assert [sum(row["row_kind"] == kind for row in state["truth_rows"]) for kind in (
        "generic_atom_valid", "generic_atom_invalid", "admit_004_admit_005_scope", "evidence_context_binding",
    )] == [8, 8, 8, 12]
    assert all(row["truth_passed"] == "true" for row in state["truth_rows"])
    assert len(state["issue_rows"]) == 10
    assert state["issue_rows"][:9] == list(state["historical"]["issues"])
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issues[gate.NEW_ISSUE]["issue_count"] == "1"
    assert issues[gate.PROVIDER_ISSUE]["status"] == "open" and issues[gate.PROVIDER_ISSUE]["issue_count"] == "11"


def test_deterministic_double_materialization_and_checker(tmp_path: Path) -> None:
    first = _materialize(tmp_path / "first")
    second = _materialize(tmp_path / "second")
    assert all((first / name).read_bytes() == (second / name).read_bytes() for name in gate.OUTPUT_FILES)
    result = _checker_module().check(first)
    assert result["truth_passed"] == "36/36" and result["provider_blocking_count"] == 11


def test_checker_rejects_missing_extra_symlink_hash_drift_and_overclaim(tmp_path: Path) -> None:
    checker = _checker_module()
    missing = _materialize(tmp_path / "missing")
    (missing / gate.CONTRACT_FILENAME).unlink()
    with pytest.raises(AssertionError):
        checker.check(missing)

    extra = _materialize(tmp_path / "extra")
    (extra / "unexpected.csv").write_text("x\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.check(extra)

    symlink = _materialize(tmp_path / "symlink")
    (symlink / gate.CONTRACT_FILENAME).unlink()
    (symlink / gate.CONTRACT_FILENAME).symlink_to(REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT / gate.CONTRACT_FILENAME)
    with pytest.raises(AssertionError):
        checker.check(symlink)

    drift = _materialize(tmp_path / "drift")
    (drift / gate.TRUTH_FILENAME).write_bytes((drift / gate.TRUTH_FILENAME).read_bytes() + b"\n")
    with pytest.raises(AssertionError):
        checker.check(drift)

    overclaim = _materialize(tmp_path / "overclaim")
    manifest_path = overclaim / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ready_for_bulk_download_now"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        checker.check(overclaim)


def test_import_silent_standard_library_only_and_no_evaluator() -> None:
    production = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_004_generic_atom_identity_evidence_context_reconciliation_design_gate.py"
    checker = _checker_module()
    assert checker._standard_library_only(production)
    assert checker._standard_library_only(CHECKER_PATH)
    tree = ast.parse(production.read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "evaluate_admit_004" not in names
    assert not names.intersection({"execute_parser", "execute_provider", "materialize_candidate_records"})
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        importlib.reload(gate)
    assert stdout.getvalue() == stderr.getvalue() == ""


def test_manifest_safety_no_machine_metadata_or_self_hash(tmp_path: Path) -> None:
    root = _materialize(tmp_path / "outputs")
    manifest = json.loads((root / gate.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert not any(key in manifest for key in ("timestamp", "hostname", "host", "manifest_sha256"))
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["historical_e1d_admit_004_rule_logic_ready_claim"] is True
    assert manifest["generic_atom_scope_separation_conflict_detected"] is True
    assert manifest["contract_count"] == manifest["contract_pass_count"] == 28
    assert manifest["e1c_insertion_present_value_grammar_reused_exactly"] is True
    assert manifest["reconciled_admit_004_interface_implementation_ready"] is False
    assert manifest["generic_atom_identity_semantics_integrated_into_effective_schema"] is False
    assert manifest["identity_evidence_context_integrated_into_effective_schema"] is False
    assert manifest["admit_004_evaluator_implemented"] is False
    assert manifest["parser_quote_class_roundtrip_verified"] is False
    assert manifest["provider_blocking_issue_count"] == 11
    assert manifest["ready_for_real_candidate_evaluation"] is False
    assert manifest["ready_for_bulk_download_now"] is False
    assert manifest["ready_for_training"] is manifest["ready_to_train_now"] is False
    assert manifest["feature_semantics_audit_required_before_training"] is True
    assert all(row["safety_passed"] == "true" for row in gate._safety_rows())
