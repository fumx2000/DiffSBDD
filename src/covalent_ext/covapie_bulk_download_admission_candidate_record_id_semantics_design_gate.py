"""Step14AU-C1 candidate-record identity semantics design gate.

This metadata-only gate freezes pure in-memory syntax and batch-uniqueness
contracts.  It does not integrate ADMIT_001 into the B2 effective view.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import CodeType
from typing import Any


STAGE = "covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1"
STEP_LABEL = "Step14AU-C1"
PROJECT_NAME = "CovaPIE"
PREVIOUS_STAGE = "covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1"
RECOMMENDED_NEXT_STEP = "integrate_covapie_candidate_record_id_semantics_into_admission_preconditions_v1"
BLOCKED_NEXT_STEP = "resolve_covapie_candidate_record_id_semantics_design_gate_blockers"
MANIFEST_SCHEMA_VERSION = "covapie_candidate_record_id_semantics_design_gate_v1_manifest_v1"

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1")
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1")

SOURCE_SHA256 = {
    str(SOURCE_ROOT / "covapie_pdb_identifier_integrated_rule_matrix.csv"): "99e3a4c8c127af4ac900343a90dfd2eebde73a2f75e9c1a3b27782144858e317",
    str(SOURCE_ROOT / "covapie_pdb_identifier_integrated_field_matrix.csv"): "56388107014e0295c3124bac4660280ff41393e8a8cb6ffa1b50e4028be3c8da",
    str(SOURCE_ROOT / "covapie_pdb_identifier_integrated_context_matrix.csv"): "dc816f74777a5cdced360048ac1cfdc27f711132868f04204d122c9d8f54c5af",
    str(SOURCE_ROOT / "covapie_pdb_identifier_integration_safety_audit.csv"): "fe480434e672a0f455299712248fa807293f73a061ed9d97ad3940bd6ec8c8e8",
    str(SOURCE_ROOT / "covapie_pdb_identifier_integration_issue_inventory.csv"): "8857f22fda3ce281dab13772ee322e9c1af838d7895e410d19084731f9637a21",
    str(SOURCE_ROOT / "covapie_pdb_identifier_semantics_integration_manifest.json"): "abbcbb129c8c26c5bcc6436e69ae55c56ff75bd2742d816ca805ab26a9258865",
}
SOURCE_FILENAMES = tuple(Path(path).name for path in SOURCE_SHA256)

CANONICAL_MASK_PAIRS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
CANDIDATE_RECORD_ID_PATTERN = r"^[A-Za-z0-9](?:[A-Za-z0-9._:-]{0,126}[A-Za-z0-9])?$"
_CANDIDATE_RECORD_ID_RE = re.compile(CANDIDATE_RECORD_ID_PATTERN)

CONTRACT_COLUMNS = (
    "contract_item", "contract_scope", "exact_requirement", "implementation_semantics",
    "evaluator_responsibility", "producer_responsibility", "forbidden_behavior",
    "contract_passed", "blocking_reason",
)
EXAMPLE_COLUMNS = (
    "example_id", "example_scope", "input_type", "input_display", "batch_type", "batch_display",
    "expected_syntax_valid", "expected_batch_valid", "expected_passed",
    "expected_canonical_candidate_record_id", "expected_blocking_reason", "observed_syntax_valid",
    "observed_batch_valid", "observed_passed", "observed_canonical_candidate_record_id",
    "observed_blocking_reason", "example_passed",
)
SOURCE_COLUMNS = (
    "source_relative_path", "tracked_by_git", "regular_file", "symlink", "sha256_expected",
    "sha256_observed", "source_boundary_passed", "blocking_reason",
)
SAFETY_COLUMNS = ("safety_item", "required_status", "observed_status", "safety_passed", "blocking_reason")
ISSUE_COLUMNS = ("issue_id", "issue_type", "severity", "status", "issue_count", "blocking_reason")
CSV_OUTPUTS = (
    "covapie_candidate_record_id_semantics_contract.csv",
    "covapie_candidate_record_id_semantics_examples.csv",
    "covapie_candidate_record_id_source_boundary_audit.csv",
    "covapie_candidate_record_id_safety_audit.csv",
    "covapie_candidate_record_id_issue_inventory.csv",
)
MANIFEST_FILENAME = "covapie_candidate_record_id_semantics_design_manifest.json"

SAFETY_ITEMS = (
    "network_access_used_current_step", "raw_directory_traversed_current_step", "raw_structure_read_current_step",
    "artifact_reference_paths_followed_current_step", "candidate_records_materialized_current_step",
    "candidate_batch_materialized_current_step", "download_queue_materialized_current_step",
    "download_manifest_materialized_current_step", "raw_files_written_current_step", "torch_imported",
    "numpy_imported", "rdkit_used", "biopython_used", "gemmi_used", "dataloader_instantiated",
    "checkpoint_loaded", "model_forward_called", "loss_compute_called", "training_allowed",
)
GATE_FAILURE_SPECS = (
    ("source_boundary", "CANDIDATE_RECORD_ID_SOURCE_BOUNDARY_FAILED", "candidate_record_id_source_boundary_failed"),
    ("source_semantics", "CANDIDATE_RECORD_ID_SOURCE_SEMANTICS_FAILED", "candidate_record_id_source_semantics_failed"),
    ("contract", "CANDIDATE_RECORD_ID_CONTRACT_VALIDATION_FAILED", "candidate_record_id_contract_validation_failed"),
    ("examples", "CANDIDATE_RECORD_ID_EXAMPLE_VALIDATION_FAILED", "candidate_record_id_example_validation_failed"),
    ("safety", "CANDIDATE_RECORD_ID_SAFETY_VALIDATION_FAILED", "candidate_record_id_safety_validation_failed"),
)


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _repo_path(relative_path: Path) -> Path:
    return REPO_ROOT / relative_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tracked_by_git(relative_path: Path) -> bool:
    return subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path.as_posix()], cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(relative_path: Path) -> list[dict[str, str]]:
    with _repo_path(relative_path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@dataclass(frozen=True)
class CandidateRecordIdNormalizationResult:
    input_type: str
    syntax_valid: bool
    canonical_candidate_record_id: str
    blocking_reason: str


@dataclass(frozen=True)
class CandidateRecordIdBatchEvaluationResult:
    candidate_syntax_valid: bool
    batch_type_valid: bool
    batch_non_empty: bool
    all_batch_ids_syntax_valid: bool
    candidate_occurrence_count: int
    batch_ids_unique: bool
    passed: bool
    canonical_candidate_record_id: str
    blocking_reason: str


def normalize_candidate_record_id(value: object) -> CandidateRecordIdNormalizationResult:
    """Validate without coercion, trimming, case folding, or I/O."""
    input_type = type(value).__name__
    if type(value) is not str:
        return CandidateRecordIdNormalizationResult(input_type, False, "", "candidate_record_id_not_exact_str")
    if value == "":
        return CandidateRecordIdNormalizationResult(input_type, False, "", "candidate_record_id_empty")
    if not value.isascii():
        return CandidateRecordIdNormalizationResult(input_type, False, "", "candidate_record_id_non_ascii")
    if not 1 <= len(value) <= 128:
        return CandidateRecordIdNormalizationResult(input_type, False, "", "candidate_record_id_length_out_of_range")
    if _CANDIDATE_RECORD_ID_RE.fullmatch(value) is None:
        return CandidateRecordIdNormalizationResult(input_type, False, "", "candidate_record_id_pattern_invalid")
    return CandidateRecordIdNormalizationResult(input_type, True, value, "")


def evaluate_candidate_record_id_batch_uniqueness(
    candidate_record_id: object, batch_candidate_record_ids: object,
) -> CandidateRecordIdBatchEvaluationResult:
    """Evaluate exactly-one membership and global batch uniqueness in memory."""
    candidate = normalize_candidate_record_id(candidate_record_id)
    batch_type_valid = type(batch_candidate_record_ids) in (list, tuple)
    batch = batch_candidate_record_ids if batch_type_valid else ()
    batch_non_empty = bool(batch) if batch_type_valid else False
    member_results = [normalize_candidate_record_id(value) for value in batch] if batch_type_valid else []
    all_members_valid = all(result.syntax_valid for result in member_results) if batch_type_valid else False
    occurrence_count = (
        sum(type(value) is str and value == candidate_record_id for value in batch)
        if type(candidate_record_id) is str and batch_type_valid else 0
    )
    batch_ids_unique = all_members_valid and len({value for value in batch}) == len(batch) if batch_type_valid else False
    canonical = candidate.canonical_candidate_record_id
    if not candidate.syntax_valid:
        reason = candidate.blocking_reason
    elif not batch_type_valid:
        reason = "batch_candidate_record_ids_invalid_type"
    elif not batch_non_empty:
        reason = "batch_candidate_record_ids_empty"
    elif not all_members_valid:
        reason = "batch_candidate_record_id_member_invalid"
    elif occurrence_count == 0:
        reason = "candidate_record_id_missing_from_batch"
    elif occurrence_count != 1:
        reason = "candidate_record_id_repeated_in_batch"
    elif not batch_ids_unique:
        reason = "batch_candidate_record_ids_not_globally_unique"
    else:
        reason = ""
    return CandidateRecordIdBatchEvaluationResult(
        candidate.syntax_valid, batch_type_valid, batch_non_empty, all_members_valid,
        occurrence_count, batch_ids_unique, reason == "", canonical, reason,
    )


def _contract_specs() -> tuple[tuple[str, str, str, str, str, str, str], ...]:
    base = (
        ("exact_python_str_type", "single_value", "type(value) is str", "exact_type_only", "reject_non_exact_str", "provide_exact_str", "isinstance_or_coercion"),
        ("str_subclass_rejected", "single_value", "str subclasses are invalid", "exact_type_only", "reject_subclasses", "do_not_subclass", "accept_str_subclass"),
        ("ascii_only", "single_value", "ASCII only", "no_unicode_normalization", "reject_non_ascii", "provide_ascii", "unicode_normalization"),
        ("length_minimum", "single_value", "length is at least 1", "one_to_128", "reject_empty", "provide_nonempty", "empty_identifier"),
        ("length_maximum", "single_value", "length is at most 128", "one_to_128", "reject_overlong", "provide_bounded", "truncate_identifier"),
        ("exact_regex", "single_value", CANDIDATE_RECORD_ID_PATTERN, "regex_fullmatch", "validate_exact_pattern", "provide_pattern_valid", "partial_match"),
        ("no_trimming", "single_value", "input is never trimmed", "identity", "preserve_input", "provide_final_value", "trim_then_accept"),
        ("no_case_normalization", "single_value", "input is never case-normalized", "identity", "preserve_case", "provide_case_stable", "lowercase_or_uppercase"),
        ("no_unicode_normalization", "single_value", "input is never Unicode-normalized", "identity", "reject_non_ascii", "provide_ascii", "unicode_normalization"),
        ("identity_canonicalization", "single_value", "canonical value equals input", "identity", "return_input_exactly", "assign_stable_id", "derive_replacement"),
        ("case_sensitive_comparison", "batch", "ABC and abc are distinct", "exact_equality", "compare_exactly", "preserve_case", "case_fold_comparison"),
        ("no_path_semantics", "single_value", "identifier is not a path", "opaque_identifier", "reject_path_characters", "do_not_use_paths", "path_interpretation"),
        ("no_implicit_coercion", "single_value", "no implicit __str__ conversion", "exact_type_only", "reject_non_str", "provide_str", "implicit_conversion"),
        ("record_vs_chemistry_identity", "semantics", "not chemistry or event identity", "opaque_record_key", "do_not_infer_chemistry", "assign_record_key", "chemistry_equivalence"),
        ("separate_from_duplicate_identity_key", "semantics", "not duplicate_identity_key", "separate_contracts", "do_not_deduplicate", "provide_separate_duplicate_key", "replace_admit_009"),
        ("producer_assigned_identity", "producer", "provider assigns ID", "external_producer_contract", "do_not_generate", "reuse_same_source_record_id", "evaluator_assignment"),
        ("no_random_assignment", "producer", "no random UUID", "deterministic_responsibility", "do_not_randomize", "avoid_random_values", "random_uuid"),
        ("no_timestamp_assignment", "producer", "no timestamp assignment", "deterministic_responsibility", "do_not_timestamp", "avoid_runtime_values", "timestamp_id"),
        ("no_batch_position_assignment", "producer", "no batch position assignment", "deterministic_responsibility", "do_not_use_position", "avoid_order_dependent_ids", "batch_index_id"),
        ("list_tuple_exact_batch_type", "batch", "type(batch) is list or tuple", "exact_container_type", "reject_other_containers", "provide_list_or_tuple", "implicit_iterable"),
        ("non_empty_batch", "batch", "batch is non-empty", "nonempty_required", "reject_empty", "provide_nonempty_batch", "empty_batch"),
        ("all_members_syntax_valid", "batch", "every member passes syntax", "per_member_validation", "validate_all_members", "provide_valid_members", "skip_member_validation"),
        ("current_id_occurs_once", "batch", "candidate occurs exactly once", "exact_occurrence_count", "check_count", "include_once", "missing_or_repeated_candidate"),
        ("global_batch_uniqueness", "batch", "all IDs are globally unique", "exact_equality", "check_all_unique", "avoid_duplicates", "deduplicate_silently"),
        ("batch_order_irrelevance", "batch", "order does not affect pass or fail", "order_independent", "do_not_sort", "do_not_rely_on_order", "position_sensitive_result"),
        ("evaluator_performs_no_io", "boundary", "pure in-memory evaluation", "pure_function", "perform_no_io", "supply_values_in_memory", "file_or_network_access"),
        ("syntax_not_provenance", "boundary", "syntax does not prove provenance", "limited_claim", "do_not_claim_provenance", "establish_provenance_elsewhere", "provenance_overclaim"),
        ("uniqueness_not_deduplication", "boundary", "uniqueness does not prove duplicate absence", "limited_claim", "do_not_deduplicate", "run_admit_009_separately", "deduplication_overclaim"),
        ("no_download_permission", "boundary", "gate does not grant download permission", "no_execution_authorization", "do_not_download", "obtain_later_authorization", "download_execution"),
        ("no_training_permission", "boundary", "gate does not grant training permission", "no_execution_authorization", "do_not_train", "complete_feature_audit_first", "training_execution"),
    )
    assert len(base) == 30
    return base


def _candidate_record_id_contract_probe_results() -> dict[str, bool]:
    """Independently probe every frozen contract item against the public helpers."""
    class ProbeStringSubclass(str):
        pass

    valid = normalize_candidate_record_id("HR_0002")
    ordered = evaluate_candidate_record_id_batch_uniqueness("A", ["A", "B", "C"])
    reordered = evaluate_candidate_record_id_batch_uniqueness("A", ["C", "A", "B"])
    invalid_path = normalize_candidate_record_id("A/B")
    invalid_unicode = normalize_candidate_record_id("candidaté")
    helper_symbols = _collect_public_helper_symbols()
    all_symbols = helper_symbols["referenced_names"] | helper_symbols["local_names"] | helper_symbols["string_literals"]
    no_id_generation = not all_symbols.intersection({
        "hash", "uuid4", "uuid", "random", "randint", "randrange", "token_hex", "token_urlsafe",
        "time", "time_ns", "datetime", "now",
    })
    evaluator_pure = not all_symbols.intersection({
        "open", "read_text", "read_bytes", "write_text", "write_bytes", "subprocess", "run", "Popen",
        "urlopen", "requests", "socket",
    })
    evaluator_is_opaque = not all_symbols.intersection({
        "pdb_id", "ligand_comp_id", "covalent_residue", "duplicate_identity_key", "leakage_group_id",
        "raw_target_relative_path", "download_result_status", "observed_sha256", "batch_index",
    })
    results = {
        "exact_python_str_type": not normalize_candidate_record_id(b"A").syntax_valid,
        "str_subclass_rejected": not normalize_candidate_record_id(ProbeStringSubclass("A")).syntax_valid,
        "ascii_only": not invalid_unicode.syntax_valid and invalid_unicode.blocking_reason == "candidate_record_id_non_ascii",
        "length_minimum": not normalize_candidate_record_id("").syntax_valid,
        "length_maximum": not normalize_candidate_record_id("A" * 129).syntax_valid,
        "exact_regex": valid.syntax_valid and not normalize_candidate_record_id("A A").syntax_valid,
        "no_trimming": not normalize_candidate_record_id(" A").syntax_valid and not normalize_candidate_record_id("A ").syntax_valid,
        "no_case_normalization": normalize_candidate_record_id("ABC").canonical_candidate_record_id == "ABC",
        "no_unicode_normalization": not invalid_unicode.syntax_valid,
        "identity_canonicalization": valid.canonical_candidate_record_id == "HR_0002",
        "case_sensitive_comparison": evaluate_candidate_record_id_batch_uniqueness("ABC", ["ABC", "abc"]).passed,
        "no_path_semantics": not invalid_path.syntax_valid,
        "no_implicit_coercion": not normalize_candidate_record_id(1).syntax_valid,
        "record_vs_chemistry_identity": evaluator_is_opaque,
        "separate_from_duplicate_identity_key": evaluator_is_opaque,
        "producer_assigned_identity": no_id_generation,
        "no_random_assignment": no_id_generation,
        "no_timestamp_assignment": no_id_generation,
        "no_batch_position_assignment": no_id_generation,
        "list_tuple_exact_batch_type": ordered.batch_type_valid and evaluate_candidate_record_id_batch_uniqueness("A", {"A"}).blocking_reason == "batch_candidate_record_ids_invalid_type",
        "non_empty_batch": not evaluate_candidate_record_id_batch_uniqueness("A", []).batch_non_empty,
        "all_members_syntax_valid": not evaluate_candidate_record_id_batch_uniqueness("A", ["A", "A A"]).all_batch_ids_syntax_valid,
        "current_id_occurs_once": evaluate_candidate_record_id_batch_uniqueness("A", ["A", "B"]).candidate_occurrence_count == 1,
        "global_batch_uniqueness": not evaluate_candidate_record_id_batch_uniqueness("A", ["A", "B", "B"]).batch_ids_unique,
        "batch_order_irrelevance": ordered.passed and reordered.passed,
        "evaluator_performs_no_io": evaluator_pure,
        "syntax_not_provenance": "provenance" not in all_symbols,
        "uniqueness_not_deduplication": "deduplication" not in all_symbols,
        "no_download_permission": "download" not in all_symbols,
        "no_training_permission": "training" not in all_symbols,
    }
    assert tuple(results) == tuple(item[0] for item in _contract_specs())
    return results


def _collect_code_object_symbols(code: CodeType) -> dict[str, set[str]]:
    """Collect names and string literals recursively without reading source text."""
    referenced_names = set(code.co_names)
    local_names = set(code.co_varnames)
    string_literals: set[str] = set()
    for constant in code.co_consts:
        if isinstance(constant, str):
            string_literals.add(constant)
        elif isinstance(constant, CodeType):
            nested = _collect_code_object_symbols(constant)
            referenced_names.update(nested["referenced_names"])
            local_names.update(nested["local_names"])
            string_literals.update(nested["string_literals"])
    return {
        "referenced_names": referenced_names,
        "local_names": local_names,
        "string_literals": string_literals,
    }


def _collect_public_helper_symbols() -> dict[str, set[str]]:
    normalization = _collect_code_object_symbols(normalize_candidate_record_id.__code__)
    batch = _collect_code_object_symbols(evaluate_candidate_record_id_batch_uniqueness.__code__)
    return {
        key: normalization[key] | batch[key]
        for key in ("referenced_names", "local_names", "string_literals")
    }


def _contract_rows() -> list[dict[str, str]]:
    probes = _candidate_record_id_contract_probe_results()
    return [{
        "contract_item": item, "contract_scope": scope, "exact_requirement": requirement,
        "implementation_semantics": semantics, "evaluator_responsibility": evaluator,
        "producer_responsibility": producer, "forbidden_behavior": forbidden,
        "contract_passed": _bool_text(probes[item]),
        "blocking_reason": "" if probes[item] else f"{item}_contract_probe_failed",
    } for item, scope, requirement, semantics, evaluator, producer, forbidden in _contract_specs()]


def _validate_contract_rows(rows: list[dict[str, str]]) -> bool:
    probes = _candidate_record_id_contract_probe_results()
    expected = _contract_rows()
    return (
        len(rows) == 30 and rows == expected and all(tuple(row.keys()) == CONTRACT_COLUMNS for row in rows)
        and tuple(probes) == tuple(item[0] for item in _contract_specs()) and all(probes.values())
    )


def _display(value: object) -> str:
    if isinstance(value, bytes):
        return repr(value)
    if type(value).__name__ == "generator":
        return "<generator>"
    return str(value).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class _ExampleSpec:
    example_id: str
    example_scope: str
    value: object
    batch_kind: str
    batch_value: object
    expected_syntax_valid: bool
    expected_batch_valid: bool
    expected_passed: bool
    expected_canonical_candidate_record_id: str
    expected_blocking_reason: str


def _example_specs() -> list[_ExampleSpec]:
    long_id = "A" + "x" * 126 + "Z"
    invalid_single = [
        ("empty", ""), ("leading_space", " A"), ("trailing_space", "A "), ("internal_space", "A B"),
        ("real_tab", "A\tB"), ("real_newline", "A\nB"), ("real_carriage_return", "A\rB"),
        ("slash", "A/B"), ("backslash", "A\\B"), ("unicode", "candidaté"), ("leading_underscore", "_A"),
        ("trailing_underscore", "A_"), ("leading_dot", ".A"), ("trailing_dot", "A."),
        ("leading_dash", "-A"), ("trailing_dash", "A-"), ("leading_colon", ":A"), ("trailing_colon", "A:"),
        ("too_long", "A" * 129), ("bytes", b"A"), ("int", 1), ("bool", True), ("none", None),
        ("path", Path("A")), ("str_subclass", _StringSubclass("A")),
    ]
    specs = [
        _ExampleSpec(f"single_valid_{index:02d}", "single", value, "none", None, True, True, True, value, "")
        for index, value in enumerate(("A", "HR_0002", "candidate-001", "candidate.record:01", long_id, "ABC", "abc"), 1)
    ]
    reason_by_name = {
        "empty": "candidate_record_id_empty", "unicode": "candidate_record_id_non_ascii", "too_long": "candidate_record_id_length_out_of_range",
        "bytes": "candidate_record_id_not_exact_str", "int": "candidate_record_id_not_exact_str", "bool": "candidate_record_id_not_exact_str",
        "none": "candidate_record_id_not_exact_str", "path": "candidate_record_id_not_exact_str", "str_subclass": "candidate_record_id_not_exact_str",
    }
    specs.extend(_ExampleSpec(
        f"single_invalid_{name}", "single", value, "none", None, False, True, False, "",
        reason_by_name.get(name, "candidate_record_id_pattern_invalid"),
    ) for name, value in invalid_single)
    specs.extend([
        _ExampleSpec("batch_valid_one", "batch", "A", "value", ["A"], True, True, True, "A", ""),
        _ExampleSpec("batch_valid_many", "batch", "HR_0002", "value", ["A", "HR_0002", "candidate-001"], True, True, True, "HR_0002", ""),
        _ExampleSpec("batch_valid_case_distinct", "batch", "ABC", "value", ["ABC", "abc"], True, True, True, "ABC", ""),
        _ExampleSpec("batch_valid_tuple", "batch", "A", "value", ("A", "B"), True, True, True, "A", ""),
        _ExampleSpec("batch_valid_reordered", "batch", "A", "value", ["B", "A", "C"], True, True, True, "A", ""),
        _ExampleSpec("batch_invalid_scalar", "batch", "A", "value", "A", True, False, False, "A", "batch_candidate_record_ids_invalid_type"),
        _ExampleSpec("batch_invalid_bytes", "batch", "A", "value", b"A", True, False, False, "A", "batch_candidate_record_ids_invalid_type"),
        _ExampleSpec("batch_invalid_set", "batch", "A", "value", {"A"}, True, False, False, "A", "batch_candidate_record_ids_invalid_type"),
        _ExampleSpec("batch_invalid_dict", "batch", "A", "value", {"A": 1}, True, False, False, "A", "batch_candidate_record_ids_invalid_type"),
        _ExampleSpec("batch_invalid_generator", "batch", "A", "generator", ("A",), True, False, False, "A", "batch_candidate_record_ids_invalid_type"),
        _ExampleSpec("batch_invalid_empty", "batch", "A", "value", [], True, False, False, "A", "batch_candidate_record_ids_empty"),
        _ExampleSpec("batch_invalid_missing", "batch", "A", "value", ["B"], True, True, False, "A", "candidate_record_id_missing_from_batch"),
        _ExampleSpec("batch_invalid_repeated_candidate", "batch", "A", "value", ["A", "A"], True, True, False, "A", "candidate_record_id_repeated_in_batch"),
        _ExampleSpec("batch_invalid_other_repeated", "batch", "A", "value", ["A", "B", "B"], True, True, False, "A", "batch_candidate_record_ids_not_globally_unique"),
        _ExampleSpec("batch_invalid_member", "batch", "A", "value", ["A", "B B"], True, False, False, "A", "batch_candidate_record_id_member_invalid"),
        _ExampleSpec("batch_invalid_non_str_member", "batch", "A", "value", ["A", 1], True, False, False, "A", "batch_candidate_record_id_member_invalid"),
        _ExampleSpec("batch_invalid_candidate_syntax", "batch", "A A", "value", ["A A"], False, False, False, "", "candidate_record_id_pattern_invalid"),
        _ExampleSpec("batch_invalid_candidate_syntax_valid_batch", "batch", "A A", "value", ["B"], False, True, False, "", "candidate_record_id_pattern_invalid"),
    ])
    return specs


def _example_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for spec in _example_specs():
        batch = (value for value in spec.batch_value) if spec.batch_kind == "generator" else spec.batch_value
        single = normalize_candidate_record_id(spec.value)
        if spec.example_scope == "single":
            observed_syntax, observed_batch, observed_passed = single.syntax_valid, True, single.syntax_valid
            canonical, reason, batch_type, batch_display = single.canonical_candidate_record_id, single.blocking_reason, "", ""
        else:
            evaluation = evaluate_candidate_record_id_batch_uniqueness(spec.value, batch)
            observed_syntax, observed_batch, observed_passed = evaluation.candidate_syntax_valid, evaluation.batch_type_valid and evaluation.batch_non_empty and evaluation.all_batch_ids_syntax_valid, evaluation.passed
            canonical, reason, batch_type, batch_display = evaluation.canonical_candidate_record_id, evaluation.blocking_reason, type(batch).__name__, _display(batch)
        expected = (
            _bool_text(spec.expected_syntax_valid), _bool_text(spec.expected_batch_valid), _bool_text(spec.expected_passed),
            spec.expected_canonical_candidate_record_id, spec.expected_blocking_reason,
        )
        observed = (_bool_text(observed_syntax), _bool_text(observed_batch), _bool_text(observed_passed), canonical, reason)
        row = {
            "example_id": spec.example_id, "example_scope": spec.example_scope, "input_type": type(spec.value).__name__, "input_display": _display(spec.value),
            "batch_type": batch_type, "batch_display": batch_display,
            "expected_syntax_valid": expected[0], "expected_batch_valid": expected[1], "expected_passed": expected[2],
            "expected_canonical_candidate_record_id": expected[3], "expected_blocking_reason": expected[4], "observed_syntax_valid": observed[0],
            "observed_batch_valid": _bool_text(observed_batch), "observed_passed": _bool_text(observed_passed),
            "observed_canonical_candidate_record_id": observed[3], "observed_blocking_reason": observed[4],
            "example_passed": _bool_text(expected == observed),
        }
        rows.append(row)
    return rows


def _validate_example_rows(rows: list[dict[str, str]]) -> bool:
    expected = _example_rows()
    return len(rows) == len(expected) and rows == expected and all(tuple(row.keys()) == EXAMPLE_COLUMNS for row in rows) and all(row["example_passed"] == "true" for row in rows)


def _source_paths() -> tuple[Path, ...]:
    return tuple(SOURCE_ROOT / name for name in SOURCE_FILENAMES)


def _source_boundary_rows() -> list[dict[str, str]]:
    rows = []
    for path in _source_paths():
        absolute = _repo_path(path)
        observed = _sha256(absolute) if absolute.is_file() and not absolute.is_symlink() else ""
        passed = _tracked_by_git(path) and absolute.is_file() and not absolute.is_symlink() and observed == SOURCE_SHA256[path.as_posix()]
        rows.append({
            "source_relative_path": path.as_posix(), "tracked_by_git": _bool_text(_tracked_by_git(path)),
            "regular_file": _bool_text(absolute.is_file()), "symlink": _bool_text(absolute.is_symlink()),
            "sha256_expected": SOURCE_SHA256[path.as_posix()], "sha256_observed": observed,
            "source_boundary_passed": _bool_text(passed), "blocking_reason": "" if passed else "source_boundary_failed",
        })
    return rows


def _validate_source_boundary_rows(rows: list[dict[str, str]]) -> bool:
    expected_paths = [path.as_posix() for path in _source_paths()]
    return (
        len(rows) == 6 and [row.get("source_relative_path") for row in rows] == expected_paths
        and all(tuple(row.keys()) == SOURCE_COLUMNS for row in rows)
        and all(row["tracked_by_git"] == "true" and row["regular_file"] == "true" and row["symlink"] == "false"
                and row["sha256_expected"] == SOURCE_SHA256[row["source_relative_path"]]
                and row["sha256_observed"] == SOURCE_SHA256[row["source_relative_path"]]
                and row["source_boundary_passed"] == "true" and row["blocking_reason"] == "" for row in rows)
    )


def _load_source() -> dict[str, Any]:
    return {
        "rule_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[0]),
        "field_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[1]),
        "context_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[2]),
        "safety_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[3]),
        "issue_rows": _read_csv(SOURCE_ROOT / SOURCE_FILENAMES[4]),
        "manifest": json.loads(_repo_path(SOURCE_ROOT / SOURCE_FILENAMES[5]).read_text(encoding="utf-8")),
    }


def _validate_source_semantics(source: dict[str, Any]) -> bool:
    manifest = source["manifest"]
    issues = source["issue_rows"]
    admit_001 = next((row for row in source["rule_rows"] if row.get("admission_rule_id") == "ADMIT_001"), None)
    candidate_field = next((row for row in source["field_rows"] if row.get("field_name") == "candidate_record_id"), None)
    candidate_context = next((row for row in source["context_rows"] if row.get("context_item") == "candidate_record_id_contract"), None)
    pdb_rule = next((row for row in source["rule_rows"] if row.get("admission_rule_id") == "ADMIT_002"), None)
    pdb_field = next((row for row in source["field_rows"] if row.get("field_name") == "pdb_id"), None)
    pdb_context = next((row for row in source["context_rows"] if row.get("context_item") == "pdb_id_format_contract"), None)
    return (
        manifest.get("stage") == PREVIOUS_STAGE and manifest.get("step_label") == "Step14AU-B2"
        and manifest.get("all_checks_passed") is True
        and manifest.get("pdb_identifier_semantics_integrated") is True and manifest.get("remaining_issue_count") == 12
        and manifest.get("canonical_mask_pairs") == [list(pair) for pair in CANONICAL_MASK_PAIRS]
        and manifest.get("canonical_mask_task_count") == 5 and manifest.get("ready_to_train_now") is False
        and manifest.get("blocking_reasons") == [
            "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED", "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "COVALENT_EVIDENCE_ENUM_UNRESOLVED", "COVALENT_RESIDUE_ATOM_NAME_NORMALIZATION_UNRESOLVED",
            "COVALENT_RESIDUE_IDENTITY_SEMANTICS_UNRESOLVED", "DOWNLOAD_INTEGRITY_VALIDATION_CONTRACT_UNRESOLVED",
            "DOWNLOAD_RESULT_STATUS_ENUM_UNRESOLVED", "DUPLICATE_IDENTITY_KEY_SEMANTICS_UNRESOLVED",
            "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED", "LIGAND_COMP_ID_SEMANTICS_UNRESOLVED",
            "RAW_TARGET_CONTEXT_CONTRACT_UNRESOLVED", "TOPOLOGY_DISPOSITION_ENUM_UNRESOLVED",
        ]
        and manifest["blocking_reasons"][0] == "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED"
        and "PDB_ID_FORMAT_SEMANTICS_UNRESOLVED" not in manifest["blocking_reasons"]
        and admit_001 is not None and all(admit_001.get(key) == value for key, value in {
            "candidate_field_dependencies": "candidate_record_id", "batch_context_dependencies": "batch_candidate_record_ids",
            "evaluation_context_dependencies": "candidate_record_id_contract", "semantics_complete": "false",
            "deterministic_evaluation_possible_now": "false", "implementation_disposition": "interface_only_pending_semantics",
            "blocking_reasons": "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED",
        }.items())
        and candidate_field is not None and all(candidate_field.get(key) == value for key, value in {
            "dependent_rules": "ADMIT_001", "batch_context_required": "true",
            "evaluation_context_dependencies": "candidate_record_id_contract", "implementation_semantics_complete": "false",
            "blocking_reasons": "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED",
        }.items())
        and candidate_context is not None and all(candidate_context.get(key) == value for key, value in {
            "required_by_rules": "ADMIT_001", "deterministic_now": "false", "exact_contract_defined": "false",
            "implementation_ready": "false", "blocking_reasons": "CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED",
        }.items())
        and pdb_rule is not None and pdb_rule.get("semantics_complete") == "true"
        and pdb_field is not None and pdb_field.get("implementation_semantics_complete") == "true"
        and pdb_context is not None and pdb_context.get("implementation_ready") == "true"
        and len(issues) == 12 and [row.get("issue_id") for row in issues] == manifest["blocking_reasons"]
        and manifest.get("ready_for_admission_evaluator_rule_logic_implementation") is False
        and manifest.get("ready_for_real_candidate_evaluation") is False
        and manifest.get("ready_for_bulk_download_now") is False and manifest.get("ready_for_training") is False
    )


def _safety_rows() -> list[dict[str, str]]:
    return [{"safety_item": item, "required_status": "false", "observed_status": "false", "safety_passed": "true", "blocking_reason": ""} for item in SAFETY_ITEMS]


def _validate_safety_rows(rows: list[dict[str, str]]) -> bool:
    return rows == _safety_rows() and all(tuple(row.keys()) == SAFETY_COLUMNS for row in rows)


def _issue_rows(section_status: tuple[tuple[str, bool], ...]) -> list[dict[str, str]]:
    failures = []
    for section, issue_id, reason in GATE_FAILURE_SPECS:
        if not dict(section_status)[section]:
            failures.append({"issue_id": issue_id, "issue_type": "candidate_record_id_semantics_design_gate_failure", "severity": "blocking", "status": "open", "issue_count": "1", "blocking_reason": reason})
    if failures:
        return failures
    return [{"issue_id": "NO_ISSUES", "issue_type": "no_candidate_record_id_semantics_design_issues", "severity": "none", "status": "no_issues", "issue_count": "0", "blocking_reason": ""}]


def _build_materialization(
    source: dict[str, Any], *, source_rows: list[dict[str, str]] | None = None,
    contract_rows: list[dict[str, str]] | None = None, example_rows: list[dict[str, str]] | None = None,
    safety_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    source_rows = _source_boundary_rows() if source_rows is None else source_rows
    contract_rows = _contract_rows() if contract_rows is None else contract_rows
    example_rows = _example_rows() if example_rows is None else example_rows
    safety_rows = _safety_rows() if safety_rows is None else safety_rows
    statuses = (
        ("source_boundary", _validate_source_boundary_rows(source_rows)),
        ("source_semantics", _validate_source_semantics(source)),
        ("contract", _validate_contract_rows(contract_rows)),
        ("examples", _validate_example_rows(example_rows)),
        ("safety", _validate_safety_rows(safety_rows)),
    )
    return {
        "source_rows": source_rows, "contract_rows": contract_rows, "example_rows": example_rows,
        "safety_rows": safety_rows, "issue_rows": _issue_rows(statuses),
        "all_source_boundary_checks_passed": dict(statuses)["source_boundary"],
        "all_source_semantics_checks_passed": dict(statuses)["source_semantics"],
        "all_contract_checks_passed": dict(statuses)["contract"],
        "all_example_checks_passed": dict(statuses)["examples"],
        "all_safety_checks_passed": dict(statuses)["safety"],
        "all_checks_passed": all(passed for _, passed in statuses),
    }


def _write_outputs(root: Path, result: dict[str, Any]) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    outputs = (
        (CSV_OUTPUTS[0], CONTRACT_COLUMNS, result["contract_rows"]),
        (CSV_OUTPUTS[1], EXAMPLE_COLUMNS, result["example_rows"]),
        (CSV_OUTPUTS[2], SOURCE_COLUMNS, result["source_rows"]),
        (CSV_OUTPUTS[3], SAFETY_COLUMNS, result["safety_rows"]),
        (CSV_OUTPUTS[4], ISSUE_COLUMNS, result["issue_rows"]),
    )
    for name, columns, rows in outputs:
        _write_csv(root / name, columns, rows)
    return {name: _sha256(root / name) for name in CSV_OUTPUTS}


def _manifest_payload(result: dict[str, Any], output_sha256: dict[str, str]) -> dict[str, Any]:
    return {
        "stage": STAGE, "step_label": STEP_LABEL, "project_name": PROJECT_NAME,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION, "previous_stage": PREVIOUS_STAGE,
        "source_read_boundary": "only_step14au_b2_six_committed_metadata_outputs", "source_input_count": 6,
        "source_input_sha256": SOURCE_SHA256, "output_files": [*CSV_OUTPUTS, MANIFEST_FILENAME],
        "output_file_count": 6, "non_manifest_output_count": 5, "output_sha256": output_sha256,
        "canonical_mask_pairs": [list(pair) for pair in CANONICAL_MASK_PAIRS], "canonical_mask_task_count": 5,
        "resolved_design_issue_ids": ["CANDIDATE_RECORD_ID_SEMANTICS_UNRESOLVED"],
        "upstream_effective_issue_count": 12, "expected_post_integration_issue_count": 11,
        "candidate_record_id_semantics_frozen": result["all_checks_passed"],
        "candidate_record_id_semantics_integrated": False,
        "integration_applied_current_step": False,
        "admit_001_rule_logic_ready": False,
        "candidate_record_id_syntax_contract_ready": result["all_checks_passed"],
        "candidate_record_id_batch_uniqueness_contract_ready": result["all_checks_passed"],
        "ready_for_candidate_record_id_semantics_integration": result["all_checks_passed"],
        "ready_for_admission_evaluator_interface_implementation": result["all_checks_passed"],
        "ready_for_admission_evaluator_rule_logic_implementation": False,
        "ready_for_real_candidate_evaluation": False, "ready_for_bulk_download_now": False,
        "ready_for_training": False, "ready_to_train_now": False,
        "feature_semantics_audit_required_before_training": True,
        "network_access_used_current_step": False, "raw_structure_read_current_step": False,
        "candidate_records_materialized_current_step": False, "download_queue_materialized_current_step": False,
        "all_source_boundary_checks_passed": result["all_source_boundary_checks_passed"],
        "all_source_semantics_checks_passed": result["all_source_semantics_checks_passed"],
        "all_contract_checks_passed": result["all_contract_checks_passed"],
        "all_example_checks_passed": result["all_example_checks_passed"],
        "all_safety_checks_passed": result["all_safety_checks_passed"], "all_checks_passed": result["all_checks_passed"],
        "blocking_reasons": [row["issue_id"] for row in result["issue_rows"] if row["issue_id"] != "NO_ISSUES"],
        "recommended_next_step": RECOMMENDED_NEXT_STEP if result["all_checks_passed"] else BLOCKED_NEXT_STEP,
    }


def run_covapie_bulk_download_admission_candidate_record_id_semantics_design_gate_v1(
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Write only the six deterministic C1 design outputs."""
    result = _build_materialization(_load_source())
    output_sha256 = _write_outputs(output_root, result)
    manifest = _manifest_payload(result, output_sha256)
    (output_root / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
