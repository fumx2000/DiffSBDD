"""Read-only ADMIT_010 formal-evaluator interface preconditions audit v1.

This gate audits committed metadata only.  It does not define the future
evaluator/result type, map a provider field, run grouping or splitting, read
raw structures, or change the Exact9 runtime.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STEP = "ADMIT_010 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1"
EXPECTED_BASE_COMMIT = "53c7d3ff4a17ce528bcf54ba20f220c3b1758757"
EXPECTED_BASE_SUBJECT = "add CovaPIE unified admission runtime for ADMIT_001 to ADMIT_009 v1"
MANIFEST_SCHEMA_VERSION = "covapie_admit_010_formal_evaluator_preconditions_manifest_v1"
PRIMARY_BLOCKER = "LEAKAGE_GROUP_ASSIGNMENT_PROVENANCE_UNRESOLVED"
RECOMMENDED_NEXT_STEP = "design_covapie_admit_010_leakage_group_assignment_provenance_contract_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

RUNTIME_ROOT = Path("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1")
DESIGN_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1")
IMPLEMENTATION_ROOT = Path("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1")
ASSIGNMENT_ROOT = Path("data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0")
SPLIT_ROOT = Path("data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0")
FINAL_ROOT = Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0")

SOURCE_PATHS = tuple(Path(value) for value in (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py",
    str(RUNTIME_ROOT / "covapie_admit_001_to_009_runtime_manifest.json"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_009_runtime_issue_inventory.csv"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_009_runtime_contract.csv"),
    str(RUNTIME_ROOT / "covapie_admit_001_to_009_registry_routing_and_oracle_audit.csv"),
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    str(DESIGN_ROOT / "covapie_bulk_download_admission_design_gate_manifest.json"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_rule_registry.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_schema_contract.csv"),
    str(DESIGN_ROOT / "covapie_bulk_download_admission_issue_inventory.csv"),
    "src/covalent_ext/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_implementation_precondition_manifest.json"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_rule_executability_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_field_semantics_matrix.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_evaluation_context_contract.csv"),
    str(IMPLEMENTATION_ROOT / "covapie_bulk_download_admission_implementation_issue_inventory.csv"),
    "src/covalent_ext/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.py",
    str(ASSIGNMENT_ROOT / "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_manifest.json"),
    str(ASSIGNMENT_ROOT / "covapie_final_leakage_group_assignment.csv"),
    str(ASSIGNMENT_ROOT / "covapie_final_leakage_group_inventory.csv"),
    str(ASSIGNMENT_ROOT / "unified_sample_index.csv"),
    str(ASSIGNMENT_ROOT / "covapie_unified_assignment_merge_issue_inventory.csv"),
    str(ASSIGNMENT_ROOT / "covapie_unified_assignment_merge_safety_audit.csv"),
    "src/covalent_ext/covapie_unified_leakage_split_materialization_smoke.py",
    str(SPLIT_ROOT / "covapie_unified_leakage_split_materialization_smoke_manifest.json"),
    str(SPLIT_ROOT / "covapie_leakage_group_split_assignment.csv"),
    str(SPLIT_ROOT / "covapie_sample_split_assignment.csv"),
    str(SPLIT_ROOT / "covapie_cross_split_leakage_audit.csv"),
    "src/covalent_ext/covapie_final_dataset_materialization_smoke.py",
    str(FINAL_ROOT / "covapie_final_dataset_materialization_smoke_manifest.json"),
    str(FINAL_ROOT / "covapie_final_dataset_membership.csv"),
    str(FINAL_ROOT / "final_dataset_index.csv"),
))
SOURCE_SHA256 = dict(zip(SOURCE_PATHS, (
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

(
    RUNTIME_SOURCE_PATH, RUNTIME_MANIFEST_PATH, RUNTIME_ISSUE_PATH,
    RUNTIME_CONTRACT_PATH, RUNTIME_REGISTRY_PATH, DESIGN_SOURCE_PATH,
    DESIGN_MANIFEST_PATH, RULE_REGISTRY_PATH, SCHEMA_CONTRACT_PATH,
    DESIGN_ISSUE_PATH, IMPLEMENTATION_SOURCE_PATH, IMPLEMENTATION_MANIFEST_PATH,
    RULE_EXECUTABILITY_PATH, FIELD_SEMANTICS_PATH, EVALUATION_CONTEXT_PATH,
    IMPLEMENTATION_ISSUE_PATH, ASSIGNMENT_SOURCE_PATH, ASSIGNMENT_MANIFEST_PATH,
    ASSIGNMENT_PATH, GROUP_INVENTORY_PATH, UNIFIED_SAMPLE_INDEX_PATH,
    ASSIGNMENT_ISSUE_PATH, ASSIGNMENT_SAFETY_PATH, SPLIT_SOURCE_PATH,
    SPLIT_MANIFEST_PATH, GROUP_SPLIT_PATH, SAMPLE_SPLIT_PATH,
    CROSS_SPLIT_PATH, FINAL_SOURCE_PATH, FINAL_MANIFEST_PATH,
    FINAL_MEMBERSHIP_PATH, FINAL_INDEX_PATH,
) = SOURCE_PATHS

MATCH_QUERIES = {
    "ADMIT_010": ("ADMIT_010",),
    "leakage_group_assignment_before_split": ("leakage_group_assignment_before_split",),
    "leakage_group_id": ("leakage_group_id",),
    "final_leakage_group_id": ("final_leakage_group_id",),
    "leakage_group_assignment_provenance_contract": ("leakage_group_assignment_provenance_contract",),
    "leakage_group_assigned": ("leakage_group_assigned",),
    "leakage_group_unassigned": ("leakage_group_unassigned",),
    PRIMARY_BLOCKER: (PRIMARY_BLOCKER,),
    "assignment_id": ("assignment_id",),
    "assignment policy": ("assignment_policy", "assignment policy"),
    "policy version": ("policy_version", "policy version"),
    "group_order": ("group_order",),
    "member_count": ("member_count",),
    "member_sample_index_row_ids": ("member_sample_index_row_ids",),
    "sample_index_row_id": ("sample_index_row_id",),
    "final_leakage_group_status": ("final_leakage_group_status",),
    "source_stage_composition": ("source_stage_composition",),
    "split_assignment": ("split_assignment",),
    "group_split_assignment_id": ("group_split_assignment_id",),
    "sample_split_assignment_id": ("sample_split_assignment_id",),
    "ligand_graph_group_id": ("ligand_graph_group_id",),
    "ligand_scaffold_group_id": ("ligand_scaffold_group_id",),
    "protein_accession_group_id": ("protein_accession_group_id",),
    "protein_exact_sequence_group_id": ("protein_exact_sequence_group_id",),
    "protein_sequence_cluster_90_id": ("protein_sequence_cluster_90_id",),
    "protein_sequence_cluster_50_id": ("protein_sequence_cluster_50_id",),
}

PRECONDITION_FILENAME = "covapie_admit_010_formal_evaluator_precondition_matrix.csv"
OCCURRENCE_FILENAME = "covapie_admit_010_field_occurrence_inventory.csv"
OBSERVED_FILENAME = "covapie_admit_010_observed_value_inventory.csv"
SOURCE_BOUNDARY_FILENAME = "covapie_admit_010_source_boundary_audit.csv"
ISSUE_FILENAME = "covapie_admit_010_formal_evaluator_issue_readiness_inventory.csv"
MANIFEST_FILENAME = "covapie_admit_010_formal_evaluator_preconditions_manifest.json"
CSV_OUTPUTS = (PRECONDITION_FILENAME, OCCURRENCE_FILENAME, OBSERVED_FILENAME, SOURCE_BOUNDARY_FILENAME, ISSUE_FILENAME)
OUTPUT_FILES = (*CSV_OUTPUTS, MANIFEST_FILENAME)

PRECONDITION_COLUMNS = (
    "precondition_id", "semantic_area", "required_contract", "observed_contract",
    "source_evidence", "verified", "blocker_id", "design_disposition", "audit_passed",
)
OCCURRENCE_COLUMNS = (
    "occurrence_order", "term", "source_relative_path", "source_sha256", "source_kind",
    "row_key_function_location", "occurrence_role", "semantic_classification",
    "current_authoritative_status", "usable_by_future_evaluator", "audit_result",
)
OBSERVED_COLUMNS = (
    "value_order", "source_relative_path", "source_sha256", "field_name", "observed_value",
    "inferred_exact_builtin_type", "empty_value", "null_like", "lifecycle_status",
    "general_grammar_frozen", "provenance_equivalence_inferred", "value_audit_passed",
)
SOURCE_BOUNDARY_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "boundary_necessity",
    "tracked", "base_tree_blob", "filesystem_regular", "non_symlink", "expected_sha256",
    "base_tree_sha256", "filesystem_sha256", "source_boundary_passed",
)
ISSUE_COLUMNS = (
    "issue_id", "issue_type", "affected_fields", "affected_rules", "severity", "status",
    "blocking_scope", "blocking_reason", "issue_origin", "integration_transition", "issue_count",
)

TRUE_READINESS = (
    "admit_010_precondition_audit_complete",
    "admit_010_rule_identity_verified",
    "admit_010_field_dependency_verified",
    "admit_010_context_dependency_verified",
    "admit_010_historical_evidence_inventory_complete",
    "admit_010_pre_split_boundary_audited",
    "admit_010_standalone_pure_memory_interface_feasible",
    "admit_010_provider_mapping_boundary_preserved",
    "feature_semantics_audit_required_before_training",
    "ready_for_admit_010_leakage_group_assignment_provenance_contract_design",
)
FALSE_READINESS = (
    "leakage_group_assignment_provenance_contract_frozen",
    "leakage_group_id_final_grammar_frozen",
    "leakage_group_id_provider_mapping_validated",
    "evaluate_admit_010_implemented",
    "Admit010EvaluationResult_implemented",
    "admit_010_design_oracle_implemented",
    "admit_010_unified_adapter_contract_frozen",
    "admit_010_unified_adapter_implemented",
    "admit_010_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_010_implemented",
    "admit_011_started",
    "evaluate_all_rules_implemented",
    "combined_candidate_verdict_implemented",
    "real_candidate_evaluation",
    "ready_for_bulk_download_now",
    "ready_for_training",
    "ready_to_train_now",
)


@dataclass(frozen=True)
class FrozenSourceRecord:
    relative_path: Path
    expected_sha256: str
    base_tree_sha256: str
    filesystem_sha256: str
    content_bytes: bytes


@dataclass(frozen=True)
class FrozenSourceSnapshot:
    records: tuple[FrozenSourceRecord, ...]


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _git(arguments: Sequence[str], repo_root: Path, *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(["git", *arguments], cwd=repo_root, text=text, capture_output=True, check=False)


def _safe_relative_path(path: Path) -> bool:
    return (
        isinstance(path, Path) and not path.is_absolute() and bool(path.parts)
        and ".." not in path.parts and path.parts[0] != "checkpoints"
        and path.parts[:2] != ("data", "raw")
    )


def _validate_expected_base_lineage(repo_root: Path, *, head_ref: str = "HEAD") -> None:
    if type(head_ref) is not str or not head_ref or head_ref.startswith("-"):
        raise ValueError("head ref is invalid")
    base = _git(["cat-file", "-e", f"{EXPECTED_BASE_COMMIT}^{{commit}}"], repo_root)
    subject = _git(["show", "-s", "--format=%s", EXPECTED_BASE_COMMIT], repo_root)
    ancestor = _git(["merge-base", "--is-ancestor", EXPECTED_BASE_COMMIT, head_ref], repo_root)
    if base.returncode != 0 or subject.returncode != 0:
        raise ValueError("expected base commit is unavailable")
    if subject.stdout.strip() != EXPECTED_BASE_SUBJECT:
        raise ValueError("expected base commit subject mismatch")
    if ancestor.returncode != 0:
        raise ValueError("expected base commit is not an ancestor of head")


def _structural_source_check(path: Path, repo_root: Path) -> bool:
    if not _safe_relative_path(path):
        return False
    try:
        metadata = os.lstat(repo_root / path)
    except OSError:
        return False
    tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()], repo_root)
    tree = _git(["ls-tree", EXPECTED_BASE_COMMIT, "--", path.as_posix()], repo_root)
    fields = tree.stdout.split("\t", 1)[0].split() if tree.returncode == 0 else []
    return (
        tracked.returncode == 0 and tree.returncode == 0 and len(fields) == 3
        and fields[0] in ("100644", "100755") and fields[1] == "blob"
        and stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    )


def build_frozen_source_snapshot(repo_root: Path = REPO_ROOT, *, head_ref: str = "HEAD") -> FrozenSourceSnapshot:
    """Validate the complete boundary structurally before any explicit byte read."""
    if len(SOURCE_PATHS) != 32 or len(set(SOURCE_PATHS)) != 32 or tuple(SOURCE_SHA256) != SOURCE_PATHS:
        raise ValueError("Exact32 source boundary shape invalid")
    _validate_expected_base_lineage(repo_root, head_ref=head_ref)
    if not all(_structural_source_check(path, repo_root) for path in SOURCE_PATHS):
        raise ValueError("source structural validation failed")
    records: list[FrozenSourceRecord] = []
    for path in SOURCE_PATHS:
        base = _git(["show", f"{EXPECTED_BASE_COMMIT}:{path.as_posix()}"], repo_root, text=False)
        if base.returncode != 0 or type(base.stdout) is not bytes:
            raise ValueError(f"base-tree source read failed: {path}")
        filesystem_bytes = (repo_root / path).read_bytes()
        base_sha = hashlib.sha256(base.stdout).hexdigest()
        filesystem_sha = hashlib.sha256(filesystem_bytes).hexdigest()
        if SOURCE_SHA256[path] != base_sha or base_sha != filesystem_sha:
            raise ValueError(f"source SHA256 mismatch: {path}")
        records.append(FrozenSourceRecord(path, SOURCE_SHA256[path], base_sha, filesystem_sha, filesystem_bytes))
    snapshot = FrozenSourceSnapshot(tuple(records))
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("frozen source snapshot invalid")
    return snapshot


def validate_frozen_source_snapshot(value: object) -> bool:
    return (
        type(value) is FrozenSourceSnapshot and len(value.records) == 32
        and tuple(record.relative_path for record in value.records) == SOURCE_PATHS
        and all(
            type(record) is FrozenSourceRecord
            and record.expected_sha256 == SOURCE_SHA256[record.relative_path]
            and record.base_tree_sha256 == record.expected_sha256
            and record.filesystem_sha256 == record.expected_sha256
            and hashlib.sha256(record.content_bytes).hexdigest() == record.expected_sha256
            for record in value.records
        )
    )


def _record(snapshot: FrozenSourceSnapshot, path: Path) -> FrozenSourceRecord:
    records = tuple(record for record in snapshot.records if record.relative_path == path)
    if len(records) != 1:
        raise ValueError("frozen source missing or duplicate")
    return records[0]


def _csv_rows(snapshot: FrozenSourceSnapshot, path: Path) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(io.StringIO(_record(snapshot, path).content_bytes.decode("utf-8"), newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("invalid CSV header")
    rows = tuple(dict(row) for row in reader)
    if any(tuple(row) != tuple(reader.fieldnames) or any(value is None for value in row.values()) for row in rows):
        raise ValueError("invalid CSV row")
    return rows


def _json(snapshot: FrozenSourceSnapshot, path: Path) -> dict[str, Any]:
    value = json.loads(_record(snapshot, path).content_bytes.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("invalid JSON document")
    return value


def _source_kind(path: Path) -> str:
    if path.suffix == ".py":
        return "production_source"
    if path.suffix == ".json":
        return "committed_manifest"
    return "committed_derived_csv"


def _boundary_necessity(path: Path) -> str:
    text = path.as_posix()
    if "001_to_009" in text:
        return "Exact9_runtime_predecessor"
    if "canonical_final_dataset_bulk_download_admission_design" in text:
        return "canonical_admission_design"
    if "implementation_precondition" in text:
        return "canonical_implementation_precondition"
    if "unified_independence_group_assignment" in text:
        return "Step14AP_group_assignment_and_membership"
    if "unified_leakage_split" in text:
        return "Step14AQ_split_boundary"
    return "Step14AR_final_materialization_boundary"


def _build_precondition_rows() -> list[dict[str, str]]:
    specs = (
        ("rule_identity", "ADMIT_010 identity and name", "ADMIT_010 leakage_group_assignment_before_split", True, "", "retain interface names only"),
        ("evaluation_phase", "evaluation occurs before final split", "pre_final_split", True, "", "retain phase"),
        ("candidate_dependency", "single candidate field identity", "leakage_group_id", True, "", "retain candidate field name"),
        ("context_dependency", "caller-supplied provenance policy context", "leakage_group_assignment_provenance_contract", True, "", "design context contract next"),
        ("historical_success_failure_vocabulary", "success and failure vocabulary", "leakage_group_assigned / leakage_group_unassigned", True, "", "retain historical vocabulary"),
        ("current_primary_blocker", "blocking issue identity and open state", PRIMARY_BLOCKER, True, "", "preserve issue unchanged_open"),
        ("field_occurrence_coverage", "fixed-boundary occurrence audit", "all fixed Exact32 committed sources searched", True, "", "retain inventory"),
        ("observed_value_coverage", "derived-only deterministic value audit", "assignment, group inventory, split, and final membership values inventoried", True, "", "do not promote sample values to grammar"),
        ("final_vs_provisional_group_distinction", "candidate/final field distinction", "canonical leakage_group_id differs by name and contract from historical final_leakage_group_id; mapping unverified", False, PRIMARY_BLOCKER, "design explicit mapping semantics"),
        ("assignment_provenance_availability", "assignment identity, source membership and policy evidence", "historical Step14AP evidence available for current 11-sample smoke only", True, "", "use as design evidence, not provider contract"),
        ("assignment_policy_version_availability", "formal policy and version fields", "assignment_policy value embeds suffix v1; no standalone policy_version field or frozen provenance contract", False, PRIMARY_BLOCKER, "freeze explicit policy/version representation"),
        ("membership_evidence", "sample and group membership evidence", "assignment rows plus five group inventories with member_sample_index_row_ids", True, "", "retain membership requirements"),
        ("pre_split_ordering_evidence", "group assignment precedes split", "Step14AQ declares Step14AP as previous/source stage and consumes its SHA-frozen assignment", True, "", "require caller provenance without split lookup"),
        ("standalone_pure_memory_feasibility", "no evaluator filesystem/network access", "caller provides candidate scalar and provenance context; canonical context contract sets both accesses false", True, "", "keep evaluator pure memory"),
        ("result_schema_precedent", "prior formal evaluator result precedent", "Exact9 runtime provides result-schema precedent; Admit010EvaluationResult remains absent", True, "", "design result later"),
        ("issue_transition_policy", "audit does not resolve predecessor issues", "Exact9 issue inventory copied byte-identically", True, "", "no transition"),
        ("provider_mapping_status", "canonical provider-to-candidate mapping", "no verified leakage_group_id provider mapping and no formal final_leakage_group_id mapping", False, PRIMARY_BLOCKER, "preserve provider boundary"),
        ("real_evaluation_status", "real candidate evaluation", "not performed", False, PRIMARY_BLOCKER, "prohibit evaluation in audit"),
        ("adapter_runtime_boundary", "adapter, registration and Exact10 runtime", "not designed or implemented; Exact9 remains unchanged", True, "", "defer until evaluator contract exists"),
        ("admit_011_boundary", "ADMIT_011 work", "not started", True, "", "remain out of scope"),
        ("training_boundary", "training readiness prerequisite", "feature-semantics audit still required; Step12D was smoke legality only", True, "", "training remains forbidden"),
    )
    return [{
        "precondition_id": f"PRE_{index:03d}", "semantic_area": area,
        "required_contract": required, "observed_contract": observed,
        "source_evidence": "Exact32 committed source boundary", "verified": _bool(verified),
        "blocker_id": blocker, "design_disposition": disposition, "audit_passed": "true",
    } for index, (area, required, observed, verified, blocker, disposition) in enumerate(specs, 1)]


def _identifier_match(line: str, token: str) -> bool:
    if re.fullmatch(r"[A-Za-z0-9_]+", token):
        return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", line) is not None
    return token in line


def _occurrence_location(path: Path, line: str, line_number: int, term: str) -> str:
    if path.suffix == ".py":
        function = re.search(r"^def ([A-Za-z0-9_]+)", line.strip())
        return f"function:{function.group(1)}" if function else f"line:{line_number}"
    if path.suffix == ".json":
        key = re.search(r'^\s*"([^"]+)"\s*:', line)
        return f"key:{key.group(1)}:line:{line_number}" if key else f"line:{line_number}"
    first = next(csv.reader([line]))[0] if line else ""
    return (f"header:{term}" if line_number == 1 else f"row:{first}:line:{line_number}")


def _occurrence_semantics(term: str, path: Path) -> tuple[str, str, str, str]:
    text = path.as_posix()
    if term in {"leakage_group_id", "leakage_group_assignment_before_split"} or term == "ADMIT_010":
        classification = "candidate_or_rule"
    elif term == "leakage_group_assignment_provenance_contract":
        classification = "caller_context"
    elif term in {"assignment_id", "group_split_assignment_id", "sample_split_assignment_id"}:
        classification = "record_identifier_not_group_identifier"
    elif term in {"ligand_graph_group_id", "ligand_scaffold_group_id", "protein_accession_group_id", "protein_exact_sequence_group_id", "protein_sequence_cluster_90_id", "protein_sequence_cluster_50_id"}:
        classification = "single_axis_group_not_final_group"
    else:
        classification = "historical_artifact_or_contract"
    authoritative = "canonical_interface" if "canonical_final_dataset_bulk_download_admission" in text else "historical_evidence_only"
    usable = "true" if authoritative == "canonical_interface" and classification in {"candidate_or_rule", "caller_context"} else "false"
    role = "definition" if path.suffix == ".py" else ("manifest_evidence" if path.suffix == ".json" else "artifact_or_contract_evidence")
    return role, classification, authoritative, usable


def _build_occurrence_rows(snapshot: FrozenSourceSnapshot) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows: list[dict[str, str]] = []
    counts = {term: 0 for term in MATCH_QUERIES}
    for record in snapshot.records:
        lines = record.content_bytes.decode("utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            for term, queries in MATCH_QUERIES.items():
                if not any(_identifier_match(line, query) for query in queries):
                    continue
                counts[term] += 1
                role, classification, authoritative, usable = _occurrence_semantics(term, record.relative_path)
                rows.append({
                    "occurrence_order": str(len(rows) + 1), "term": term,
                    "source_relative_path": record.relative_path.as_posix(),
                    "source_sha256": record.expected_sha256, "source_kind": _source_kind(record.relative_path),
                    "row_key_function_location": _occurrence_location(record.relative_path, line, line_number, term),
                    "occurrence_role": role, "semantic_classification": classification,
                    "current_authoritative_status": authoritative, "usable_by_future_evaluator": usable,
                    "audit_result": "observed_without_semantic_equivalence_promotion",
                })
    if not rows or [int(row["occurrence_order"]) for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("occurrence inventory ordering invalid")
    return rows, counts


OBSERVED_FIELDS = {
    ASSIGNMENT_PATH: (
        "assignment_id", "sample_index_row_id", "ligand_graph_group_id", "ligand_scaffold_group_id",
        "protein_exact_sequence_group_id", "protein_accession_group_id", "protein_sequence_cluster_90_id",
        "protein_sequence_cluster_50_id", "final_leakage_group_id", "final_leakage_group_member_count",
        "final_leakage_group_status", "assignment_policy", "final_group_assignment_passed",
    ),
    GROUP_INVENTORY_PATH: (
        "final_leakage_group_id", "group_order", "member_count", "member_sample_index_row_ids",
        "source_stage_composition", "final_leakage_group_status", "singleton_group",
    ),
    GROUP_SPLIT_PATH: (
        "group_split_assignment_id", "final_leakage_group_id", "group_order", "member_count",
        "member_sample_index_row_ids", "source_stage_composition", "final_leakage_group_status",
        "assigned_split", "split_policy", "group_kept_intact",
    ),
    SAMPLE_SPLIT_PATH: (
        "sample_split_assignment_id", "sample_index_row_id", "final_leakage_group_id",
        "final_leakage_group_member_count", "assigned_split", "split_unit_type",
    ),
    FINAL_MEMBERSHIP_PATH: (
        "final_dataset_membership_id", "sample_index_row_id", "assigned_split",
        "final_leakage_group_id", "final_leakage_group_member_count", "source_index_stage",
    ),
}


def _infer_type(value: str) -> str:
    if value in {"True", "False", "true", "false"}:
        return "bool"
    if re.fullmatch(r"-?(0|[1-9][0-9]*)", value):
        return "int"
    return "str"


def _build_observed_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    unique: set[tuple[Path, str, str]] = set()
    values: list[tuple[Path, str, str]] = []
    for path, fields in OBSERVED_FIELDS.items():
        source_rows = _csv_rows(snapshot, path)
        if not source_rows or any(field not in source_rows[0] for field in fields):
            raise ValueError(f"observed field missing: {path}")
        for field in fields:
            for source_row in source_rows:
                item = (path, field, source_row[field])
                if item not in unique:
                    unique.add(item)
                    values.append(item)
    values.sort(key=lambda item: (SOURCE_PATHS.index(item[0]), OBSERVED_FIELDS[item[0]].index(item[1]), item[2]))
    rows: list[dict[str, str]] = []
    for index, (path, field, value) in enumerate(values, 1):
        lower = value.lower()
        lifecycle = (
            "provisional_status" if "provisional" in lower
            else "final_named_historical_artifact" if field.startswith("final_") or "final_" in field
            else "historical_observed_value"
        )
        rows.append({
            "value_order": str(index), "source_relative_path": path.as_posix(),
            "source_sha256": SOURCE_SHA256[path], "field_name": field, "observed_value": value,
            "inferred_exact_builtin_type": _infer_type(value), "empty_value": _bool(value == ""),
            "null_like": _bool(lower in {"", "null", "none", "na", "n/a", "nan"}),
            "lifecycle_status": lifecycle, "general_grammar_frozen": "false",
            "provenance_equivalence_inferred": "false", "value_audit_passed": "true",
        })
    if len(rows) != len(unique):
        raise ValueError("observed inventory not deduplicated")
    return rows


def _build_source_rows(snapshot: FrozenSourceSnapshot) -> list[dict[str, str]]:
    return [{
        "source_order": str(index), "source_relative_path": record.relative_path.as_posix(),
        "source_kind": _source_kind(record.relative_path),
        "boundary_necessity": _boundary_necessity(record.relative_path), "tracked": "true",
        "base_tree_blob": "true", "filesystem_regular": "true", "non_symlink": "true",
        "expected_sha256": record.expected_sha256, "base_tree_sha256": record.base_tree_sha256,
        "filesystem_sha256": record.filesystem_sha256, "source_boundary_passed": "true",
    } for index, record in enumerate(snapshot.records, 1)]


def _validate_authoritative_contracts(snapshot: FrozenSourceSnapshot) -> dict[str, Any]:
    rule = next(row for row in _csv_rows(snapshot, RULE_REGISTRY_PATH) if row["admission_rule_id"] == "ADMIT_010")
    schema = next(row for row in _csv_rows(snapshot, SCHEMA_CONTRACT_PATH) if row["admission_field_name"] == "leakage_group_id")
    executable = next(row for row in _csv_rows(snapshot, RULE_EXECUTABILITY_PATH) if row["admission_rule_id"] == "ADMIT_010")
    field = next(row for row in _csv_rows(snapshot, FIELD_SEMANTICS_PATH) if row["field_name"] == "leakage_group_id")
    context = next(row for row in _csv_rows(snapshot, EVALUATION_CONTEXT_PATH) if row["context_item"] == "leakage_group_assignment_provenance_contract")
    registry = next(row for row in _csv_rows(snapshot, RUNTIME_REGISTRY_PATH) if row["rule_id"] == "ADMIT_010")
    blocker = next(row for row in _csv_rows(snapshot, RUNTIME_ISSUE_PATH) if row["issue_id"] == PRIMARY_BLOCKER)
    coverage = next(row for row in _csv_rows(snapshot, RUNTIME_ISSUE_PATH) if row["issue_id"] == "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE")
    assignment_manifest = _json(snapshot, ASSIGNMENT_MANIFEST_PATH)
    split_manifest = _json(snapshot, SPLIT_MANIFEST_PATH)
    final_manifest = _json(snapshot, FINAL_MANIFEST_PATH)
    checks = (
        rule == {**rule, "admission_rule_name": "leakage_group_assignment_before_split", "required_status": "leakage_group_assigned", "blocking_reason": "leakage_group_unassigned", "evaluation_phase": "pre_final_split"},
        schema["requirement_phase"] == "pre_final_split" and schema["required_at_phase"] == "true",
        executable["candidate_field_dependencies"] == "leakage_group_id" and executable["evaluation_context_dependencies"] == "leakage_group_assignment_provenance_contract" and executable["external_filesystem_required"] == executable["network_required"] == "false" and executable["pure_in_memory_interface_possible"] == "true",
        field["producer_scope"] == "leakage_assignment_stage" and field["implementation_semantics_complete"] == "false" and field["blocking_reasons"] == PRIMARY_BLOCKER,
        context["provided_by_future_caller"] == "true" and context["filesystem_access_inside_evaluator"] == context["network_access_inside_evaluator"] == "false" and context["exact_contract_defined"] == context["implementation_ready"] == "false",
        registry["registered"] == "false" and registry["dispatch_disposition"] == "UNIFIED_ADMISSION_RULE_NOT_REGISTERED",
        blocker["status"] == "open" and blocker["affected_fields"] == "leakage_group_id" and blocker["affected_rules"] == "ADMIT_010" and blocker["integration_transition"] == "unchanged_open",
        coverage["affected_rules"] == "ADMIT_010|ADMIT_011|ADMIT_012|ADMIT_013|ADMIT_014|ADMIT_015",
        assignment_manifest["stage"] == split_manifest["previous_stage"] == split_manifest["source_step14ap_stage"],
        assignment_manifest["split_assignments_written"] is False and split_manifest["split_optimizer_executed"] is True,
        final_manifest["previous_stage"] == split_manifest["stage"] and final_manifest["source_step14aq_preconditions_passed"] is True,
    )
    if not all(checks):
        raise ValueError("authoritative ADMIT_010 contract validation failed")
    return {
        "rule": rule, "schema": schema, "executable": executable, "field": field,
        "context": context, "registry": registry, "blocker": blocker, "coverage": coverage,
        "assignment_manifest": assignment_manifest, "split_manifest": split_manifest,
        "final_manifest": final_manifest,
    }


def build_audit_state(snapshot: FrozenSourceSnapshot | None = None) -> dict[str, Any]:
    snapshot = snapshot or build_frozen_source_snapshot()
    if not validate_frozen_source_snapshot(snapshot):
        raise ValueError("invalid source snapshot")
    contracts = _validate_authoritative_contracts(snapshot)
    precondition_rows = _build_precondition_rows()
    occurrence_rows, term_counts = _build_occurrence_rows(snapshot)
    observed_rows = _build_observed_rows(snapshot)
    source_rows = _build_source_rows(snapshot)
    issue_bytes = _record(snapshot, RUNTIME_ISSUE_PATH).content_bytes
    issue_rows = list(_csv_rows(snapshot, RUNTIME_ISSUE_PATH))
    if tuple(issue_rows[0]) != ISSUE_COLUMNS or hashlib.sha256(issue_bytes).hexdigest() != SOURCE_SHA256[RUNTIME_ISSUE_PATH]:
        raise ValueError("Exact9 issue inventory preservation failed")
    required_positive_terms = set(MATCH_QUERIES) - {"policy version"}
    if any(term_counts[term] == 0 for term in required_positive_terms):
        missing = sorted(term for term in required_positive_terms if term_counts[term] == 0)
        raise ValueError(f"required term occurrence absent: {missing}")
    readiness = {key: True for key in TRUE_READINESS} | {key: False for key in FALSE_READINESS}
    safety = {
        "network_used": False, "raw_read": False, "raw_write": False,
        "split_execution": False, "leakage_reassignment": False,
        "candidate_materialization": False, "provider_mapping": False,
        "admit_010_evaluator_implementation": False, "admit_011": False,
        "model_or_training": False, "stage_commit_push": False, "gh_used": False,
    }
    return {
        "snapshot": snapshot, "contracts": contracts, "precondition_rows": precondition_rows,
        "occurrence_rows": occurrence_rows, "observed_rows": observed_rows,
        "source_rows": source_rows, "issue_rows": issue_rows, "issue_bytes": issue_bytes,
        "term_search_counts": term_counts, "readiness": readiness, "safety": safety,
    }


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if tuple(row) != columns:
            raise ValueError("output row schema mismatch")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _manifest(state: dict[str, Any], output_hashes: dict[str, str]) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "project": PROJECT, "stage": STAGE, "step": STEP,
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "base_commit": EXPECTED_BASE_COMMIT, "base_subject": EXPECTED_BASE_SUBJECT,
        "admission_rule_id": "ADMIT_010",
        "admission_rule_name": "leakage_group_assignment_before_split",
        "evaluation_phase": "pre_final_split", "candidate_field": "leakage_group_id",
        "evaluation_context": "leakage_group_assignment_provenance_contract",
        "required_status": "leakage_group_assigned", "historical_blocking_reason": "leakage_group_unassigned",
        "primary_unresolved_blocker": PRIMARY_BLOCKER, "primary_blocker_status": "open",
        "canonical_candidate_field": "leakage_group_id",
        "historical_artifact_field": "final_leakage_group_id",
        "candidate_to_historical_field_mapping_status": "unverified",
        "assignment_id_semantics": "record_identifier_not_group_identifier",
        "duplicate_identity_key_substitution_allowed": False,
        "single_axis_group_substitution_allowed": False,
        "split_assignment_proves_pre_split_assignment": False,
        "future_evaluator_runs_grouping_algorithm": False,
        "future_evaluator_accesses_filesystem_or_split_files": False,
        "future_api_names_reserved_only": ["evaluate_admit_010", "Admit010EvaluationResult"],
        "source_count": len(SOURCE_PATHS), "precondition_row_count": len(state["precondition_rows"]),
        "occurrence_row_count": len(state["occurrence_rows"]), "observed_value_row_count": len(state["observed_rows"]),
        "issue_row_count": len(state["issue_rows"]), "term_search_counts": state["term_search_counts"],
        "issue_inventory_predecessor_sha256": SOURCE_SHA256[RUNTIME_ISSUE_PATH],
        "issue_inventory_output_sha256": output_hashes[ISSUE_FILENAME],
        "issue_inventory_byte_identical_to_exact9": output_hashes[ISSUE_FILENAME] == SOURCE_SHA256[RUNTIME_ISSUE_PATH],
        "readiness": state["readiness"], "safety": state["safety"],
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "output_sha256": output_hashes,
        "all_checks_passed": True,
    }
    manifest.update(state["readiness"])
    return manifest


def _preflight_output_root(root: Path) -> None:
    """Reject every unsafe root or existing entry before the first write."""
    if not isinstance(root, Path):
        raise ValueError("output root must be a Path")
    try:
        root_metadata = os.lstat(root)
    except FileNotFoundError:
        root.mkdir(parents=True, exist_ok=False)
        try:
            root_metadata = os.lstat(root)
        except OSError as error:
            raise ValueError("created output root cannot be inspected") from error
    except OSError as error:
        raise ValueError("output root cannot be inspected") from error
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ValueError("output root must be a real directory")

    try:
        entries = tuple(root.iterdir())
    except OSError as error:
        raise ValueError("output root inventory cannot be read") from error
    allowed_names = set(OUTPUT_FILES)
    observed_names = {entry.name for entry in entries}
    if not observed_names <= allowed_names:
        raise ValueError("output root contains an unexpected entry")
    for entry in entries:
        try:
            metadata = os.lstat(entry)
        except OSError as error:
            raise ValueError("existing output entry cannot be inspected") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("existing output entry must be a regular non-symlink file")


def _atomic_write(path: Path, content: bytes) -> None:
    """Atomically replace one output using a same-directory durable temp file."""
    if not isinstance(path, Path) or type(content) is not bytes:
        raise ValueError("atomic output requires Path and exact bytes")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    descriptor_owned = True
    try:
        stream = os.fdopen(descriptor, "wb")
        descriptor_owned = False
        with stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if descriptor_owned:
            os.close(descriptor)
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass


def materialize_audit(output_root: Path | None = None) -> dict[str, Any]:
    state = build_audit_state()
    payloads = {
        PRECONDITION_FILENAME: _csv_bytes(PRECONDITION_COLUMNS, state["precondition_rows"]),
        OCCURRENCE_FILENAME: _csv_bytes(OCCURRENCE_COLUMNS, state["occurrence_rows"]),
        OBSERVED_FILENAME: _csv_bytes(OBSERVED_COLUMNS, state["observed_rows"]),
        SOURCE_BOUNDARY_FILENAME: _csv_bytes(SOURCE_BOUNDARY_COLUMNS, state["source_rows"]),
        ISSUE_FILENAME: state["issue_bytes"],
    }
    output_hashes = {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()}
    manifest = _manifest(state, output_hashes)
    payloads[MANIFEST_FILENAME] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    root = output_root if output_root is not None else REPO_ROOT / DEFAULT_OUTPUT_ROOT
    _preflight_output_root(root)
    for name in OUTPUT_FILES:
        _atomic_write(root / name, payloads[name])
    entries = tuple(root.iterdir())
    if {entry.name for entry in entries} != set(OUTPUT_FILES):
        raise ValueError("completed output inventory mismatch")
    for entry in entries:
        metadata = os.lstat(entry)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("completed output entry is not a regular non-symlink file")
    return {"output_root": root, "manifest": manifest, "output_sha256": {name: hashlib.sha256(payloads[name]).hexdigest() for name in OUTPUT_FILES}}


def run_covapie_bulk_download_admission_admit_010_formal_evaluator_interface_preconditions_audit_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Materialize the six deterministic metadata-only audit outputs."""
    return materialize_audit(output_root)


if __name__ == "__main__":
    materialize_audit()
