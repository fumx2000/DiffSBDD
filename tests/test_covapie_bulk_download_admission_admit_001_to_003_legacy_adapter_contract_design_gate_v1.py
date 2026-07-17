from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate
    as gate,
)


CHECKER_PATH = (
    gate.REPO_ROOT
    / "scripts/check_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1.py"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location("phase3_checker", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def snapshot():
    return gate.build_frozen_source_snapshot()


@pytest.fixture(scope="module")
def state(snapshot):
    value = gate.build_phase3_design_state(snapshot)
    assert value["all_checks_passed"] is True
    return value


def _materialize(root: Path) -> dict[str, object]:
    return gate.run_covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate_v1(
        root
    )


def _hashes(root: Path) -> dict[str, str]:
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in gate.OUTPUT_FILES
    }


def test_exact16_order_and_full_sha_constants():
    assert len(gate.SOURCE_PATHS) == 16
    assert len(set(gate.SOURCE_PATHS)) == 16
    assert tuple(gate.SOURCE_SHA256) == gate.SOURCE_PATHS
    assert all(len(value) == 64 for value in gate.SOURCE_SHA256.values())
    assert gate.SOURCE_PATHS[0] == gate.PHASE2_SOURCE_PATH
    assert gate.SOURCE_PATHS[-2:] == (
        gate.PHASE1_ROUTING_PATH,
        gate.PHASE1_RESULT_PATH,
    )


def test_discovered_example_sha256_are_fully_frozen():
    assert gate.SOURCE_SHA256[gate.ADMIT001_EXAMPLES_PATH] == (
        "1654d36a42cd405866ed152750508dbc46ed78371b7ebb25e47e8bfe9c8bbb9e"
    )
    assert gate.SOURCE_SHA256[gate.ADMIT002_EXAMPLES_PATH] == (
        "35ea09ae36ddf2311b1dcf5a313d18e62888c68e542eb068bd98c04900379ce9"
    )
    assert gate.SOURCE_SHA256[gate.ADMIT003_EXAMPLES_PATH] == (
        "64a5ef19ceb0d37f37af65a5638d844e33de997ccfa3af4df61de0779ab75af6"
    )


def test_snapshot_expected_base_and_filesystem_hashes_match(snapshot):
    assert gate.validate_frozen_source_snapshot(snapshot)
    assert tuple(record.relative_path for record in snapshot.records) == gate.SOURCE_PATHS
    for record in snapshot.records:
        assert record.expected_sha256 == record.base_tree_sha256
        assert record.expected_sha256 == record.filesystem_sha256
        assert hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256


def test_base_object_subject_and_successor_lineage():
    subject = subprocess.run(
        ["git", "show", "-s", "--format=%s", gate.EXPECTED_BASE_COMMIT],
        cwd=gate.REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    assert subject == gate.EXPECTED_BASE_SUBJECT
    gate._validate_expected_base_lineage(gate.REPO_ROOT, head_ref="HEAD")


def test_non_descendant_head_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_git = gate._git
    synthetic_non_descendant = "synthetic-non-descendant"
    observed: list[tuple[str, ...]] = []

    def non_descendant_git(
        arguments,
        repo_root,
        *,
        text=True,
    ):
        observed.append(tuple(arguments))
        if arguments == [
            "merge-base",
            "--is-ancestor",
            gate.EXPECTED_BASE_COMMIT,
            synthetic_non_descendant,
        ]:
            return subprocess.CompletedProcess(
                arguments,
                1,
                "",
                "not ancestor",
            )
        return original_git(arguments, repo_root, text=text)

    monkeypatch.setattr(gate, "_git", non_descendant_git)

    with pytest.raises(ValueError, match="not an ancestor"):
        gate._validate_expected_base_lineage(
            gate.REPO_ROOT,
            head_ref=synthetic_non_descendant,
        )

    state = gate.build_phase3_design_state(
        head_ref=synthetic_non_descendant,
    )
    assert state["all_checks_passed"] is False
    assert state["contract_rows"] == []
    assert state["reason_rows"] == []
    assert state["routing_rows"] == []
    assert state["issue_rows"] == []
    assert (
        "merge-base",
        "--is-ancestor",
        gate.EXPECTED_BASE_COMMIT,
        synthetic_non_descendant,
    ) in observed


def test_all_structural_checks_precede_first_source_byte_read(monkeypatch):
    calls: list[Path] = []

    def structural(path: Path, repo_root: Path) -> bool:
        del repo_root
        calls.append(path)
        return path != gate.SOURCE_PATHS[-1]

    def forbidden_read(self: Path) -> bytes:
        raise AssertionError(f"source byte read occurred: {self}")

    monkeypatch.setattr(gate, "_structural_source_check", structural)
    monkeypatch.setattr(Path, "read_bytes", forbidden_read)
    with pytest.raises(ValueError, match="structural"):
        gate.build_frozen_source_snapshot()
    assert tuple(calls) == gate.SOURCE_PATHS


def test_missing_source_structure_fails_closed():
    assert gate._structural_source_check(Path("missing/exact16-source.csv"), gate.REPO_ROOT) is False


def test_symlink_source_structure_fails_closed(tmp_path):
    target = tmp_path / "target"
    target.write_text("victim", encoding="utf-8")
    link = tmp_path / "link"
    link.symlink_to(target)
    assert gate._structural_source_check(link, gate.REPO_ROOT) is False
    assert target.read_text(encoding="utf-8") == "victim"


def test_snapshot_hash_corruption_fails_closed(snapshot):
    corrupted_record = replace(
        snapshot.records[0], content_bytes=snapshot.records[0].content_bytes + b"x"
    )
    corrupted = gate.FrozenSourceSnapshot((corrupted_record, *snapshot.records[1:]))
    assert gate.validate_frozen_source_snapshot(corrupted) is False
    state = gate.build_phase3_design_state(corrupted)
    assert state["all_checks_passed"] is False


def test_legacy_callable_signatures_and_exact_dict_keysets(state):
    shapes = state["predecessor"]["callable_shapes"]
    for rule_id, spec in gate.RULE_SPECS.items():
        assert shapes[rule_id]["parameters"] == spec["parameters"]
        assert shapes[rule_id]["keys"] == spec["keys"]


def test_phase3_gate_import_does_not_import_or_execute_legacy_evaluators() -> None:
    forbidden = (
        gate.ADMIT001_INTEGRATION_PATH.stem,
        gate.ADMIT002_INTEGRATION_PATH.stem,
        gate.ADMIT003_INTEGRATION_PATH.stem,
    )
    module_name = (
        "covalent_ext."
        "covapie_bulk_download_admission_"
        "admit_001_to_003_legacy_adapter_contract_design_gate"
    )
    script = "\n".join(
        (
            "import json",
            "import sys",
            f"sys.path.insert(0, {str(gate.REPO_ROOT / 'src')!r})",
            f"import {module_name}",
            f"forbidden = {forbidden!r}",
            (
                "present = sorted("
                "name.rsplit('.', 1)[-1] "
                "for name in sys.modules "
                "if name.rsplit('.', 1)[-1] in forbidden"
                ")"
            ),
            "print(json.dumps(present))",
        )
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=gate.REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "[]\n"
    assert completed.stderr == ""


def test_adapter_identities_and_rule_names(state):
    rows = {row["admission_rule_id"]: row for row in state["contract_rows"]}
    assert rows["ADMIT_001"]["admission_rule_name"] == "unique_candidate_identity"
    assert rows["ADMIT_001"]["adapter_id"] == "covapie_admit_001_unified_adapter_v1"
    assert rows["ADMIT_002"]["admission_rule_name"] == "valid_pdb_id_format"
    assert rows["ADMIT_002"]["adapter_id"] == "covapie_admit_002_unified_adapter_v1"
    assert rows["ADMIT_003"]["admission_rule_name"] == "ligand_or_het_identity_present"
    assert rows["ADMIT_003"]["adapter_id"] == "covapie_admit_003_unified_adapter_v1"


def test_per_rule_outcome_subsets(state):
    rows = {row["admission_rule_id"]: row for row in state["contract_rows"]}
    assert rows["ADMIT_001"]["allowed_outcomes"] == "passed|blocked|invalid"
    assert rows["ADMIT_002"]["allowed_outcomes"] == "passed|invalid"
    assert rows["ADMIT_003"]["allowed_outcomes"] == "passed|invalid"


def test_exact23_reason_outcome_mapping_order(state):
    observed = tuple(
        (row["admission_rule_id"], row["legacy_blocking_reason"], row["unified_outcome"])
        for row in state["reason_rows"]
    )
    expected = tuple(
        item
        for rule_id, specs in gate.REASON_SPECS.items()
        for reason, outcome in specs
        for item in ((rule_id, reason, outcome),)
    )
    assert len(observed) == 23
    assert observed == expected
    assert all(row["mapping_contract_passed"] == "true" for row in state["reason_rows"])


def test_admit001_invalid_and_blocked_classification(state):
    rows = [row for row in state["reason_rows"] if row["admission_rule_id"] == "ADMIT_001"]
    assert [row["unified_outcome"] for row in rows] == [
        "passed",
        "invalid",
        "invalid",
        "invalid",
        "invalid",
        "invalid",
        "blocked",
        "blocked",
        "blocked",
    ]


def test_admit001_context_prevalidation_reasons_are_excluded(state):
    mapped = {row["legacy_blocking_reason"] for row in state["reason_rows"]}
    assert set(gate.ADMIT001_CONTEXT_PREVALIDATED_REASONS).isdisjoint(mapped)


def test_admit002_has_only_passed_and_invalid(state):
    assert {
        row["unified_outcome"]
        for row in state["reason_rows"]
        if row["admission_rule_id"] == "ADMIT_002"
    } == {"passed", "invalid"}


def test_admit003_has_only_passed_and_invalid(state):
    assert {
        row["unified_outcome"]
        for row in state["reason_rows"]
        if row["admission_rule_id"] == "ADMIT_003"
    } == {"passed", "invalid"}


def test_candidate_non_mapping_and_missing_field_contracts(state):
    rows = state["routing_rows"]
    for rule_id, spec in gate.RULE_SPECS.items():
        projection = {
            row["contract_item"]: row
            for row in rows
            if row["admission_rule_id"] == rule_id
            and row["contract_area"] == "candidate_projection"
        }
        assert projection["candidate_record_type"]["failure_disposition"] == spec["non_mapping_reason"]
        assert projection["required_field"]["failure_disposition"] == spec["missing_reason"]
        assert projection["candidate_record_type"]["legacy_evaluator_called_on_failure"] == "false"
        assert projection["required_field"]["legacy_evaluator_called_on_failure"] == "false"


def test_candidate_projection_identity_extra_field_and_mutation_contracts(state):
    for rule_id in gate.RULE_SPECS:
        items = {
            row["contract_item"]: row["exact_requirement"]
            for row in state["routing_rows"]
            if row["admission_rule_id"] == rule_id
            and row["contract_area"] == "candidate_projection"
        }
        assert "no trim/coerce/normalize/copy" in items["field_value_identity"]
        assert "extra fields" in items["extra_fields"]
        assert "must not be mutated" in items["candidate_mutation"]


def test_admit001_runtime_context_routing_order(state):
    items = [
        row["contract_item"]
        for row in state["routing_rows"]
        if row["admission_rule_id"] == "ADMIT_001"
        and row["contract_area"] == "routing"
    ]
    assert items == [
        "rule_id_and_registration",
        "batch_context_1_mapping",
        "batch_context_2_key_presence",
        "batch_context_3_exact_container",
        "batch_context_4_nonempty",
        "batch_context_5_member_syntax",
        "evaluation_context_6",
        "download_result_context_7",
        "stage_authorization_context_8",
    ]


def test_admit002_and_003_runtime_context_routing_order(state):
    for rule_id in ("ADMIT_002", "ADMIT_003"):
        items = [
            row["contract_item"]
            for row in state["routing_rows"]
            if row["admission_rule_id"] == rule_id
            and row["contract_area"] == "routing"
        ]
        assert items == [
            "rule_id_and_registration",
            "batch_context_1",
            "evaluation_context_2",
            "download_result_context_3",
            "stage_authorization_context_4",
        ]


def test_static_policy_is_not_runtime_caller_context(state):
    for rule_id, spec in gate.RULE_SPECS.items():
        rows = [
            row
            for row in state["routing_rows"]
            if row["admission_rule_id"] == rule_id
            and row["contract_area"] == "static_policy_boundary"
        ]
        assert rows[0]["contract_item"] == spec["static_policy"]
        assert "caller does not repeat" in rows[0]["exact_requirement"]
        assert "no dynamic filesystem load" in rows[0]["exact_requirement"]
        assert rows[1]["contract_item"] == "runtime_evaluation_context"
        assert rows[1]["exact_requirement"].startswith("None")


def test_normalized_validated_and_consumed_field_mapping(state):
    contracts = {row["admission_rule_id"]: row for row in state["contract_rows"]}
    assert "candidate syntax valid" in contracts["ADMIT_001"]["validated_candidate_fields_contract"]
    assert "iff passed" in contracts["ADMIT_002"]["validated_candidate_fields_contract"]
    assert "iff passed" in contracts["ADMIT_003"]["validated_candidate_fields_contract"]
    assert contracts["ADMIT_001"]["consumed_context_items"] == '("batch_candidate_record_ids",)'
    assert contracts["ADMIT_002"]["consumed_context_items"] == "()"
    assert contracts["ADMIT_003"]["consumed_context_items"] == "()"
    assert all(row["evaluator_io_used"] == "false" for row in contracts.values())


def test_pdb_input_form_is_invariant_only(state):
    row = next(row for row in state["contract_rows"] if row["admission_rule_id"] == "ADMIT_002")
    assert row["input_form_contract"] == (
        "invariant_only;passed=>legacy_4_character|extended_12_character;"
        "invalid=>invalid;not_projected"
    )


def test_revised_contract_and_routing_headers_are_exact():
    assert len(gate.CONTRACT_COLUMNS) == 31
    assert gate.CONTRACT_COLUMNS[17:21] == (
        "source_type_failure_reason",
        "source_invariant_failure_reason",
        "unknown_reason_failure_reason",
        "legacy_value_invariant_contract",
    )
    assert gate.CONTRACT_COLUMNS[21:25] == (
        "semantic_oracle_callable",
        "semantic_oracle_parameters",
        "expected_legacy_result_projection",
        "legacy_result_oracle_equivalence_required",
    )
    assert gate.CONTRACT_COLUMNS[25] == "adapter_side_invalid_result_contract"
    assert gate.ROUTING_COLUMNS == (
        "admission_rule_id",
        "contract_order",
        "contract_area",
        "contract_item",
        "exact_requirement",
        "failure_disposition",
        "dispatch_error_reason",
        "legacy_evaluator_called_on_failure",
        "contract_passed",
    )


def test_explicit_execution_precedence_contract_rows(state):
    rows = [
        row
        for row in state["routing_rows"]
        if row["contract_item"] == "execution_precedence"
    ]
    assert len(rows) == 3
    assert tuple(row["admission_rule_id"] for row in rows) == (
        "ADMIT_001",
        "ADMIT_002",
        "ADMIT_003",
    )
    assert all(
        row["exact_requirement"]
        == (
            "1:rule-ID validation|2:known/registered/adapter-ready validation|"
            "3:runtime context routing validation|4:candidate Mapping validation|"
            "5:required candidate-field validation|6:legacy evaluator call|"
            "7:exact legacy-result type/key/field validation|"
            "8:legacy-result semantic invariant and semantic-oracle equivalence validation|"
            "9:reason-to-outcome mapping|"
            "10:UnifiedAdmissionRuleEvaluation construction"
        )
        for row in rows
    )


def test_three_frozen_semantic_oracle_callables_and_sources(state):
    rows = {row["admission_rule_id"]: row for row in state["contract_rows"]}
    assert {
        rule_id: row["semantic_oracle_callable"] for rule_id, row in rows.items()
    } == {
        "ADMIT_001": "evaluate_candidate_record_id_batch_uniqueness",
        "ADMIT_002": "normalize_pdb_identifier",
        "ADMIT_003": "normalize_ligand_comp_id",
    }
    shapes = state["predecessor"]["oracle_shapes"]
    assert shapes["ADMIT_001"]["source_path"] == gate.ADMIT001_DESIGN_PATH
    assert shapes["ADMIT_002"]["source_path"] == gate.ADMIT002_DESIGN_PATH
    assert shapes["ADMIT_003"]["source_path"] == gate.ADMIT003_DESIGN_PATH
    assert all(
        shapes[rule_id]["callable"] != gate.RULE_SPECS[rule_id]["callable"]
        for rule_id in gate.RULE_SPECS
    )


def test_three_semantic_oracle_parameter_contracts(state):
    observed = {
        row["admission_rule_id"]: row["semantic_oracle_parameters"]
        for row in state["contract_rows"]
    }
    assert observed == {
        "ADMIT_001": "candidate_record_id|batch_candidate_record_ids",
        "ADMIT_002": "pdb_id",
        "ADMIT_003": "ligand_comp_id",
    }


def test_three_expected_legacy_result_projections_are_exact(state):
    observed = {
        row["admission_rule_id"]: row["expected_legacy_result_projection"]
        for row in state["contract_rows"]
    }
    assert observed == {
        "ADMIT_001": (
            "admission_rule_id=ADMIT_001;passed=oracle.passed;"
            "normalized_candidate_record_id=oracle.canonical_candidate_record_id;"
            "blocking_reason=oracle.blocking_reason"
        ),
        "ADMIT_002": (
            "admission_rule_id=ADMIT_002;passed=oracle.syntax_valid;"
            "canonical_pdb_id=oracle.canonical_pdb_id;input_form=oracle.input_form;"
            "blocking_reason=oracle.blocking_reason"
        ),
        "ADMIT_003": (
            "admission_rule_id=ADMIT_003;passed=oracle.passed;"
            "canonical_ligand_comp_id=oracle.canonical_ligand_comp_id;"
            "blocking_reason=oracle.blocking_reason"
        ),
    }


def test_oracle_equivalence_is_required_for_all_three_rules(state):
    assert [
        row["legacy_result_oracle_equivalence_required"]
        for row in state["contract_rows"]
    ] == ["true", "true", "true"]


def test_admit001_valid_unique_oracle_rejects_known_wrong_blocked_result(state):
    from covalent_ext import (
        covapie_bulk_download_admission_candidate_record_id_semantics_design_gate
        as semantic_oracle,
    )

    oracle = semantic_oracle.evaluate_candidate_record_id_batch_uniqueness(
        "A", ["A"]
    )
    expected = {
        "admission_rule_id": "ADMIT_001",
        "passed": oracle.passed,
        "normalized_candidate_record_id": oracle.canonical_candidate_record_id,
        "blocking_reason": oracle.blocking_reason,
    }
    known_but_wrong = {
        "admission_rule_id": "ADMIT_001",
        "passed": False,
        "normalized_candidate_record_id": "A",
        "blocking_reason": "candidate_record_id_missing_from_batch",
    }
    assert expected == {
        "admission_rule_id": "ADMIT_001",
        "passed": True,
        "normalized_candidate_record_id": "A",
        "blocking_reason": "",
    }
    assert known_but_wrong != expected
    assert next(
        row["legacy_result_oracle_equivalence_required"]
        for row in state["contract_rows"]
        if row["admission_rule_id"] == "ADMIT_001"
    ) == "true"


def test_admit001_blocked_reason_is_bound_to_actual_batch_state():
    from covalent_ext import (
        covapie_bulk_download_admission_candidate_record_id_semantics_design_gate
        as semantic_oracle,
    )

    missing = semantic_oracle.evaluate_candidate_record_id_batch_uniqueness(
        "A", ["B"]
    )
    repeated = semantic_oracle.evaluate_candidate_record_id_batch_uniqueness(
        "A", ["A", "A"]
    )
    globally_nonunique = (
        semantic_oracle.evaluate_candidate_record_id_batch_uniqueness(
            "A", ["A", "B", "B"]
        )
    )
    assert missing.blocking_reason == "candidate_record_id_missing_from_batch"
    assert repeated.blocking_reason == "candidate_record_id_repeated_in_batch"
    assert globally_nonunique.blocking_reason == (
        "batch_candidate_record_ids_not_globally_unique"
    )


def test_admit002_legacy_input_oracle_derives_canonical_and_input_form():
    from covalent_ext import (
        covapie_bulk_download_admission_pdb_identifier_semantics_design_gate
        as semantic_oracle,
    )

    class StringSubclass(str):
        pass

    ordinary = semantic_oracle.normalize_pdb_identifier("1ABC")
    subclass = semantic_oracle.normalize_pdb_identifier(StringSubclass("1ABC"))
    assert ordinary.syntax_valid is True
    assert ordinary.input_form == "legacy_4_character"
    assert ordinary.canonical_pdb_id == "pdb_00001abc"
    assert ordinary.blocking_reason == ""
    assert subclass.syntax_valid is True
    assert subclass.canonical_pdb_id == ordinary.canonical_pdb_id


def test_admit002_extended_input_oracle_derives_canonical_and_input_form():
    from covalent_ext import (
        covapie_bulk_download_admission_pdb_identifier_semantics_design_gate
        as semantic_oracle,
    )

    oracle = semantic_oracle.normalize_pdb_identifier("PDB_1000ABCD")
    assert oracle.syntax_valid is True
    assert oracle.input_form == "extended_12_character"
    assert oracle.canonical_pdb_id == "pdb_1000abcd"
    assert oracle.blocking_reason == ""


def test_admit002_valid_oracle_rejects_known_wrong_invalid_result(state):
    from covalent_ext import (
        covapie_bulk_download_admission_pdb_identifier_semantics_design_gate
        as semantic_oracle,
    )

    oracle = semantic_oracle.normalize_pdb_identifier("1abc")
    expected = {
        "admission_rule_id": "ADMIT_002",
        "passed": oracle.syntax_valid,
        "canonical_pdb_id": oracle.canonical_pdb_id,
        "input_form": oracle.input_form,
        "blocking_reason": oracle.blocking_reason,
    }
    known_but_wrong = {
        "admission_rule_id": "ADMIT_002",
        "passed": False,
        "canonical_pdb_id": "",
        "input_form": "invalid",
        "blocking_reason": "pdb_id_format_invalid",
    }
    assert expected["passed"] is True
    assert known_but_wrong != expected
    assert next(
        row["legacy_result_oracle_equivalence_required"]
        for row in state["contract_rows"]
        if row["admission_rule_id"] == "ADMIT_002"
    ) == "true"


def test_admit003_valid_oracle_rejects_known_wrong_invalid_result(state):
    from covalent_ext import (
        covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate
        as semantic_oracle,
    )

    oracle = semantic_oracle.normalize_ligand_comp_id("jug")
    expected = {
        "admission_rule_id": "ADMIT_003",
        "passed": oracle.passed,
        "canonical_ligand_comp_id": oracle.canonical_ligand_comp_id,
        "blocking_reason": oracle.blocking_reason,
    }
    known_but_wrong = {
        "admission_rule_id": "ADMIT_003",
        "passed": False,
        "canonical_ligand_comp_id": "",
        "blocking_reason": "LIGAND_COMP_ID_SYNTAX_INVALID",
    }
    assert expected == {
        "admission_rule_id": "ADMIT_003",
        "passed": True,
        "canonical_ligand_comp_id": "JUG",
        "blocking_reason": "",
    }
    assert known_but_wrong != expected
    assert next(
        row["legacy_result_oracle_equivalence_required"]
        for row in state["contract_rows"]
        if row["admission_rule_id"] == "ADMIT_003"
    ) == "true"


def test_semantic_oracle_mismatch_uses_source_invariant_failure(state):
    for row in state["contract_rows"]:
        rule_id = row["admission_rule_id"]
        assert row["source_invariant_failure_reason"] == (
            f"{rule_id}_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID"
        )
        assert row["source_invariant_failure_reason"] != row[
            "unknown_reason_failure_reason"
        ]
        assert row["malformed_result_disposition"] == (
            "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;"
            "no_partial_unified_result"
        )


def test_exact16_context_dispatch_error_reasons(state):
    expected = {
        ("ADMIT_001", "batch_context_1_mapping"): "ADMIT_001_BATCH_CONTEXT_MAPPING_REQUIRED",
        ("ADMIT_001", "batch_context_2_key_presence"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_REQUIRED",
        ("ADMIT_001", "batch_context_3_exact_container"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_EXACT_LIST_OR_TUPLE_REQUIRED",
        ("ADMIT_001", "batch_context_4_nonempty"): "ADMIT_001_BATCH_CANDIDATE_RECORD_IDS_NONEMPTY_REQUIRED",
        ("ADMIT_001", "batch_context_5_member_syntax"): "ADMIT_001_BATCH_CANDIDATE_RECORD_ID_MEMBER_INVALID",
        ("ADMIT_001", "evaluation_context_6"): "ADMIT_001_EVALUATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_001", "download_result_context_7"): "ADMIT_001_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ("ADMIT_001", "stage_authorization_context_8"): "ADMIT_001_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "batch_context_1"): "ADMIT_002_BATCH_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "evaluation_context_2"): "ADMIT_002_EVALUATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "download_result_context_3"): "ADMIT_002_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ("ADMIT_002", "stage_authorization_context_4"): "ADMIT_002_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "batch_context_1"): "ADMIT_003_BATCH_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "evaluation_context_2"): "ADMIT_003_EVALUATION_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "download_result_context_3"): "ADMIT_003_DOWNLOAD_RESULT_CONTEXT_MUST_BE_NONE",
        ("ADMIT_003", "stage_authorization_context_4"): "ADMIT_003_STAGE_AUTHORIZATION_CONTEXT_MUST_BE_NONE",
    }
    observed = {
        (row["admission_rule_id"], row["contract_item"]): row[
            "dispatch_error_reason"
        ]
        for row in state["routing_rows"]
        if row["dispatch_error_reason"]
    }
    assert observed == expected
    assert all(
        row["failure_disposition"]
        == "UNIFIED_ADMISSION_CONTEXT_ROUTING_INVALID"
        and row["legacy_evaluator_called_on_failure"] == "false"
        for row in state["routing_rows"]
        if row["dispatch_error_reason"]
    )


def test_exact_source_type_failure_reasons(state):
    observed = {
        row["admission_rule_id"]: row["source_type_failure_reason"]
        for row in state["contract_rows"]
    }
    assert observed == {
        "ADMIT_001": "ADMIT_001_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "ADMIT_002": "ADMIT_002_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
        "ADMIT_003": "ADMIT_003_UNIFIED_ADAPTER_SOURCE_TYPE_INVALID",
    }


def test_exact_source_invariant_failure_reasons(state):
    observed = {
        row["admission_rule_id"]: row["source_invariant_failure_reason"]
        for row in state["contract_rows"]
    }
    assert observed == {
        "ADMIT_001": "ADMIT_001_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "ADMIT_002": "ADMIT_002_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
        "ADMIT_003": "ADMIT_003_UNIFIED_ADAPTER_SOURCE_INVARIANT_INVALID",
    }


def test_exact_unknown_reason_failure_reasons(state):
    observed = {
        row["admission_rule_id"]: row["unknown_reason_failure_reason"]
        for row in state["contract_rows"]
    }
    assert observed == {
        "ADMIT_001": "ADMIT_001_UNIFIED_ADAPTER_REASON_UNMAPPED",
        "ADMIT_002": "ADMIT_002_UNIFIED_ADAPTER_REASON_UNMAPPED",
        "ADMIT_003": "ADMIT_003_UNIFIED_ADAPTER_REASON_UNMAPPED",
    }
    assert all(
        row["unknown_reason_disposition"]
        == "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;do_not_guess_outcome"
        for row in state["contract_rows"]
    )


def test_admit001_legacy_value_consistency_invariants(state):
    text = next(
        row["legacy_value_invariant_contract"]
        for row in state["contract_rows"]
        if row["admission_rule_id"] == "ADMIT_001"
    )
    assert "normalized_candidate_record_id nonempty exact str and equals original candidate_record_id" in text
    assert "candidate_record_id_missing_from_batch|candidate_record_id_repeated_in_batch|batch_candidate_record_ids_not_globally_unique" in text
    assert "candidate_record_id_not_exact_str|candidate_record_id_empty|candidate_record_id_non_ascii|candidate_record_id_length_out_of_range|candidate_record_id_pattern_invalid" in text
    assert text.endswith("normalized_candidate_record_id empty")


def test_admit002_legacy_value_consistency_invariants(state):
    text = next(
        row["legacy_value_invariant_contract"]
        for row in state["contract_rows"]
        if row["admission_rule_id"] == "ADMIT_002"
    )
    assert "canonical_pdb_id exact str matching ^pdb_[a-z0-9]{8}$" in text
    assert "input_form in legacy_4_character|extended_12_character" in text
    assert "canonical_pdb_id empty,input_form exact invalid" in text
    assert "legacy passed exact bool and equals (mapped outcome == passed)" in text


def test_admit003_legacy_value_consistency_invariants(state):
    text = next(
        row["legacy_value_invariant_contract"]
        for row in state["contract_rows"]
        if row["admission_rule_id"] == "ADMIT_003"
    )
    assert "original ligand_comp_id exact str" in text
    assert "canonical_ligand_comp_id nonempty exact str and equals original ligand_comp_id.upper()" in text
    assert "matches ^[A-Z0-9]{1,32}$" in text
    assert text.endswith("canonical_ligand_comp_id empty")


def test_exact_six_adapter_side_invalid_unified_payloads(state):
    rows = [
        row
        for row in state["routing_rows"]
        if row["contract_item"]
        in (
            "candidate_non_mapping_unified_result",
            "candidate_missing_field_unified_result",
        )
    ]
    assert len(rows) == 6
    for row in rows:
        fields = dict(
            item.split("=", 1) for item in row["exact_requirement"].split(";")
        )
        assert fields["schema_version"] == gate.RESULT_SCHEMA_VERSION
        assert fields["admission_rule_id"] == row["admission_rule_id"]
        assert fields["outcome"] == "invalid"
        assert fields["passed"] == "false"
        assert fields["blocks_candidate"] == "true"
        assert fields["normalized_values"] == "()"
        assert fields["validated_candidate_fields"] == "()"
        assert fields["evaluator_io_used"] == "false"
        assert fields["legacy_evaluator_called"] == "false"
        assert row["legacy_evaluator_called_on_failure"] == "false"


def test_singleton_tuple_text_is_unambiguous_everywhere(state):
    contracts = {row["admission_rule_id"]: row for row in state["contract_rows"]}
    assert contracts["ADMIT_001"]["consumed_candidate_fields"] == '("candidate_record_id",)'
    assert contracts["ADMIT_001"]["consumed_context_items"] == '("batch_candidate_record_ids",)'
    assert contracts["ADMIT_002"]["consumed_candidate_fields"] == '("pdb_id",)'
    assert contracts["ADMIT_002"]["consumed_context_items"] == "()"
    assert contracts["ADMIT_003"]["consumed_candidate_fields"] == '("ligand_comp_id",)'
    assert contracts["ADMIT_003"]["consumed_context_items"] == "()"
    serialized = json.dumps(
        [*state["contract_rows"], *state["routing_rows"]], sort_keys=True
    )
    assert "(candidate_record_id)" not in serialized
    assert "(batch_candidate_record_ids)" not in serialized


def test_revised_routing_row_count_is_exactly_74(state):
    assert len(state["routing_rows"]) == 74


def test_unknown_legacy_reason_fails_closed_without_fallback_row(state):
    assert all(
        row["unknown_reason_disposition"]
        == "fail_closed:UNIFIED_ADMISSION_RULE_ADAPTER_NOT_READY;do_not_guess_outcome"
        for row in state["contract_rows"]
    )
    assert all(row["legacy_blocking_reason"] != "unknown" for row in state["reason_rows"])


def test_issue_transition_exact_replacement_and_count(state):
    source = [dict(row) for row in state["predecessor"]["phase2_issues"].rows]
    current = state["issue_rows"]
    assert len(current) == 12
    assert source[:9] == current[:9]
    assert source[10:] == current[10:]
    assert current[9] == {
        "issue_id": "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING",
        "issue_type": "implementation_pending",
        "affected_fields": "candidate_record_id|pdb_id|ligand_comp_id",
        "affected_rules": "ADMIT_001|ADMIT_002|ADMIT_003",
        "severity": "blocking",
        "status": "open",
        "blocking_scope": "unified_admission_engine",
        "blocking_reason": "UNIFIED_ADMISSION_LEGACY_EVALUATOR_ADAPTER_IMPLEMENTATION_PENDING",
        "issue_origin": gate.STAGE,
        "integration_transition": "semantics_frozen_implementation_pending",
        "issue_count": "1",
    }


def test_provider_and_engine_blockers_remain_open(state):
    issues = {row["issue_id"]: row for row in state["issue_rows"]}
    assert issues["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["issue_count"] == "11"
    assert issues["REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT"]["severity"] == "blocking"
    assert issues["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["status"] == "open"
    assert issues["UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED"]["status"] == "open"


def test_readiness_does_not_overclaim(state):
    _payloads, manifest = gate._payloads(state)
    assert all(manifest[item] is True for item in gate.TRUE_READINESS)
    assert all(manifest[item] is False for item in gate.FALSE_READINESS)
    assert manifest["recommended_next_step"] == gate.RECOMMENDED_NEXT_STEP


def test_phase2_production_sha_and_runtime_registry_are_unchanged(state):
    record = next(record for record in state["source_snapshot"].records if record.relative_path == gate.PHASE2_SOURCE_PATH)
    assert record.filesystem_sha256 == "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978"
    assert gate._registry_literal_keys(gate._ast_document(state["source_snapshot"], gate.PHASE2_SOURCE_PATH)) == ("ADMIT_004",)


def test_payload_materialization_is_byte_deterministic(state):
    first, first_manifest = gate._payloads(state)
    second, second_manifest = gate._payloads(state)
    assert first == second
    assert first_manifest == second_manifest


def test_double_materialization_is_byte_identical(tmp_path):
    root = tmp_path / "outputs"
    _materialize(root)
    first = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    _materialize(root)
    second = {name: (root / name).read_bytes() for name in gate.OUTPUT_FILES}
    assert first == second
    assert not tuple(root.glob("*.tmp"))
    assert not tuple(root.glob("*.part"))


def test_materializer_symlink_victim_fails_closed(tmp_path):
    root = tmp_path / "outputs"
    root.mkdir()
    victim = tmp_path / "victim"
    victim.write_bytes(b"do-not-overwrite")
    (root / gate.CONTRACT_FILENAME).symlink_to(victim)
    with pytest.raises(ValueError, match="unsafe"):
        _materialize(root)
    assert victim.read_bytes() == b"do-not-overwrite"
    assert set(path.name for path in root.iterdir()) == {gate.CONTRACT_FILENAME}


def test_materializer_extra_entry_fails_before_writes(tmp_path):
    root = tmp_path / "outputs"
    root.mkdir()
    extra = root / "extra"
    extra.write_bytes(b"keep")
    with pytest.raises(ValueError, match="unexpected"):
        _materialize(root)
    assert extra.read_bytes() == b"keep"
    assert set(path.name for path in root.iterdir()) == {"extra"}


def test_manifest_has_no_timestamp_absolute_path_or_self_hash(state):
    payloads, manifest = gate._payloads(state)
    text = payloads[gate.MANIFEST_FILENAME].decode("utf-8")
    assert "timestamp" not in text.lower()
    assert str(gate.REPO_ROOT) not in text
    assert gate.MANIFEST_FILENAME not in manifest["output_sha256"]
    assert manifest["output_sha256_excludes_manifest_self_hash"] is True


def test_checker_accepts_default_outputs_directly():
    checker = _load_checker()
    result = checker.check_output_root()
    assert result["all_checks_passed"] is True
    assert result["reason_row_count"] == 23
    assert result["routing_row_count"] == 74
    assert result["context_error_reason_count"] == 16
    assert result["adapter_failure_reason_count"] == 9
    assert result["adapter_side_invalid_payload_row_count"] == 6
    assert result["semantic_oracle_contract_count"] == 3
    assert result["legacy_result_oracle_equivalence_required_count"] == 3
    assert result["active_issue_count"] == 12
    assert result["double_materialization_passed"] is True
    assert result["symlink_victim_passed"] is True
    assert result["output_tamper_fail_closed_passed"] is True


@pytest.mark.parametrize("failure_kind", ["missing", "extra", "hash", "manifest_overclaim", "symlink"])
def test_checker_output_fail_closed_paths(tmp_path, failure_kind):
    checker = _load_checker()
    root = tmp_path / failure_kind
    _materialize(root)
    if failure_kind == "missing":
        (root / gate.CONTRACT_FILENAME).unlink()
    elif failure_kind == "extra":
        (root / "extra.csv").write_text("x\n", encoding="utf-8")
    elif failure_kind == "hash":
        with (root / gate.CONTRACT_FILENAME).open("ab") as handle:
            handle.write(b"corrupt")
    elif failure_kind == "manifest_overclaim":
        path = root / gate.MANIFEST_FILENAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["ready_for_training"] = True
        path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path = root / gate.CONTRACT_FILENAME
        content = path.read_bytes()
        path.unlink()
        victim = tmp_path / "victim"
        victim.write_bytes(content)
        path.symlink_to(victim)
    with pytest.raises((FileNotFoundError, ValueError)):
        checker.check_output_root(root)


def test_production_and_checker_have_no_forbidden_runtime_imports():
    forbidden = {"numpy", "torch", "rdkit", "pandas", "requests", "urllib3"}
    for path in (Path(gate.__file__), CHECKER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        assert forbidden.isdisjoint(imports)


def test_import_smoke_has_no_output_or_materialization_side_effect():
    output_root = gate.REPO_ROOT / gate.DEFAULT_OUTPUT_ROOT
    before = _hashes(output_root)
    command = (
        "import covalent_ext."
        "covapie_bulk_download_admission_admit_001_to_003_legacy_adapter_contract_design_gate;"
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('checker',{str(CHECKER_PATH)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=gate.REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(gate.REPO_ROOT / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    assert completed.stdout == ""
    assert completed.stderr == ""
    assert _hashes(output_root) == before


def test_no_adapter_runtime_registration_or_aggregation_implementation():
    forbidden_attributes = (
        "evaluate_admission_rule",
        "evaluate_all_rules",
        "EVALUATOR_REGISTRY",
        "_adapt_admit_001",
        "_adapt_admit_002",
        "_adapt_admit_003",
    )
    assert all(not hasattr(gate, name) for name in forbidden_attributes)
    source_text = Path(gate.__file__).read_text(encoding="utf-8")
    assert "combined_candidate_verdict(" not in source_text
    assert "cross_rule_precedence(" not in source_text
