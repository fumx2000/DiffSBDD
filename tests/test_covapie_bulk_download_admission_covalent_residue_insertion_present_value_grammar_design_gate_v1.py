from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate as gate,
)


CHECKER_PATH = REPO_ROOT / "scripts/check_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1.py"


def _load_checker():
    namespace: dict[str, object] = {"__file__": str(CHECKER_PATH), "__name__": "e1c_checker_test"}
    exec(compile(CHECKER_PATH.read_text(encoding="utf-8"), str(CHECKER_PATH), "exec"), namespace)
    return namespace


def test_exact39_source_order_structure_and_sha() -> None:
    snapshot = gate.build_frozen_source_snapshot()
    assert len(gate.SOURCE_PATHS) == len(set(gate.SOURCE_PATHS)) == 39
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    assert all(record.expected_sha256 == record.observed_sha256 == hashlib.sha256(record.content_bytes).hexdigest() for record in snapshot.records)
    assert all(path.parts[0] not in {"data/raw", "checkpoints"} for path in gate.SOURCE_PATHS)


def test_all_structural_checks_precede_first_source_read(monkeypatch: pytest.MonkeyPatch) -> None:
    checked: list[Path] = []

    def structural(path: Path, _root: Path) -> bool:
        checked.append(path)
        return len(checked) != 39

    monkeypatch.setattr(gate, "_structural_source_check", structural)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot()
    assert tuple(checked) == gate.SOURCE_PATHS


def test_source_missing_symlink_hash_and_base_tree_drift_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = tuple(Path(f"sources/source_{index:02d}.txt") for index in range(39))
    for index, path in enumerate(paths):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"source-{index}\n".encode())
    hashes = {path: hashlib.sha256((tmp_path / path).read_bytes()).hexdigest() for path in paths}
    base_bytes = {path: (tmp_path / path).read_bytes() for path in paths}
    monkeypatch.setattr(gate, "SOURCE_PATHS", paths)
    monkeypatch.setattr(gate, "SOURCE_SHA256", hashes)
    monkeypatch.setattr(gate, "_structural_source_check", lambda _path, _root: True)

    class Result:
        returncode = 0
        stderr = b""

        def __init__(self, stdout: bytes):
            self.stdout = stdout

    monkeypatch.setattr(gate, "_git", lambda arguments, root, text=True: Result(base_bytes[Path(arguments[1].split(":", 1)[1])]))
    assert len(gate.build_frozen_source_snapshot(tmp_path).records) == 39
    (tmp_path / paths[0]).write_bytes(b"filesystem-drift\n")
    with pytest.raises(ValueError, match="source SHA256 mismatch"):
        gate.build_frozen_source_snapshot(tmp_path)
    (tmp_path / paths[0]).write_bytes(b"source-0\n")

    monkeypatch.setattr(gate, "_git", lambda arguments, root, text=True: Result(b"base-tree-drift\n" if paths[0].as_posix() in arguments[1] else base_bytes[Path(arguments[1].split(":", 1)[1])]))
    with pytest.raises(ValueError, match="base-tree SHA256 drift"):
        gate.build_frozen_source_snapshot(tmp_path)


def test_structural_source_check_rejects_missing_and_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class Result:
        returncode = 0
        stdout = "blob\n"

    monkeypatch.setattr(gate, "_git", lambda *_args, **_kwargs: Result())
    regular = tmp_path / "regular.txt"
    regular.write_text("x", encoding="utf-8")
    assert gate._structural_source_check(Path("regular.txt"), tmp_path) is True
    assert gate._structural_source_check(Path("missing.txt"), tmp_path) is False
    symlink = tmp_path / "symlink.txt"
    symlink.symlink_to(regular)
    assert gate._structural_source_check(Path("symlink.txt"), tmp_path) is False
    assert gate._safe_source_path(Path("data/raw/x.cif")) is False
    assert gate._safe_source_path(Path("checkpoints/x.ckpt")) is False


def test_normative_constants_and_compiled_ascii_fullmatch_policy() -> None:
    assert gate.NORMATIVE_DICTIONARY_NAME == "PDBx/mmCIF V5"
    assert gate.NORMATIVE_ITEM == "_atom_site.pdbx_PDB_ins_code"
    assert gate.NORMATIVE_REFERENCE_ROLE == "_struct_conn.pdbx_ptnr1/2_PDB_ins_code references atom_site insertion code"
    assert gate.WWPDB_DICTIONARY_CODE_PATTERN == r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]*"
    assert gate.INSERTION_PRESENT_VALUE_PATTERN == r"[][_,.;:\"&<>()/\{}'`~!@#$%A-Za-z0-9*|+-]+"
    source = (REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate.py").read_text(encoding="utf-8")
    assert "INSERTION_PRESENT_VALUE_RE.fullmatch(value)" in source
    assert "INSERTION_PRESENT_VALUE_RE.search" not in source
    assert "INSERTION_PRESENT_VALUE_RE.match" not in source


def test_all_28_punctuation_and_ascii_alphanumerics_pass_exactly() -> None:
    assert len(gate.ALLOWED_PUNCTUATION) == len(set(gate.ALLOWED_PUNCTUATION)) == 28
    for character in gate.ALLOWED_PUNCTUATION:
        value = f"A{character}B"
        result = gate.validate_covalent_residue_insertion_present_value(value)
        assert result == {"valid": True, "value_exact_str": True, "outcome": "passed", "canonical_value": value, "reason": ""}
    for value in ("[", "]", "A", "Z", "a", "z", "0", "9", "A.B"):
        assert gate.validate_covalent_residue_insertion_present_value(value)["canonical_value"] == value


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        ("", gate.PRESENT_REASON["empty"]), (".", gate.PRESENT_REASON["marker"]),
        ("?", gate.PRESENT_REASON["marker"]), ("A B", gate.PRESENT_REASON["whitespace"]),
        ("A\tB", gate.PRESENT_REASON["whitespace"]), (" A", gate.PRESENT_REASON["whitespace"]),
        ("A ", gate.PRESENT_REASON["whitespace"]), ("A\nB", gate.PRESENT_REASON["whitespace"]),
        ("A\rB", gate.PRESENT_REASON["whitespace"]), ("A\vB", gate.PRESENT_REASON["whitespace"]),
        ("A\fB", gate.PRESENT_REASON["whitespace"]), ("A=B", gate.PRESENT_REASON["grammar"]),
        ("A\\B", gate.PRESENT_REASON["grammar"]), ("é", gate.PRESENT_REASON["non_ascii"]),
        (1, gate.PRESENT_REASON["type"]), (None, gate.PRESENT_REASON["type"]),
    ],
)
def test_invalid_present_values(value: object, reason: str) -> None:
    result = gate.validate_covalent_residue_insertion_present_value(value)
    assert result["valid"] is False and result["outcome"] == "invalid" and result["canonical_value"] is None
    assert result["reason"] == reason


def test_exact_str_rejects_subclass_and_no_max_length() -> None:
    class Derived(str):
        pass

    assert gate.validate_covalent_residue_insertion_present_value(Derived("A"))["reason"] == gate.PRESENT_REASON["type"]
    value = "A" * 4096
    first = gate.validate_covalent_residue_insertion_present_value(value)
    second = gate.validate_covalent_residue_insertion_present_value(first["canonical_value"])
    assert first == second
    assert first["canonical_value"] is value


def test_case_trim_coercion_and_normalization_are_not_applied() -> None:
    assert gate.validate_covalent_residue_insertion_present_value("aA")["canonical_value"] == "aA"
    assert gate.validate_covalent_residue_insertion_present_value(" A")["valid"] is False
    assert gate.validate_covalent_residue_insertion_present_value(1)["valid"] is False
    assert gate.validate_covalent_residue_insertion_present_value("Ａ")["reason"] == gate.PRESENT_REASON["non_ascii"]


def test_state_value_truth_and_unknown_never_promoted() -> None:
    cases = (
        (1, "", "invalid", "COVALENT_RESIDUE_INSERTION_STATE_TYPE_INVALID"),
        ("other", "", "invalid", "COVALENT_RESIDUE_INSERTION_STATE_VALUE_INVALID"),
        ("absent", None, "invalid", "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"),
        ("absent", "", "passed", ""),
        ("absent", "A", "invalid", "COVALENT_RESIDUE_INSERTION_ABSENT_REQUIRES_EMPTY"),
        ("unknown", None, "invalid", "COVALENT_RESIDUE_INSERTION_VALUE_TYPE_INVALID"),
        ("unknown", "", "blocked", gate.UNKNOWN_REASON),
        ("unknown", "A", "invalid", "COVALENT_RESIDUE_INSERTION_UNKNOWN_REQUIRES_EMPTY"),
        ("present", None, "invalid", gate.PRESENT_REASON["type"]),
        ("present", "", "invalid", gate.PRESENT_REASON["empty"]),
        ("present", ".", "invalid", gate.PRESENT_REASON["marker"]),
        ("present", "A B", "invalid", gate.PRESENT_REASON["whitespace"]),
        ("present", "é", "invalid", gate.PRESENT_REASON["non_ascii"]),
        ("present", "A=B", "invalid", gate.PRESENT_REASON["grammar"]),
        ("present", "A.B", "passed", ""),
    )
    for state, value, outcome, reason in cases:
        result = gate.validate_covalent_residue_insertion_state_value(state, value)
        assert result["outcome"] == outcome and result["reason"] == reason
    unknown = gate.validate_covalent_residue_insertion_state_value("unknown", "")
    assert unknown["canonical_state"] == "unknown" and unknown["blocks_admit_004"] is True


def test_invalid_state_value_outcomes_block_admit_004_fail_closed() -> None:
    class Derived(str):
        pass

    invalid_cases = (
        (1, ""), (Derived("present"), "A"), ("other", ""),
        ("absent", None), ("absent", "A"),
        ("unknown", None), ("unknown", "A"),
        ("present", None), ("present", Derived("A")), ("present", ""),
        ("present", "."), ("present", "?"), ("present", "A B"),
        ("present", "é"), ("present", "A=B"),
    )
    for state, value in invalid_cases:
        result = gate.validate_covalent_residue_insertion_state_value(state, value)
        assert result["outcome"] == "invalid" and result["blocks_admit_004"] is True
    unknown = gate.validate_covalent_residue_insertion_state_value("unknown", "")
    absent = gate.validate_covalent_residue_insertion_state_value("absent", "")
    present = gate.validate_covalent_residue_insertion_state_value("present", "A.B")
    assert unknown["outcome"] == "blocked" and unknown["blocks_admit_004"] is True
    assert absent["outcome"] == "passed" and absent["blocks_admit_004"] is False
    assert present["outcome"] == "passed" and present["blocks_admit_004"] is False


def test_struct_conn_atom_site_exact_agreement_design() -> None:
    passed = gate.validate_struct_conn_atom_site_insertion_agreement(True, "a.B", True, "a.B", "a.B", "a.B")
    assert passed == {"valid": True, "outcome": "passed", "canonical_value": "a.B", "reason": ""}
    for args in ((False, "A", True, "A", "A", "A"), (True, ".", True, ".", ".", "."), (True, "A", True, "a", "A", "A")):
        result = gate.validate_struct_conn_atom_site_insertion_agreement(*args)
        assert result["valid"] is False and result["outcome"] == "blocked"
    assert gate.validate_struct_conn_atom_site_insertion_agreement(True, "A", True, "a", "A", "A")["reason"] == gate.SOURCE_CONFLICT_REASON


def test_agreement_requires_candidate_and_provenance_exact_equality() -> None:
    passed = gate.validate_struct_conn_atom_site_insertion_agreement(True, "A.B", True, "A.B", "A.B", "A.B")
    assert passed == {"valid": True, "outcome": "passed", "canonical_value": "A.B", "reason": ""}
    conflicts = (
        (True, "A.B", True, "A.B", "A", "A.B"),
        (True, "A.B", True, "A.B", "A.B", "A"),
        (True, "A.B", True, "A", "A.B", "A.B"),
    )
    for values in conflicts:
        result = gate.validate_struct_conn_atom_site_insertion_agreement(*values)
        assert result["valid"] is False and result["reason"] == gate.SOURCE_CONFLICT_REASON
    invalid_evidence = (
        (True, "A.B", True, "A.B", 1, "A.B"),
        (True, "A.B", True, "A.B", "A.B", 1),
        (True, ".", True, ".", ".", "."),
        (True, "A=B", True, "A=B", "A=B", "A=B"),
    )
    for values in invalid_evidence:
        result = gate.validate_struct_conn_atom_site_insertion_agreement(*values)
        assert result["valid"] is False and result["reason"] == gate.EVIDENCE_INVALID_REASON


def test_64_row_matrix_exact_shape() -> None:
    rows = gate.build_examples_and_truth_rows()
    assert len(rows) == 64
    assert [sum(row["row_kind"] == kind for row in rows) for kind in ("present_valid_example", "present_invalid_example", "state_value_truth")] == [35, 15, 14]
    assert all(row["example_passed"] == "true" for row in rows)


def test_issue_transition_exact11_and_readiness() -> None:
    state = gate.build_design_state()
    assert len(state["issue_rows"]) == 10 and all(row["status"] == "open" for row in state["issue_rows"])
    assert state["exact11_count"] == 11 and state["exact11_conflicts"] == 3
    identity = next(row for row in state["issue_rows"] if row["issue_id"] == "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED")
    assert identity["integration_transition"] == "insertion_present_value_grammar_design_frozen_pending_successor_integration"


def test_deterministic_double_materialization_and_checker(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1(first)
    gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1(second)
    assert {path.name for path in first.iterdir()} == set(gate.OUTPUT_FILES)
    assert all((first / filename).read_bytes() == (second / filename).read_bytes() for filename in gate.OUTPUT_FILES)
    assert _load_checker()["check"](first)["all_checks_passed"] is True
    assert not list(tmp_path.rglob("*.tmp")) and not list(tmp_path.rglob("*.part"))


def test_output_missing_extra_symlink_hash_and_manifest_overclaim_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "outputs"
    gate.run_covapie_bulk_download_admission_covalent_residue_insertion_present_value_grammar_design_gate_v1(root)
    check = _load_checker()["check"]
    target = root / gate.CONTRACT_FILENAME
    original = target.read_bytes()
    target.unlink()
    with pytest.raises(AssertionError):
        check(root)
    target.write_bytes(original)
    copy = tmp_path / "contract-regular-copy.csv"
    copy.write_bytes(original)
    target.unlink()
    target.symlink_to(copy)
    with pytest.raises(AssertionError):
        check(root)
    target.unlink()
    target.write_bytes(original)
    (root / "extra.csv").write_text("x\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        check(root)
    (root / "extra.csv").unlink()
    target.write_bytes(original + b"drift")
    with pytest.raises(AssertionError):
        check(root)
    target.write_bytes(original)
    manifest_path = root / gate.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["admit_004_rule_logic_ready"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AssertionError):
        check(root)


def test_production_and_checker_use_only_standard_library() -> None:
    allowed = set(sys.stdlib_module_names) | {"__future__", "covalent_ext"}
    for path in (Path(gate.__file__), CHECKER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported <= allowed


def test_import_has_no_stdout_stderr_or_output_side_effects() -> None:
    module_name = gate.__name__
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        importlib.reload(sys.modules[module_name])
    assert stdout.getvalue() == stderr.getvalue() == ""


def test_no_raw_parser_provider_or_model_behavior_in_safety_contract() -> None:
    state = gate.build_design_state()
    safety = {row["safety_item"]: row for row in state["safety_rows"]}
    for item in gate.FALSE_SAFETY_ITEMS:
        assert safety[item]["expected_executed"] == safety[item]["observed_executed"] == "false"
        assert safety[item]["safety_passed"] == "true"
