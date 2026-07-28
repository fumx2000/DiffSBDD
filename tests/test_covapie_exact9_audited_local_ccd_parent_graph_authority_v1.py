from __future__ import annotations

import csv
import dataclasses
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_exact9_audited_local_ccd_parent_graph_authority_v1 as authority,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle  # noqa: E402
from covalent_ext.covapie_current11_pre_reaction_graph_and_bond_order_authority_v1 import (  # noqa: E402
    ParentAtom,
    ParentBond,
    parse_ccd_component_with_stats,
)


CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_exact9_audited_local_ccd_parent_graph_authority_v1.py"
)
SPEC = importlib.util.spec_from_file_location("exact9_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
NESTED_LIFECYCLE_ENV = "COVAPIE_EXACT9_NESTED_LIFECYCLE"


def _git(*arguments: str, cwd: Path = ROOT, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *arguments),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check:
        assert result.returncode == 0, result.stderr
    return result.stdout


def _base_bytes(path: Path) -> bytes:
    return _git("show", f"{authority.BASE_COMMIT}:{path.as_posix()}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _artifacts() -> dict[str, bytes]:
    return authority.build_evidence_payloads(ROOT)


def _artifact_rows(name: str) -> list[dict[str, str]]:
    return _rows((ROOT / authority.OUTPUT_ROOT / name).read_bytes())


def _bool(value: str) -> bool:
    assert value in ("true", "false")
    return value == "true"


def test_formal_base_identity_and_predecessor_frozen_sha() -> None:
    shown = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", authority.BASE_COMMIT
    ).decode().splitlines()
    assert shown == [
        authority.BASE_COMMIT,
        authority.BASE_PARENT,
        authority.BASE_TREE,
        authority.BASE_SUBJECT,
    ]
    assert hashlib.sha256(_base_bytes(authority.PREDECESSOR_SOURCE)).hexdigest() == (
        "fc3afac00655c4e0857d12464d7e9c658bb8ac86bde2f845149d26bdda4ad284"
    )
    assert hashlib.sha256(_base_bytes(authority.PREDECESSOR_MANIFEST)).hexdigest() == (
        "4a3ab3ba6edf83f7f85f9418e5146a63814f5dec383a38ff61a7bcfc2df68626"
    )
    for path, expected in authority.FROZEN_BASE_SHA256.items():
        assert hashlib.sha256(_base_bytes(path)).hexdigest() == expected
    assert _git(
        "rev-parse", f"{authority.BASE_COMMIT}:.gitignore"
    ).decode().strip() == authority.GITIGNORE_BLOB
    gitignore = _base_bytes(authority.GITIGNORE).decode("utf-8")
    assert (
        "/data/raw/covalent_sources/ccd/"
        "independence_evidence_batch_000001/"
    ) in gitignore.splitlines()


def test_exact9_paths_and_expected_sha_come_only_from_base_audit() -> None:
    audit = authority.load_expected_audit(ROOT)
    assert tuple(audit) == authority.EXACT9_COMPONENTS
    assert authority.EXACT9_PATHS == tuple(
        authority.CCD_ROOT / f"{component}.cif"
        for component in authority.EXACT9_COMPONENTS
    )
    assert len({row["sha256"] for row in audit.values()}) == 9
    assert all(re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) for row in audit.values())
    source = Path(authority.__file__).read_text(encoding="utf-8")
    for row in audit.values():
        assert row["sha256"] not in source


def test_raw_exact9_safety_and_sha_before_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    audit = authority.load_expected_audit(ROOT)
    for component, relative in zip(authority.EXACT9_COMPONENTS, authority.EXACT9_PATHS):
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_mode & 0o777 == 0o644
        assert 0 < path.stat().st_size < authority.MAX_PAYLOAD_SIZE_BYTES
        assert _git("check-ignore", "-q", "--", relative.as_posix()) == b""
        assert _git("ls-files", "--", relative.as_posix()) == b""
        assert _git("diff", "--cached", "--name-only", "--", relative.as_posix()) == b""
        assert hashlib.sha256(path.read_bytes()).hexdigest() == audit[component]["sha256"]

    bad_audit = dict(audit["JUG"])
    bad_audit["sha256"] = "0" * 64

    def forbidden(*_args, **_kwargs):
        raise AssertionError("decode/parse boundary crossed before SHA match")

    monkeypatch.setattr(authority, "_component_identity", forbidden)
    monkeypatch.setattr(authority, "parse_ccd_component_with_stats", forbidden)
    result = authority._admit_component(ROOT, "JUG", bad_audit)
    assert result.admission_row["payload_sha_matches"] is False
    assert result.admission_row["decode_passed"] is False
    assert result.admission_row["parse_passed"] is False
    assert result.admission_row["admission_disposition"] == "blocked_sha_mismatch"


def test_component_identity_exact_and_fail_closed() -> None:
    assert authority._component_identity(
        "data_JUG\n_chem_comp.id JUG\n", "JUG"
    ) == ("JUG", "JUG")
    with pytest.raises(ValueError, match="ccd_component_identity_missing"):
        authority._component_identity("data_JUG\n", "JUG")
    with pytest.raises(ValueError, match="ccd_component_identity_mismatch"):
        authority._component_identity(
            "data_jug\n_chem_comp.id JUG\n", "JUG"
        )
    with pytest.raises(ValueError, match="ccd_component_identity_mismatch"):
        authority._component_identity(
            "data_JUG\n_chem_comp.id E64\n", "JUG"
        )


def test_predecessor_parser_heavy_filter_charge_and_halogens() -> None:
    payload = """data_X
loop_
_chem_comp_atom.atom_id
_chem_comp_atom.type_symbol
_chem_comp_atom.charge
C1 C -1
F1 F 0
CL1 Cl 0
BR1 Br 0
I1 I 0
H1 H 0
D1 D 0
T1 T 0
#
loop_
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
_chem_comp_bond.value_order
_chem_comp_bond.pdbx_aromatic_flag
C1 F1 SING N
F1 CL1 SING N
CL1 BR1 SING N
BR1 I1 SING N
C1 H1 SING N
C1 D1 SING N
C1 T1 SING N
#
"""
    atoms, bonds, stats = parse_ccd_component_with_stats(payload)
    assert tuple(atom.type_symbol for atom in atoms) == ("C", "F", "CL", "BR", "I")
    assert atoms[0].formal_charge == -1
    assert tuple(atom.row_index_0based for atom in atoms) == tuple(range(5))
    assert stats.source_atom_row_count == 8
    assert stats.explicit_hydrogen_atom_count == 3
    assert stats.heavy_atom_count == 5
    assert stats.source_bond_row_count == 7
    assert stats.hydrogen_involving_bond_count == 3
    assert stats.heavy_heavy_bond_count == len(bonds) == 4


def test_bond_normalization_freezes_standard_ccd_aromatic_encoding() -> None:
    assert authority.normalize_parent_bond_order("SING", "Y") == "aromatic"
    assert authority.normalize_parent_bond_order("DOUB", "Y") == "aromatic"
    assert authority.normalize_parent_bond_order("AROM", "Y") == "aromatic"
    assert authority.normalize_parent_bond_order("SING", "N") == "single"
    assert authority.normalize_parent_bond_order("DOUB", "N") == "double"
    assert authority.normalize_parent_bond_order("TRIP", "N") == "triple"
    with pytest.raises(ValueError, match="aromatic_flag_order_conflict"):
        authority.normalize_parent_bond_order("TRIP", "Y")
    with pytest.raises(ValueError, match="aromatic_flag_order_conflict"):
        authority.normalize_parent_bond_order("AROM", "N")
    with pytest.raises(ValueError, match="unsupported_ccd_bond_order"):
        authority.normalize_parent_bond_order("QUAD", "N")


def test_parent_graph_validation_and_sha_are_order_independent() -> None:
    atoms = (
        ParentAtom("C1", "C", 0, 0),
        ParentAtom("O1", "O", -1, 1),
        ParentAtom("F1", "F", 0, 2),
    )
    bonds = (
        ParentBond("C1", "O1", "DOUB", "N"),
        ParentBond("F1", "C1", "SING", "N"),
    )
    normalized, count, graph_sha = authority._validate_parent_graph(atoms, bonds)
    assert count == 1
    assert normalized == (
        ("C1", "F1", "SING", "N", "single"),
        ("C1", "O1", "DOUB", "N", "double"),
    )
    assert re.fullmatch(r"[0-9a-f]{64}", graph_sha)
    reversed_sha = authority.canonical_parent_graph_sha256(
        tuple(reversed(atoms)),
        tuple(reversed(tuple((left, right, order) for left, right, _, _, order in normalized))),
    )
    assert reversed_sha == graph_sha
    with pytest.raises(ValueError, match="parent_graph_disconnected"):
        authority._validate_parent_graph(atoms, bonds[:1])
    with pytest.raises(ValueError, match="parent_bond_self_loop"):
        authority._validate_parent_graph(
            atoms, (ParentBond("C1", "C1", "SING", "N"),)
        )
    with pytest.raises(ValueError, match="duplicate_parent_bond"):
        authority._validate_parent_graph(atoms, (bonds[0], bonds[0], bonds[1]))


def test_exact9_admission_statistics_graph_sha_and_connectivity() -> None:
    rows = _artifact_rows(authority.ADMISSION_FILE)
    expected = {
        "JUG": (19, 6, 13, 20, 6, 14),
        "E64": (55, 30, 25, 54, 30, 24),
        "ZYA": (52, 23, 29, 53, 23, 30),
        "PCM": (85, 42, 43, 87, 42, 45),
        "INP": (85, 43, 42, 87, 43, 44),
        "INA": (82, 40, 42, 83, 40, 43),
        "IN6": (82, 39, 43, 84, 39, 45),
        "IN3": (73, 33, 40, 75, 33, 42),
        "UFP": (33, 12, 21, 34, 12, 22),
    }
    assert len(rows) == 9
    for row in rows:
        values = tuple(
            int(row[field])
            for field in (
                "source_atom_row_count", "explicit_hydrogen_atom_count",
                "parent_heavy_atom_count", "source_bond_row_count",
                "hydrogen_involving_bond_count", "parent_heavy_bond_count",
            )
        )
        assert values == expected[row["ligand_comp_id"]]
        assert int(row["unsupported_bond_order_count"]) == 0
        assert int(row["parent_component_count"]) == 1
        assert re.fullmatch(r"[0-9a-f]{64}", row["parent_graph_sha256"])
        assert row["admission_disposition"] == "admitted_sha_attested_local_ccd"
        assert row["blocking_reasons"] == ""
        assert _bool(row["verified"])


def test_parent_atom_and_bond_authority_tables() -> None:
    atoms = _artifact_rows(authority.ATOM_FILE)
    bonds = _artifact_rows(authority.BOND_FILE)
    assert len(atoms) == 298
    assert len(bonds) == 309
    assert Counter(row["normalized_bond_order"] for row in bonds) == {
        "single": 184, "double": 36, "aromatic": 89,
    }
    atom_ids: dict[str, set[str]] = {}
    indices: dict[str, list[int]] = {}
    graph_sha_by_component: dict[str, set[str]] = {}
    for row in atoms:
        component = row["ligand_comp_id"]
        atom_ids.setdefault(component, set())
        assert row["ccd_atom_id"] not in atom_ids[component]
        atom_ids[component].add(row["ccd_atom_id"])
        indices.setdefault(component, []).append(
            int(row["ccd_heavy_atom_row_index_0based"])
        )
        graph_sha_by_component.setdefault(component, set()).add(
            row["component_parent_graph_sha256"]
        )
        assert row["ccd_type_symbol"] not in ("H", "D", "T")
        assert row["ccd_type_symbol"] in authority.SUPPORTED_ELEMENTS
        assert row["authority_class"] == authority.AUTHORITY_CLASS
        assert _bool(row["verified"])
    assert all(values == list(range(len(values))) for values in indices.values())
    assert all(len(values) == 1 for values in graph_sha_by_component.values())
    edge_sets: dict[str, set[tuple[str, str]]] = {}
    for row in bonds:
        component = row["ligand_comp_id"]
        edge = (row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"])
        assert edge[0] < edge[1]
        assert edge[0] in atom_ids[component] and edge[1] in atom_ids[component]
        edge_sets.setdefault(component, set())
        assert edge not in edge_sets[component]
        edge_sets[component].add(edge)
        assert row["normalized_bond_order"] in authority.NORMALIZED_BOND_ORDERS
        assert row["authority_class"] == authority.AUTHORITY_CLASS
        assert _bool(row["verified"])


def test_current11_component_coverage_counts_and_readiness_boundary() -> None:
    rows = _artifact_rows(authority.READINESS_FILE)
    assert len(rows) == 11
    assert set(row["ligand_comp_id"] for row in rows) == set(
        authority.EXACT9_COMPONENTS
    )
    assert sum(int(row["derived_parent_heavy_atom_count"]) for row in rows) == 324
    assert sum(int(row["supporting_parent_heavy_atom_count"]) for row in rows) == 324
    for row in rows:
        assert all(
            _bool(row[field])
            for field in (
                "local_ccd_admitted",
                "component_parent_atom_authority_available",
                "component_parent_bond_order_authority_available",
                "component_parent_graph_valid",
                "parent_heavy_atom_count_matches", "verified",
            )
        )
        assert all(not _bool(row[field]) for field in checker.FALSE_READINESS_FIELDS)
        assert "current11_observed_atom_projection_missing" in row["blocking_reasons"]


def test_two_phase_transaction_failure_emits_header_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_admit = authority._admit_component

    def blocked(repo_root: Path, component: str, audit_row):
        result = real_admit(repo_root, component, audit_row)
        if component != "JUG":
            return result
        row = dict(result.admission_row)
        row.update({
            "verified": False,
            "admission_disposition": "blocked_graph_validation",
            "blocking_reasons": "synthetic_transaction_blocker",
        })
        return dataclasses.replace(result, admission_row=row)

    monkeypatch.setattr(authority, "_admit_component", blocked)
    payloads = authority.build_evidence_payloads(ROOT)
    assert len(_rows(payloads[authority.ATOM_FILE])) == 0
    assert len(_rows(payloads[authority.BOND_FILE])) == 0
    manifest = json.loads(payloads[authority.MANIFEST_FILE])
    assert manifest["transaction_phase_a_passed"] is False
    assert manifest["transaction_authority_materialized"] is False
    assert manifest["outcome"] == "blocked_exact9_parent_component_graph_authority"


def test_failure_matrix_exact24_typed_unique_and_closed() -> None:
    rows = authority.build_failure_matrix()
    assert len(rows) == 24
    assert tuple(row["failure_case"] for row in rows) == checker.EXPECTED_FAILURE_CASES
    assert len({row["mutation_signature"] for row in rows}) == 24
    for row in rows:
        fields = json.loads(row["mutated_fields"])
        assert row["mutated_fields"] == json.dumps(
            fields, sort_keys=True, separators=(",", ":")
        )
        assert row["expected_reasons_verified"]
        assert row["fails_closed"]
        assert row["verified"]
        scenario = dataclasses.replace(authority.BASELINE_SCENARIO, **fields)
        observation = authority.evaluate_failure_scenario(scenario)
        assert set(filter(None, row["expected_reasons"].split(";"))) <= set(
            observation.reasons
        )
    with pytest.raises(TypeError):
        authority.evaluate_failure_scenario(
            dataclasses.replace(authority.BASELINE_SCENARIO, payload_exists=1)
        )


def test_evidence_is_byte_identical_and_manifest_truthful() -> None:
    first = _artifacts()
    second = _artifacts()
    assert first == second
    for name, payload in first.items():
        assert (ROOT / authority.OUTPUT_ROOT / name).read_bytes() == payload
    manifest = json.loads(first[authority.MANIFEST_FILE])
    assert manifest["outcome"] == (
        "exact9_parent_component_graph_authority_materialized"
    )
    assert manifest["exact9_local_ccd_admitted_count"] == 9
    assert manifest["unique_component_parent_atom_row_count"] == 298
    assert manifest["unique_component_parent_bond_row_count"] == 309
    assert manifest["current11_parent_component_graph_coverage_count"] == 11
    assert manifest["current11_sample_expanded_parent_atom_occurrence_count"] == 324
    assert manifest["current11_observed_atom_projection_exact_count"] == 0
    assert manifest["reaction_family_label_available_count"] == 0
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["training_used"] is False
    assert manifest["ready_for_training"] is False
    assert authority.MANIFEST_FILE not in manifest["evidence_sha256"]


def test_exact10_paths_modes_and_safety() -> None:
    assert len(checker.EXACT10) == len(set(checker.EXACT10)) == 10
    assert not any(path.as_posix().startswith("data/raw/") for path in checker.EXACT10)
    assert set(path.name for path in checker.EXACT10[4:]) == set(
        authority.OUTPUT_FILES
    )
    for relative in checker.EXACT10:
        path = ROOT / relative
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_mode & 0o777 == 0o644
        assert relative.suffix.lower() not in checker.FORBIDDEN_SUFFIXES


def test_checker_two_runs_have_identical_stdout() -> None:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "src",
    }
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            (sys.executable, "-B", checker.EXACT10[2].as_posix()),
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stderr == b""
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1]


def test_shared_hermetic_lifecycle_exact4_with_ignored_raw_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert len(_artifact_rows(authority.ADMISSION_FILE)) == 9
        return
    real_copy = lifecycle._copy_exact_paths
    real_capture = lifecycle._capture_state
    observed_states: list[str] = []
    checker_outputs: list[bytes] = []
    targeted_counts: list[int] = []

    def copy_with_raw(source: Path, destination: Path, exact_paths):
        real_copy(source, destination, exact_paths)
        raw_target = destination / authority.CCD_ROOT
        raw_target.mkdir(parents=True, exist_ok=True)
        for component in authority.EXACT9_COMPONENTS:
            source_path = source / authority.CCD_ROOT / f"{component}.cif"
            target_path = raw_target / f"{component}.cif"
            shutil.copyfile(source_path, target_path)
            target_path.chmod(0o644)

    def capture(repository: Path, **kwargs):
        state = real_capture(repository, **kwargs)
        environment = {
            **os.environ,
            NESTED_LIFECYCLE_ENV: "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        }
        targeted = subprocess.run(
            (
                sys.executable, "-m", "pytest", "-q",
                checker.EXACT10[1].as_posix(),
            ),
            cwd=repository,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert targeted.returncode == 0, targeted.stdout + targeted.stderr
        assert targeted.stderr == b""
        match = re.search(rb"(\d+) passed", targeted.stdout)
        assert match
        targeted_counts.append(int(match.group(1)))
        checked = subprocess.run(
            (sys.executable, "-B", checker.EXACT10[2].as_posix()),
            cwd=repository,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert checked.returncode == 0, checked.stdout + checked.stderr
        assert checked.stderr == b""
        observed_states.append(state.lifecycle)
        checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_copy_exact_paths", copy_with_raw)
    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=authority.BASE_COMMIT,
        formal_commit_subject=authority.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert observed_states == list(lifecycle.LIFECYCLES)
    assert len(set(targeted_counts)) == 1
    assert len(set(checker_outputs)) == 1
    assert report.candidate_parent == authority.BASE_COMMIT
    assert report.candidate_subject == authority.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
    assert tuple(tmp_path.iterdir()) == ()
