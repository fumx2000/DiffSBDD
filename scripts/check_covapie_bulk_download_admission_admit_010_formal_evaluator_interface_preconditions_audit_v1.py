#!/usr/bin/env python3
"""Independent checker for the ADMIT_010 evaluator-precondition audit v1."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit as gate,
)


EXPECTED_BASE_COMMIT = "53c7d3ff4a17ce528bcf54ba20f220c3b1758757"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_009 v1"
EXPECTED_BLOCKER = "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"
EXPECTED_NEXT_STEP = "design_covapie_admit_010_leakage_group_assignment_provenance_contract_v1"
EXPECTED_STAGE = "covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_OUTPUT_ROOT = Path("data/derived/covalent_small") / EXPECTED_STAGE
EXPECTED_FILES = (
    "covapie_admit_010_formal_evaluator_precondition_matrix.csv",
    "covapie_admit_010_field_occurrence_inventory.csv",
    "covapie_admit_010_observed_value_inventory.csv",
    "covapie_admit_010_source_boundary_audit.csv",
    "covapie_admit_010_formal_evaluator_issue_readiness_inventory.csv",
    "covapie_admit_010_formal_evaluator_preconditions_manifest.json",
)
EXPECTED_OUTPUT_SHA256 = {
    "covapie_admit_010_formal_evaluator_precondition_matrix.csv": "eaa26be3e624f9c07f2e5f69313f9258b4f6dc33f470b7bf4422da1a5c998a2c",
    "covapie_admit_010_field_occurrence_inventory.csv": "e494e55bdf147985a03d936458577948099b61bd77e220b86a045f4f9337240b",
    "covapie_admit_010_observed_value_inventory.csv": "ac8774eea9942063d7593f8e1de5a084afa93865f14e0e796c8418022fcea3e3",
    "covapie_admit_010_source_boundary_audit.csv": "b28a90a36bddf7b3522637a1374bbeddaf394cb204de198b34bf9edab6182e10",
    "covapie_admit_010_formal_evaluator_issue_readiness_inventory.csv": "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6",
    "covapie_admit_010_formal_evaluator_preconditions_manifest.json": "29df6cdf3b1eb7c1a690610d9fad88055797caba58f27f01f0b7da0d488d4c43",
}

EXPECTED_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_manifest.json",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_issue_inventory.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_runtime_contract.csv",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1/covapie_admit_001_to_009_registry_routing_and_oracle_audit.csv",
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_design_gate_manifest.json",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_issue_inventory.csv",
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_precondition_manifest.json",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_implementation_issue_inventory.csv",
    "src/covalent_ext/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.py",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_final_leakage_group_assignment.csv",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_final_leakage_group_inventory.csv",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/unified_sample_index.csv",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_unified_assignment_merge_issue_inventory.csv",
    "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/covapie_unified_assignment_merge_safety_audit.csv",
    "src/covalent_ext/covapie_unified_leakage_split_materialization_smoke.py",
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/covapie_unified_leakage_split_materialization_smoke_manifest.json",
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/covapie_leakage_group_split_assignment.csv",
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/covapie_sample_split_assignment.csv",
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/covapie_cross_split_leakage_audit.csv",
    "src/covalent_ext/covapie_final_dataset_materialization_smoke.py",
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/covapie_final_dataset_materialization_smoke_manifest.json",
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/covapie_final_dataset_membership.csv",
    "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv",
)
EXPECTED_SOURCE_SHA256 = dict(zip(EXPECTED_SOURCE_PATHS, (
    "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
    "b4d5092949292f27310a05ef2c5c77c8036e7ad0474a15b8a0574bc910931dfc",
    "bb159a201f103a4cc04087978a7ca2a7bec7574fb9fc55d3cc0b059415f679e6",
    "28afebbc6351d10ceeabedb5fdbe99bd3549b784a02682d9875a66b769f12bec",
    "6a3471a08d65e0d0d0f6c6cf258016a670e7f324ab5b9ea4a3b8cff7b1723ba9",
    "79ecb3fb1084ddc161d1bec1a7db664ffbeda71952e31e4233317ecd487905d6",
    "085cb2f2a6bfe9bebe9e503dd10aa0b4d6f9ad754ff99539b1bafb33c78b5444",
    "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "0f78005a11fbab8d4bbbada49ad4cc1b6803f596c566a27264a36246925d48d3",
    "5fcc47a764a8a87e110350359e7c17056773c7ffd659b9094b6433beded2a9f8",
    "2304b5754d8052b4b186981a98c12f259608a3492947e069c2afab84084a0d52",
    "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
    "7c7707f5261461083bda7ab2177a423b608c725c070dafaff558bdf39256211e",
    "3e0f182e192d06be5fe4baa8cfdb2687ee23856ec5cbefbdac9c6bd2b6206212",
    "0609a4e7773c948c232e69fb4dafe5ace59d7bebea3f183f1d0d1629b93741cf",
    "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    "ae18fd8d0ed8bad803126fb65bc947446d99ca0e4c6f42c63927d969f4bacfbc",
    "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326",
    "068095310b4b0ec1d38c27e3b944977066aadd9f9203488ef7fe5bfcd744540c",
    "004df1f1ee9eae632f83cf19ded1b41e7130730316321d925bb9426b98857b42",
    "4e565e670ef09fd78c65c5aa799378f3efbd965dc896c65d37a6896d71c5212e",
    "697f4ad7d4d5afb7598862ad82b93db7f8e6c1aa05ea61a9162cae45a1d59bba",
    "ed62fcf56ad87d8a49743517329c97aa98d3a781562fa403b4b43a9b9ea3ffc3",
    "29ffff244e33e3ec93f2c2b3e5e42a09ce73d7f55019f833e97659301f6a388c",
    "8941aae3350156800ee0f6bbaa8088a3add6b130c9405664786cc0886c0577ce",
    "d173ef39bfc23304a419f37d0e002d3b817aa7261ee61e99ffe362effe1fa865",
    "6f25c8976b295749f3af6407c3bb8ce17cfbda9f18cb967df5fe9b47b480c433",
    "ddf1705176c8680d90e0e216a9af3d1501c6a821764c3e7138a28269e687a977",
    "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
), strict=True))

EXPECTED_PRECONDITION_AREAS = (
    "rule_identity", "evaluation_phase", "candidate_dependency", "context_dependency",
    "historical_success_failure_vocabulary", "current_primary_blocker", "field_occurrence_coverage",
    "observed_value_coverage", "final_vs_provisional_group_distinction",
    "assignment_provenance_availability", "assignment_policy_version_availability",
    "membership_evidence", "pre_split_ordering_evidence", "standalone_pure_memory_feasibility",
    "result_schema_precedent", "issue_transition_policy", "provider_mapping_status",
    "real_evaluation_status", "adapter_runtime_boundary", "admit_011_boundary", "training_boundary",
)
TRUE_READINESS = (
    "admit_010_precondition_audit_complete", "admit_010_rule_identity_verified",
    "admit_010_field_dependency_verified", "admit_010_context_dependency_verified",
    "admit_010_historical_evidence_inventory_complete", "admit_010_pre_split_boundary_audited",
    "admit_010_standalone_pure_memory_interface_feasible", "admit_010_provider_mapping_boundary_preserved",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_010_leakage_group_assignment_provenance_contract_design",
)
FALSE_READINESS = (
    "leakage_group_assignment_provenance_contract_frozen", "leakage_group_id_final_grammar_frozen",
    "leakage_group_id_provider_mapping_validated", "evaluate_admit_010_implemented",
    "Admit010EvaluationResult_implemented", "admit_010_design_oracle_implemented",
    "admit_010_unified_adapter_contract_frozen", "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine", "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started", "evaluate_all_rules_implemented", "combined_candidate_verdict_implemented",
    "real_candidate_evaluation", "ready_for_bulk_download_now", "ready_for_training", "ready_to_train_now",
)


def _git(arguments: Sequence[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, text=text, capture_output=True, check=False)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_path(path: str) -> bool:
    value = Path(path)
    return not value.is_absolute() and bool(value.parts) and ".." not in value.parts and value.parts[0] != "checkpoints" and value.parts[:2] != ("data", "raw")


def _freeze_source_bytes() -> dict[str, bytes]:
    assert len(EXPECTED_SOURCE_PATHS) == len(set(EXPECTED_SOURCE_PATHS)) == 32
    assert tuple(EXPECTED_SOURCE_SHA256) == EXPECTED_SOURCE_PATHS
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, "HEAD"])
    assert subject.returncode == ancestor.returncode == 0 and subject.stdout.strip() == EXPECTED_BASE_SUBJECT
    for path in EXPECTED_SOURCE_PATHS:
        assert _safe_path(path)
        metadata = os.lstat(REPO_ROOT / path)
        tracked = _git(["ls-files", "--error-unmatch", "--", path])
        tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path])
        fields = tree.stdout.split("\t", 1)[0].split()
        assert tracked.returncode == tree.returncode == 0 and len(fields) == 3
        assert fields[0] in {"100644", "100755"} and fields[1] == "blob"
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    result: dict[str, bytes] = {}
    for path in EXPECTED_SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path}"], text=False)
        filesystem = (REPO_ROOT / path).read_bytes()
        assert base.returncode == 0 and type(base.stdout) is bytes
        assert _sha_bytes(base.stdout) == _sha_bytes(filesystem) == EXPECTED_SOURCE_SHA256[path]
        result[path] = filesystem
    return result


def _read_csv(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == expected_columns
        rows = [dict(row) for row in reader]
    assert all(tuple(row) == expected_columns and all(value is not None for value in row.values()) for row in rows)
    return rows


def _validate_output_structure(root: Path) -> None:
    assert root.is_dir() and not root.is_symlink()
    entries = sorted(root.iterdir(), key=lambda path: path.name)
    assert sorted(path.name for path in entries) == sorted(EXPECTED_FILES)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part"}
    for path in entries:
        metadata = os.lstat(path)
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert path.suffix not in forbidden and metadata.st_size <= 5 * 1024 * 1024


def _refresh_hash(root: Path, name: str) -> None:
    manifest_path = root / EXPECTED_FILES[5]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = _sha_bytes((root / name).read_bytes())
    manifest["output_sha256"][name] = digest
    if name == EXPECTED_FILES[4]:
        manifest["issue_inventory_output_sha256"] = digest
        manifest["issue_inventory_byte_identical_to_exact9"] = digest == EXPECTED_SOURCE_SHA256[EXPECTED_SOURCE_PATHS[2]]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1
    return matches[0]


def _validate_materializer_static_contract() -> None:
    production_path = REPO_ROOT / "src/covalent_ext/covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit.py"
    tree = ast.parse(production_path.read_text(encoding="utf-8"), filename=str(production_path))
    preflight = _function_node(tree, "_preflight_output_root")
    atomic = _function_node(tree, "_atomic_write")
    materialize = _function_node(tree, "materialize_audit")
    assert callable(getattr(gate, "_preflight_output_root", None))
    assert callable(getattr(gate, "_atomic_write", None))

    materialize_calls = [node for node in ast.walk(materialize) if isinstance(node, ast.Call)]
    preflight_lines = [node.lineno for node in materialize_calls if _call_name(node) == "_preflight_output_root"]
    atomic_lines = [node.lineno for node in materialize_calls if _call_name(node) == "_atomic_write"]
    assert len(preflight_lines) == len(atomic_lines) == 1 and preflight_lines[0] < atomic_lines[0]
    assert not any(_call_name(node) == "write_bytes" for node in materialize_calls)
    for node in materialize_calls:
        if _call_name(node) not in {"open", "fdopen"}:
            continue
        modes = [argument.value for argument in node.args[1:2] if isinstance(argument, ast.Constant) and isinstance(argument.value, str)]
        modes.extend(
            keyword.value.value
            for keyword in node.keywords
            if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str)
        )
        assert not any(set(mode) & set("wax+") for mode in modes)

    preflight_calls = {_call_name(node) for node in ast.walk(preflight) if isinstance(node, ast.Call)}
    assert {"lstat", "mkdir", "iterdir"} <= preflight_calls
    atomic_calls = {_call_name(node) for node in ast.walk(atomic) if isinstance(node, ast.Call)}
    assert {"mkstemp", "fdopen", "write", "flush", "fsync", "replace", "unlink"} <= atomic_calls
    assert any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(atomic))
    source = inspect.getsource(gate._atomic_write)
    assert 'suffix=".tmp"' in source and "dir=path.parent" in source


def _validate_materializer_output_safety() -> None:
    _validate_materializer_static_contract()
    with tempfile.TemporaryDirectory(prefix="covapie_admit010_checker_") as temporary:
        base = Path(temporary)

        safe = base / "safe"
        gate.materialize_audit(safe)
        assert {entry.name for entry in safe.iterdir()} == set(EXPECTED_FILES)
        assert all(stat.S_ISREG(os.lstat(safe / name).st_mode) and not (safe / name).is_symlink() for name in EXPECTED_FILES)
        assert not any(entry.name.endswith(".tmp") for entry in safe.iterdir())

        existing = base / "existing"
        existing.mkdir()
        for name in EXPECTED_FILES:
            shutil.copy2(REPO_ROOT / EXPECTED_OUTPUT_ROOT / name, existing / name)
        before = {name: _sha_bytes((existing / name).read_bytes()) for name in EXPECTED_FILES}
        gate.materialize_audit(existing)
        assert {name: _sha_bytes((existing / name).read_bytes()) for name in EXPECTED_FILES} == before
        assert not any(entry.name.endswith(".tmp") for entry in existing.iterdir())

        target = base / "external-root-target"
        target.mkdir()
        sentinel = target / "sentinel.txt"
        sentinel.write_text("unchanged", encoding="utf-8")
        root_link = base / "root-link"
        root_link.symlink_to(target, target_is_directory=True)
        try:
            gate.materialize_audit(root_link)
        except ValueError:
            pass
        else:
            raise AssertionError("output-root symlink was accepted")
        assert sentinel.read_text(encoding="utf-8") == "unchanged"
        assert {entry.name for entry in target.iterdir()} == {"sentinel.txt"}

        root_file = base / "root-file"
        root_file.write_text("unchanged", encoding="utf-8")
        try:
            gate.materialize_audit(root_file)
        except ValueError:
            pass
        else:
            raise AssertionError("regular-file output root was accepted")
        assert root_file.read_text(encoding="utf-8") == "unchanged"

        extra = base / "extra"
        extra.mkdir()
        authorized = extra / EXPECTED_FILES[0]
        authorized.write_bytes(b"authorized-before\n")
        unexpected = extra / "unexpected.txt"
        unexpected.write_text("do-not-clean", encoding="utf-8")
        before_authorized = authorized.read_bytes()
        try:
            gate.materialize_audit(extra)
        except ValueError:
            pass
        else:
            raise AssertionError("unexpected output entry was accepted")
        assert authorized.read_bytes() == before_authorized
        assert unexpected.read_text(encoding="utf-8") == "do-not-clean"

        external_output = base / "external-output.csv"
        external_output.write_text("unchanged\n", encoding="utf-8")
        output_link_root = base / "output-link-root"
        output_link_root.mkdir()
        (output_link_root / EXPECTED_FILES[0]).symlink_to(external_output)
        try:
            gate.materialize_audit(output_link_root)
        except ValueError:
            pass
        else:
            raise AssertionError("authorized output symlink was accepted")
        assert external_output.read_text(encoding="utf-8") == "unchanged\n"
        assert {entry.name for entry in output_link_root.iterdir()} == {EXPECTED_FILES[0]}

        output_directory_root = base / "output-directory-root"
        output_directory_root.mkdir()
        (output_directory_root / EXPECTED_FILES[1]).mkdir()
        try:
            gate.materialize_audit(output_directory_root)
        except ValueError:
            pass
        else:
            raise AssertionError("authorized output directory was accepted")
        assert (output_directory_root / EXPECTED_FILES[1]).is_dir()

        assert not any(path.name.endswith(".tmp") for path in base.rglob("*"))


def _validate_disk(root: Path = REPO_ROOT / EXPECTED_OUTPUT_ROOT, *, enforce_frozen_hashes: bool = True) -> dict[str, Any]:
    sources = _freeze_source_bytes()
    _validate_output_structure(root)
    if enforce_frozen_hashes:
        assert {_path.name: _sha_bytes(_path.read_bytes()) for _path in root.iterdir()} == EXPECTED_OUTPUT_SHA256

    preconditions = _read_csv(root / EXPECTED_FILES[0], gate.PRECONDITION_COLUMNS)
    assert len(preconditions) == 21
    assert [row["precondition_id"] for row in preconditions] == [f"PRE_{index:03d}" for index in range(1, 22)]
    assert tuple(row["semantic_area"] for row in preconditions) == EXPECTED_PRECONDITION_AREAS
    assert all(row["audit_passed"] == "true" for row in preconditions)
    incomplete = {"final_vs_provisional_group_distinction", "assignment_policy_version_availability", "provider_mapping_status", "real_evaluation_status"}
    assert {row["semantic_area"] for row in preconditions if row["verified"] == "false"} == incomplete
    assert all(row["blocker_id"] == EXPECTED_BLOCKER for row in preconditions if row["verified"] == "false")

    occurrences = _read_csv(root / EXPECTED_FILES[1], gate.OCCURRENCE_COLUMNS)
    assert len(occurrences) == 401 and [row["occurrence_order"] for row in occurrences] == [str(index) for index in range(1, 402)]
    assert all(row["source_relative_path"] in EXPECTED_SOURCE_SHA256 and row["source_sha256"] == EXPECTED_SOURCE_SHA256[row["source_relative_path"]] for row in occurrences)
    assert all(row["audit_result"] == "observed_without_semantic_equivalence_promotion" for row in occurrences)
    record_ids = {"assignment_id", "group_split_assignment_id", "sample_split_assignment_id"}
    assert all(row["semantic_classification"] == "record_identifier_not_group_identifier" for row in occurrences if row["term"] in record_ids)
    single_axes = {"ligand_graph_group_id", "ligand_scaffold_group_id", "protein_accession_group_id", "protein_exact_sequence_group_id", "protein_sequence_cluster_90_id", "protein_sequence_cluster_50_id"}
    assert all(row["semantic_classification"] == "single_axis_group_not_final_group" for row in occurrences if row["term"] in single_axes)

    observed = _read_csv(root / EXPECTED_FILES[2], gate.OBSERVED_COLUMNS)
    assert len(observed) == 197 and [row["value_order"] for row in observed] == [str(index) for index in range(1, 198)]
    keys = [(row["source_relative_path"], row["field_name"], row["observed_value"]) for row in observed]
    assert len(keys) == len(set(keys))
    assert {row["inferred_exact_builtin_type"] for row in observed} == {"str", "int", "bool"}
    assert all(row["general_grammar_frozen"] == row["provenance_equivalence_inferred"] == "false" and row["value_audit_passed"] == "true" for row in observed)
    assert not any(row["field_name"] == "leakage_group_id" for row in observed)
    final_values = {row["observed_value"] for row in observed if row["field_name"] == "final_leakage_group_id"}
    assert final_values == {f"COVAPIE_LEAKAGE_GROUP_{index:06d}" for index in range(1, 6)}
    assert any(row["lifecycle_status"] == "provisional_status" for row in observed)

    source_rows = _read_csv(root / EXPECTED_FILES[3], gate.SOURCE_BOUNDARY_COLUMNS)
    assert len(source_rows) == 32 and [row["source_order"] for row in source_rows] == [str(index) for index in range(1, 33)]
    assert tuple(row["source_relative_path"] for row in source_rows) == EXPECTED_SOURCE_PATHS
    assert all(row["expected_sha256"] == row["base_tree_sha256"] == row["filesystem_sha256"] == EXPECTED_SOURCE_SHA256[row["source_relative_path"]] for row in source_rows)
    assert all(row["source_boundary_passed"] == "true" and row["non_symlink"] == "true" for row in source_rows)

    issue_path = root / EXPECTED_FILES[4]
    issues = _read_csv(issue_path, gate.ISSUE_COLUMNS)
    assert issue_path.read_bytes() == sources[EXPECTED_SOURCE_PATHS[2]] and len(issues) == 11
    blocker = next(row for row in issues if row["issue_id"] == EXPECTED_BLOCKER)
    coverage = next(row for row in issues if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assert blocker["status"] == "open" and blocker["affected_fields"] == "leakage_group_id" and blocker["affected_rules"] == "ADMIT_010" and blocker["integration_transition"] == "unchanged_open"
    assert coverage["affected_rules"] == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015"

    manifest = json.loads((root / EXPECTED_FILES[5]).read_text(encoding="utf-8"))
    assert type(manifest) is dict and "covapie_admit_010_formal_evaluator_preconditions_manifest.json" not in manifest.get("output_sha256", {})
    assert manifest["stage"] == EXPECTED_STAGE and manifest["base_commit"] == EXPECTED_BASE_COMMIT
    assert manifest["admission_rule_id"] == "ADMIT_010" and manifest["admission_rule_name"] == "leakage_group_assignment_before_split"
    assert manifest["evaluation_phase"] == "pre_final_split" and manifest["candidate_field"] == "leakage_group_id"
    assert manifest["evaluation_context"] == "leakage_group_assignment_provenance_contract"
    assert manifest["required_status"] == "leakage_group_assigned" and manifest["historical_blocking_reason"] == "leakage_group_unassigned"
    assert manifest["primary_unresolved_blocker"] == EXPECTED_BLOCKER and manifest["primary_blocker_status"] == "open"
    assert manifest["canonical_candidate_field"] == "leakage_group_id" and manifest["historical_artifact_field"] == "final_leakage_group_id"
    assert manifest["candidate_to_historical_field_mapping_status"] == "unverified"
    assert manifest["assignment_id_semantics"] == "record_identifier_not_group_identifier"
    assert manifest["duplicate_identity_key_substitution_allowed"] is False and manifest["single_axis_group_substitution_allowed"] is False
    assert manifest["split_assignment_proves_pre_split_assignment"] is False
    assert manifest["future_evaluator_runs_grouping_algorithm"] is False and manifest["future_evaluator_accesses_filesystem_or_split_files"] is False
    assert manifest["source_count"] == 32 and manifest["precondition_row_count"] == 21 and manifest["occurrence_row_count"] == 401 and manifest["observed_value_row_count"] == 197 and manifest["issue_row_count"] == 11
    assert set(manifest["term_search_counts"]) == set(gate.MATCH_QUERIES) and manifest["term_search_counts"]["policy version"] == 0
    assert all(manifest["term_search_counts"][term] > 0 for term in manifest["term_search_counts"] if term != "policy version")
    actual_non_manifest = {name: _sha_bytes((root / name).read_bytes()) for name in EXPECTED_FILES[:5]}
    assert manifest["output_sha256"] == actual_non_manifest
    assert manifest["issue_inventory_byte_identical_to_exact9"] is True and manifest["issue_inventory_output_sha256"] == EXPECTED_SOURCE_SHA256[EXPECTED_SOURCE_PATHS[2]]
    assert all(manifest["readiness"][key] is True and manifest[key] is True for key in TRUE_READINESS)
    assert all(manifest["readiness"][key] is False and manifest[key] is False for key in FALSE_READINESS)
    assert all(value is False for value in manifest["safety"].values())
    assert manifest["recommended_next_step"] == EXPECTED_NEXT_STEP and manifest["all_checks_passed"] is True
    assert not hasattr(gate, "evaluate_admit_010") and not hasattr(gate, "Admit010EvaluationResult")
    return manifest


def main() -> int:
    _validate_materializer_output_safety()
    manifest = _validate_disk()
    assert manifest["ready_for_admit_010_leakage_group_assignment_provenance_contract_design"] is True
    print("ADMIT_010 formal evaluator interface preconditions audit v1: PASS")
    print(f"ready_for_admit_010_leakage_group_assignment_provenance_contract_design={str(manifest['ready_for_admit_010_leakage_group_assignment_provenance_contract_design']).lower()}")
    print(f"primary_blocker_status={manifest['primary_blocker_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
