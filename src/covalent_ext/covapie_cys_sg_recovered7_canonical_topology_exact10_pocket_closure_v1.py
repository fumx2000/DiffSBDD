"""Close recovered7 model-bound topology, Exact10, and pocket evidence.

This is a thin, offline successor over published owners.  It consumes the
published exact12 recovery snapshot and the seven already acquired raw entry
mmCIF files.  Entry-embedded ``chem_comp_atom``/``chem_comp_bond`` records are
the only topology evidence used.  Component topology and the explicit
protein-ligand event edge remain separate, and no reaction reconstruction or
coordinate-derived bond inference is performed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from covalent_ext import (
    covapie_current11_pre_reaction_graph_and_bond_order_authority_v1
    as topology_owner,
)
from covalent_ext import (
    covapie_cys_sg_stage_b0_open_candidate_structural_evidence_recovery_v1
    as event_owner,
)
from covalent_ext import (
    covapie_sample_preparation_execution_smoke as full_atom_pocket_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as exact10_owner,
)
from covalent_ext import (
    real_covalent_confirmed_candidate_atom_site_coordinate_extraction_altloc_aware_rerun
    as atom_site_owner,
)


SCHEMA_VERSION = (
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1"
)
PUBLISHED_EXECUTION_COMMIT = "5cabada8264e1a3243f629b186f4ed3208f7a249"
REPO_ROOT = Path(__file__).resolve().parents[2]

EXECUTION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1"
)
EXECUTION_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_cys_sg_exact12_targeted_structural_evidence_acquisition_execution_v1.py"
)
EXECUTION_AUDIT = EXECUTION_ROOT / (
    "covapie_cys_sg_exact12_acquisition_execution_and_integrity_audit.csv"
)
RECOVERY_SNAPSHOT = EXECUTION_ROOT / (
    "covapie_cys_sg_exact12_post_acquisition_structural_recovery_snapshot.csv"
)
EXECUTION_MANIFEST = EXECUTION_ROOT / (
    "covapie_cys_sg_exact12_targeted_acquisition_execution_manifest.json"
)
PUBLISHED_EXECUTION_SHA256: Mapping[Path, str] = {
    EXECUTION_SOURCE:
        "2bdd7ab25db3270a7e71767084ae73a409b65cd79d031632a6689d0031b644f7",
    EXECUTION_AUDIT:
        "575f8437435a71dbba1fabfd347bd22422bb26da1ef0c947b4df6c577f2dad04",
    RECOVERY_SNAPSHOT:
        "38f49690c5f349f550dc04d3d7f099b9e337d9ea2887b9db4e2c128cd5fe4b9b",
    EXECUTION_MANIFEST:
        "711cde319f4887f5d7088c4002c09c3ca18151e07d7269090599548694922f6f",
}

RAW_ROOT = Path(
    "data/raw/covalent_sources/covpdb/future_struct_conn_crosscheck_raw_v0"
)
RECOVERED_IDENTITIES = (
    ("2DJF", "1ZB"),
    ("2R9F", "K2Z"),
    ("4DCD", "K36"),
    ("6WTT", "K36"),
    ("4F49", "K36"),
    ("6L70", "K36"),
    ("5WKJ", "K36"),
)
UNRESOLVED_STRUCTURAL_REVIEW_IDENTITIES = (
    ("1A54", "MDC"),
    ("6VWE", "JY1"),
    ("6WTJ", "K36"),
    ("7C8U", "K36"),
    ("6WTK", "UED"),
)
RAW_SHA256_BY_PDB: Mapping[str, str] = {
    "2DJF": "909fdf9bb28d1875a3ab80c5108b50025e6180196656e0eb5e46f572e4c185c2",
    "2R9F": "af5a5539b88559786185eb671a46b09b7f73854a2bf550f3d8149d0d2c40b828",
    "4DCD": "bd42d910542faf3d337d76024faaad67ef8a3b40996fcb0be5918c80b777c4a2",
    "6WTT": "33bdd92bd5ab6b5fb147bf6b2a8ca73f12e0fbde744c045890389c2d057b7240",
    "4F49": "9f7d7419182647a82fd3a0d837524db179b4a4429c809906d97b3aef8618543d",
    "6L70": "963b6e5a6556b17e30f8c0549e85932a9eb5af9c8bf8df6736f03e6e761f614d",
    "5WKJ": "6c17237a4f1ced1d0f49d387ff3c2b61f24429e7a1df6d061d69adb6f3bd5b14",
}
TOPOLOGY_SOURCE_PDB_BY_COMPONENT: Mapping[str, str] = {
    "1ZB": "2DJF",
    "K2Z": "2R9F",
    "K36": "4DCD",
}
TOPOLOGY_SOURCE_KIND = "RCSB_ENTRY_MMCIF_EMBEDDED_CHEM_COMP_ATOM_BOND"
POCKET_RADIUS_ANGSTROM = full_atom_pocket_owner.POCKET_RADIUS_ANGSTROM

OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
MATRIX_FILE = "covapie_cys_sg_recovered7_canonical_closure_matrix.csv"
EVIDENCE_FILE = (
    "covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json"
)
MANIFEST_FILE = "covapie_cys_sg_recovered7_canonical_closure_manifest.json"
OUTPUT_FILES = (MATRIX_FILE, EVIDENCE_FILE, MANIFEST_FILE)

MATRIX_COLUMNS = (
    "canonical_candidate_id", "pdb_id", "ligand_component_id", "raw_sha256",
    "event_reactive_residue_atom", "event_reactive_ligand_atom",
    "event_mapping_status", "topology_source_kind", "topology_source_identity",
    "topology_source_sha256", "ligand_observed_heavy_atom_count",
    "topology_heavy_atom_count", "ligand_heavy_atom_mapping_status",
    "topology_atom_mapping_status", "canonical_ligand_heavy_atom_count",
    "explicit_hydrogen_excluded_count", "unsupported_nonh_model_bound_count",
    "canonical_model_atom_set_status", "exact10_status", "pocket_atom_count",
    "target_cys_present", "target_sg_present", "pocket_status",
    "mechanical_closure_status", "downstream_chemistry_label_status",
    "primary_remaining_issue",
)

REUSED_OWNERS = {
    "atom_site": (
        "src/covalent_ext/real_covalent_confirmed_candidate_atom_site_"
        "coordinate_extraction_altloc_aware_rerun.py#extract_atom_site_loop_rows_v0"
    ),
    "event": (
        "src/covalent_ext/covapie_cys_sg_stage_b0_open_candidate_structural_"
        "evidence_recovery_v1.py#recover_exact_struct_conn_event_v1"
    ),
    "topology": (
        "src/covalent_ext/covapie_current11_pre_reaction_graph_and_bond_order_"
        "authority_v1.py#_parse_loop,normalize_bond_order"
    ),
    "full_atom": (
        "src/covalent_ext/covapie_sample_preparation_execution_smoke.py#"
        "_model_allowed,_altloc_allowed"
    ),
    "pocket": (
        "src/covalent_ext/covapie_sample_preparation_execution_smoke.py#"
        "_coords,_distance,POCKET_RADIUS_ANGSTROM"
    ),
    "exact10": (
        "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_"
        "policy_resolution_v1.py#project_type_symbols_to_checkpoint_heavy_v1"
    ),
}

FAMILY_WARHEAD_AUTHORITY_REGISTRY = Path(
    "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_approved_warhead_rule_"
    "authority_binding_v1/covapie_family_and_warhead_rule_authority_registry.csv"
)
ROLE_RULE_REGISTRY = Path(
    "data/derived/covalent_small/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/"
    "covapie_ligand_role_annotation_rule_registry.csv"
)
CURRENT11_EFFECTIVE_AUTHORITY_STATE = Path(
    "covapie-state/manual-review/"
    "covapie_current11_unified_effective_authority_view_v1.json"
)
DOWNSTREAM_AUTHORITY_SOURCE_SHA256: Mapping[Path, str] = {
    FAMILY_WARHEAD_AUTHORITY_REGISTRY:
        "4899d4664acf45d5ee90283e7977d62385b3a70fe41e082f4d060388be7e106b",
    ROLE_RULE_REGISTRY:
        "329d739587c525d76891f3a81689e397ea088b89a142361696a36f0e58f95889",
    CURRENT11_EFFECTIVE_AUTHORITY_STATE:
        "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774",
}
DOWNSTREAM_AUTHORITY_OWNERS = {
    "reaction_family": (
        "src/covalent_ext/covapie_current11_reaction_family_and_approved_"
        "warhead_rule_authority_binding_v1.py"
    ),
    "warhead_rule": (
        "src/covalent_ext/covapie_current11_reaction_family_and_approved_"
        "warhead_rule_authority_binding_v1.py"
    ),
    "boundary_role": (
        "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_"
        "contract_design_v1.py"
    ),
    "effective_authority": (
        "src/covalent_ext/covapie_current11_unified_effective_authority_view_v1.py"
    ),
}

REQUIRED_DOWNSTREAM_DIMENSIONS = (
    "reaction_family", "warhead_rule", "warhead_atom_set",
    "attachment_boundary", "role_assignment",
)
FINAL_DOWNSTREAM_STATUSES = {
    "ALREADY_AUTHORITATIVE",
    "AUTOMATIC_RULE_AVAILABLE",
    "HUMAN_CHEMISTRY_REVIEW_REQUIRED",
}
_PRIMARY_ISSUE_BY_DIMENSION = {
    "reaction_family": "REACTION_FAMILY_APPROVED_RULE_NO_MATCH",
    "warhead_rule": "WARHEAD_RULE_APPROVED_RULE_NO_MATCH",
    "warhead_atom_set": "WARHEAD_ATOM_SET_AUTHORITY_REQUIRED",
    "attachment_boundary": "ATTACHMENT_BOUNDARY_AUTHORITY_REQUIRED",
    "role_assignment": "ROLE_ASSIGNMENT_AUTHORITY_REQUIRED",
}


class ClosureValidationError(ValueError):
    """Fail-closed validation error for recovered7 closure."""


@dataclass(frozen=True)
class ComponentTopologyAuthority:
    component_id: str
    source_path: str
    source_kind: str
    source_sha256: str
    semantic_topology_sha256: str
    atoms: tuple[dict[str, Any], ...]
    bonds: tuple[dict[str, Any], ...]
    atom_count: int
    heavy_atom_count: int
    explicit_hydrogen_atom_count: int
    bond_count: int
    heavy_heavy_bond_count: int
    bond_order_available: bool


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False, indent=2,
    ) + "\n").encode("utf-8")


def _csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=MATRIX_COLUMNS, extrasaction="raise", lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            column: "true" if row[column] is True
            else "false" if row[column] is False
            else row[column]
            for column in MATRIX_COLUMNS
        })
    return stream.getvalue().encode("utf-8")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _downstream_source_path(repo_root: Path, path: Path) -> Path:
    if path == CURRENT11_EFFECTIVE_AUTHORITY_STATE:
        return repo_root.parent / path
    return repo_root / path


def _read_downstream_authority_source_v1(
    repo_root: Path, path: Path,
) -> bytes:
    payload = _downstream_source_path(repo_root, path).read_bytes()
    if _sha256(payload) != DOWNSTREAM_AUTHORITY_SOURCE_SHA256[path]:
        raise ClosureValidationError(
            f"DOWNSTREAM_AUTHORITY_SOURCE_SHA256_MISMATCH:{path.as_posix()}"
        )
    return payload


def _approved_reusable_binding_v1(row: Mapping[str, str]) -> bool:
    return (
        row.get("reaction_family_authority_status")
        in {"approved", "authoritative", "approved_reusable"}
        and row.get("approval_status") in {"approved", "authoritative"}
        and row.get("approval_scope") in {"reusable", "reusable_rule"}
        and bool(row.get("reaction_family_version"))
        and bool(row.get("warhead_rule_version"))
        and bool(row.get("structural_representation_type"))
        and bool(row.get("structural_representation"))
    )


def load_downstream_authority_context_v1(
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Load SHA-bound reusable registries and sample-bound Current11 state."""

    binding_rows = _csv_rows(_read_downstream_authority_source_v1(
        repo_root, FAMILY_WARHEAD_AUTHORITY_REGISTRY,
    ))
    role_rows = _csv_rows(_read_downstream_authority_source_v1(
        repo_root, ROLE_RULE_REGISTRY,
    ))
    effective = json.loads(_read_downstream_authority_source_v1(
        repo_root, CURRENT11_EFFECTIVE_AUTHORITY_STATE,
    ))
    effective_records = effective.get("effective_authority_records")
    if (
        type(effective_records) is not list
        or effective.get("effective_authority_record_count") != len(effective_records)
        or len(effective_records) != 11
    ):
        raise ClosureValidationError("CURRENT11_EFFECTIVE_AUTHORITY_STATE_INVALID")
    if not all(row.get("verified") == "true" for row in (
        *binding_rows, *role_rows,
    )):
        raise ClosureValidationError("DOWNSTREAM_AUTHORITY_REGISTRY_NOT_VERIFIED")

    approved_bindings = [
        row for row in binding_rows if _approved_reusable_binding_v1(row)
    ]
    approved_role_rows = [
        row for row in role_rows
        if row.get("rule_status") == "approved_deterministic"
    ]
    sample_bound_records: list[dict[str, Any]] = []
    for wrapper in effective_records:
        record = wrapper.get("effective_authority_record")
        if type(record) is not dict:
            raise ClosureValidationError(
                "CURRENT11_EFFECTIVE_AUTHORITY_RECORD_INVALID"
            )
        sample_bound_records.append(record)
    return {
        "binding_rows": binding_rows,
        "role_rows": role_rows,
        "approved_family_rows": approved_bindings,
        "approved_warhead_rows": approved_bindings,
        "approved_role_rows": approved_role_rows,
        "sample_bound_records": sample_bound_records,
    }


def _authority_dimension_v1(
    *,
    authority_status: str,
    source_path: Path | None,
    authority_id: str | None,
    rule_scope: str,
    match_count: int,
    applicability_reason: str,
    ambiguity_reason: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    if type(match_count) is not int or match_count < 0:
        raise ClosureValidationError("DOWNSTREAM_AUTHORITY_MATCH_COUNT_INVALID")
    result = {
        "authority_status": authority_status,
        "authority_source_path_or_NONE": (
            source_path.as_posix() if source_path is not None else "NONE"
        ),
        "authority_source_sha256_or_NONE": (
            DOWNSTREAM_AUTHORITY_SOURCE_SHA256[source_path]
            if source_path is not None else "NONE"
        ),
        "authority_id_or_NONE": authority_id or "NONE",
        "rule_scope": rule_scope,
        "match_count": match_count,
        "applicability_reason": applicability_reason,
        "ambiguity_reason_or_NONE": ambiguity_reason or "NONE",
    }
    result.update(extra)
    return result


def _unresolved_issue_v1(
    dimension: str, audit: Mapping[str, Any],
) -> str:
    match_count = audit.get("match_count")
    status = audit.get("authority_status")
    if type(match_count) is not int or match_count < 0:
        raise ClosureValidationError(
            f"DOWNSTREAM_AUTHORITY_MATCH_COUNT_INVALID:{dimension}"
        )
    if match_count > 1:
        return {
            "reaction_family": "REACTION_FAMILY_APPROVED_RULE_MULTI_MATCH",
            "warhead_rule": "WARHEAD_RULE_MULTI_MATCH",
            "warhead_atom_set": "WARHEAD_ATOM_SET_MULTI_MATCH",
            "attachment_boundary": "ATTACHMENT_BOUNDARY_MULTI_MATCH",
            "role_assignment": "ROLE_ASSIGNMENT_MULTI_MATCH",
        }[dimension]
    if status in {"CANDIDATE_ONLY_RULE_MATCH", "UNAPPROVED_RULE_MATCH"}:
        return {
            "reaction_family": "REACTION_FAMILY_RULE_NOT_APPROVED",
            "warhead_rule": "WARHEAD_RULE_NOT_APPROVED",
            "warhead_atom_set": "WARHEAD_ATOM_SET_RULE_NOT_APPROVED",
            "attachment_boundary": "ATTACHMENT_BOUNDARY_RULE_NOT_APPROVED",
            "role_assignment": "ROLE_ASSIGNMENT_RULE_NOT_APPROVED",
        }[dimension]
    if status in {"AMBIGUOUS", "REACTION_STATE_AMBIGUOUS"}:
        return {
            "reaction_family": "REACTION_FAMILY_AUTHORITY_AMBIGUOUS",
            "warhead_rule": "POST_REACTION_CHEMISTRY_AMBIGUOUS",
            "warhead_atom_set": "WARHEAD_ATOM_SET_AMBIGUOUS",
            "attachment_boundary": "ATTACHMENT_BOUNDARY_AMBIGUOUS",
            "role_assignment": "ROLE_ASSIGNMENT_AMBIGUOUS",
        }[dimension]
    return _PRIMARY_ISSUE_BY_DIMENSION[dimension]


def derive_downstream_chemistry_classification_v1(
    dimension_audits: Mapping[str, Mapping[str, Any]],
) -> tuple[str, str]:
    """Apply exact-one and scope semantics to a complete dimension audit."""

    if set(dimension_audits) != set(REQUIRED_DOWNSTREAM_DIMENSIONS):
        raise ClosureValidationError("DOWNSTREAM_AUTHORITY_DIMENSION_SET_INVALID")
    resolved: list[bool] = []
    sample_bound: list[bool] = []
    for dimension in REQUIRED_DOWNSTREAM_DIMENSIONS:
        audit = dimension_audits[dimension]
        match_count = audit.get("match_count")
        status = audit.get("authority_status")
        if type(match_count) is not int or match_count < 0:
            raise ClosureValidationError(
                f"DOWNSTREAM_AUTHORITY_MATCH_COUNT_INVALID:{dimension}"
            )
        provenance_complete = (
            audit.get("authority_source_path_or_NONE") != "NONE"
            and type(audit.get("authority_source_sha256_or_NONE")) is str
            and len(audit["authority_source_sha256_or_NONE"]) == 64
            and audit.get("authority_id_or_NONE") != "NONE"
        )
        exact_sample_bound = (
            status == "SAMPLE_BOUND_AUTHORITY_MATCH"
            and audit.get("rule_scope") == "SAMPLE_BOUND_AUTHORITY"
            and match_count == 1
            and provenance_complete
            and audit.get("published") is True
            and audit.get("sample_identity_exact") is True
            and audit.get("complete_dimension_authority") is True
        )
        reusable_rule = (
            status in {
                "APPROVED_REUSABLE_RULE_MATCH",
                "APPROVED_DETERMINISTIC_RULE_MATCH",
            }
            and audit.get("rule_scope") in {
                "REUSABLE_APPROVED_RULE",
                "REUSABLE_APPROVED_DETERMINISTIC_RULE",
            }
            and match_count == 1
            and provenance_complete
            and audit.get("published") is True
            and audit.get("approved") is True
            and audit.get("version_bound") is True
            and audit.get("exact_sample_applicability") is True
            and audit.get("deterministic_unique_result") is True
            and audit.get("invariants_pass") is True
            and (
                dimension not in {"reaction_family", "warhead_rule"}
                or (
                    audit.get("reactive_ligand_atom_compatible") is True
                    and audit.get("cys_sg_event_compatible") is True
                )
            )
        )
        resolved.append(exact_sample_bound or reusable_rule)
        sample_bound.append(exact_sample_bound)
    if all(sample_bound):
        return "ALREADY_AUTHORITATIVE", "NONE"
    if all(resolved):
        return (
            "AUTOMATIC_RULE_AVAILABLE",
            "AUTOMATIC_CHEMISTRY_LABEL_EXECUTION_NOT_PERFORMED",
        )
    for dimension, is_resolved in zip(REQUIRED_DOWNSTREAM_DIMENSIONS, resolved):
        if not is_resolved:
            return (
                "HUMAN_CHEMISTRY_REVIEW_REQUIRED",
                _unresolved_issue_v1(dimension, dimension_audits[dimension]),
            )
    raise ClosureValidationError("DOWNSTREAM_AUTHORITY_CLASSIFICATION_UNREACHABLE")


def build_downstream_chemistry_authority_audit_v1(
    snapshot_row: Mapping[str, str],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit recovered7 against approved reusable and exact sample-bound authority."""

    pdb_id = snapshot_row["pdb_id"]
    component_id = snapshot_row["ligand_component_id"]
    sample_matches = [
        row for row in context["sample_bound_records"]
        if row.get("pdb_id") == pdb_id
        and row.get("ligand_comp_id") == component_id
    ]
    approved_family_count = len(context["approved_family_rows"])
    approved_warhead_count = len(context["approved_warhead_rows"])
    approved_role_count = len(context["approved_role_rows"])
    if approved_family_count or approved_warhead_count or approved_role_count:
        raise ClosureValidationError(
            "APPROVED_REUSABLE_RULE_MATCHER_REQUIRED_FOR_CHANGED_AUTHORITY_SOURCE"
        )

    dimensions = {
        "reaction_family": _authority_dimension_v1(
            authority_status="APPROVED_REUSABLE_RULE_NO_MATCH",
            source_path=FAMILY_WARHEAD_AUTHORITY_REGISTRY,
            authority_id=None,
            rule_scope="REUSABLE_APPROVED_RULE",
            match_count=0,
            applicability_reason=(
                "the SHA-bound authority registry contains zero approved, "
                "version-bound reusable reaction-family rules"
            ),
            approved_reusable_rule_count=approved_family_count,
            candidate_only_registry_entry_count=len(context["binding_rows"]),
            graph_match_executed=False,
            graph_match_not_executed_reason=(
                "no approved reusable rule survived the authority prefilter"
            ),
        ),
        "warhead_rule": _authority_dimension_v1(
            authority_status="APPROVED_REUSABLE_RULE_NO_MATCH",
            source_path=FAMILY_WARHEAD_AUTHORITY_REGISTRY,
            authority_id=None,
            rule_scope="REUSABLE_APPROVED_RULE",
            match_count=0,
            applicability_reason=(
                "the SHA-bound authority registry contains zero approved, "
                "version-bound reusable warhead rules"
            ),
            ambiguity_reason=(
                "component topology is not reaction-specific POST authority"
            ),
            approved_reusable_rule_count=approved_warhead_count,
            candidate_only_registry_entry_count=len(context["binding_rows"]),
            graph_match_executed=False,
            graph_match_not_executed_reason=(
                "no approved reusable rule survived the authority prefilter"
            ),
            reaction_specific_post_graph_proven=False,
        ),
        "warhead_atom_set": _authority_dimension_v1(
            authority_status="SAMPLE_BOUND_AUTHORITY_NO_MATCH",
            source_path=CURRENT11_EFFECTIVE_AUTHORITY_STATE,
            authority_id=None,
            rule_scope="SAMPLE_BOUND_CURRENT11_BOUNDARY_AUTHORITY",
            match_count=len(sample_matches),
            applicability_reason=(
                "no exact recovered7 PDB/component identity occurs in the "
                "Current11 sample-bound effective authority view"
            ),
            ambiguity_reason=(
                "candidate-only reusable rules cannot supply a reviewed atom set"
            ),
            sample_bound_authority_population_count=len(
                context["sample_bound_records"]
            ),
        ),
        "attachment_boundary": _authority_dimension_v1(
            authority_status="SAMPLE_BOUND_AUTHORITY_NO_MATCH",
            source_path=CURRENT11_EFFECTIVE_AUTHORITY_STATE,
            authority_id=None,
            rule_scope="SAMPLE_BOUND_CURRENT11_BOUNDARY_AUTHORITY",
            match_count=len(sample_matches),
            applicability_reason=(
                "no exact recovered7 PDB/component identity occurs in the "
                "Current11 sample-bound effective authority view"
            ),
            ambiguity_reason=(
                "no approved deterministic reusable boundary rule is published"
            ),
            sample_bound_authority_population_count=len(
                context["sample_bound_records"]
            ),
        ),
        "role_assignment": _authority_dimension_v1(
            authority_status="APPROVED_DETERMINISTIC_RULE_NO_MATCH",
            source_path=ROLE_RULE_REGISTRY,
            authority_id=None,
            rule_scope="REUSABLE_APPROVED_DETERMINISTIC_RULE",
            match_count=0,
            applicability_reason=(
                "the role registry contains gates and proposal/support methods, "
                "but zero approved deterministic final role-assignment rules"
            ),
            ambiguity_reason="final role authority requires human gold review",
            approved_deterministic_rule_count=approved_role_count,
            registry_entry_count=len(context["role_rows"]),
        ),
    }
    combined_status, primary_issue = (
        derive_downstream_chemistry_classification_v1(dimensions)
    )
    return {
        **dimensions,
        "audited_sample_identity": f"{pdb_id}/{component_id}",
        "anchor_role": _authority_dimension_v1(
            authority_status="NOT_APPLICABLE_UNTIL_ROLE_ASSIGNMENT_RESOLVED",
            source_path=ROLE_RULE_REGISTRY,
            authority_id=None,
            rule_scope="DEPENDENT_ON_ROLE_ASSIGNMENT",
            match_count=0,
            applicability_reason=(
                "anchor derivation is not applicable before final role authority"
            ),
        ),
        "combined_status": combined_status,
        "primary_remaining_issue": primary_issue,
        "audit_complete": True,
    }


def _repo_path(repo_root: Path, path: Path) -> Path:
    return repo_root / path


def _clean(value: object) -> str:
    text = str(value or "")
    return "" if text in {".", "?", "NONE"} else text


def _atom_value(row: Mapping[str, Any], field: str) -> str:
    return _clean(row.get("_atom_site." + field, ""))


def _component_value(row: Mapping[str, Any], category: str, field: str) -> str:
    return _clean(row.get(f"_{category}.{field}", ""))


def _canonical_type_symbol(value: object) -> str:
    if type(value) is not str:
        return ""
    stripped = value.strip()
    if not stripped:
        return ""
    checkpoint = {
        token.upper(): token for token in exact10_owner.CHECKPOINT_TOKEN_TO_INDEX
    }
    if stripped.upper() == "H":
        return "H"
    return checkpoint.get(stripped.upper(), stripped)


def _finite_atom(row: Mapping[str, Any]) -> bool:
    try:
        values = [float(_atom_value(row, field)) for field in (
            "Cartn_x", "Cartn_y", "Cartn_z", "occupancy",
        )]
    except ValueError:
        return False
    return all(math.isfinite(value) for value in values)


def _normalize_embedded_component_bond_order_v1(
    value_order: str, aromatic_flag: str,
) -> str:
    """Adapt entry-mmCIF alternating aromatic orders to the current owner."""

    order = value_order.strip().upper()
    aromatic = aromatic_flag.strip().upper()
    if aromatic == "Y":
        if order not in {"SING", "DOUB", "AROM"}:
            raise ClosureValidationError("UNSUPPORTED_EMBEDDED_AROMATIC_BOND_ORDER")
        return "aromatic"
    return topology_owner.normalize_bond_order(order, aromatic)


def _atom_identity(row: Mapping[str, Any], source_row_index: int) -> dict[str, Any]:
    return {
        "source_atom_site_row_index_0based": source_row_index,
        "atom_site_id": _atom_value(row, "id"),
        "group_PDB": _atom_value(row, "group_PDB"),
        "type_symbol": _canonical_type_symbol(_atom_value(row, "type_symbol")),
        "label_atom_id": _atom_value(row, "label_atom_id"),
        "label_comp_id": _atom_value(row, "label_comp_id"),
        "label_asym_id": _atom_value(row, "label_asym_id"),
        "label_seq_id": _atom_value(row, "label_seq_id"),
        "label_alt_id": _atom_value(row, "label_alt_id") or "NONE",
        "auth_atom_id": _atom_value(row, "auth_atom_id"),
        "auth_comp_id": _atom_value(row, "auth_comp_id"),
        "auth_asym_id": _atom_value(row, "auth_asym_id"),
        "auth_seq_id": _atom_value(row, "auth_seq_id"),
        "insertion_code": _atom_value(row, "pdbx_PDB_ins_code") or "NONE",
        "model_num": _atom_value(row, "pdbx_PDB_model_num") or "1",
        "occupancy": _atom_value(row, "occupancy"),
        "x": _atom_value(row, "Cartn_x"),
        "y": _atom_value(row, "Cartn_y"),
        "z": _atom_value(row, "Cartn_z"),
    }


def validate_published_execution_v1(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    payloads: dict[Path, bytes] = {}
    for path, expected in PUBLISHED_EXECUTION_SHA256.items():
        payload = _repo_path(repo_root, path).read_bytes()
        if _sha256(payload) != expected:
            raise ClosureValidationError(
                f"PUBLISHED_EXECUTION_SHA256_MISMATCH:{path.as_posix()}"
            )
        payloads[path] = payload
    manifest = json.loads(payloads[EXECUTION_MANIFEST])
    required = {
        "acquisition_valid_count": 12,
        "exact_structural_event_recovered_count": 7,
        "no_explicit_event_recovered_count": 5,
        "distance_only_inference_used": False,
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise ClosureValidationError(f"PUBLISHED_EXECUTION_RESULT_MISMATCH:{key}")
    return manifest


def derive_recovered7_rows_v1(repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    validate_published_execution_v1(repo_root)
    payload = _repo_path(repo_root, RECOVERY_SNAPSHOT).read_bytes()
    rows = _csv_rows(payload)
    recovered = [row for row in rows if row["cys_sg_event_recovered"] == "true"]
    identities = [(row["pdb_id"], row["ligand_component_id"]) for row in recovered]
    if identities != list(RECOVERED_IDENTITIES):
        raise ClosureValidationError("RECOVERED7_COHORT_MISMATCH")
    unresolved = {
        (row["pdb_id"], row["ligand_component_id"])
        for row in rows if row["cys_sg_event_recovered"] != "true"
    }
    if unresolved != set(UNRESOLVED_STRUCTURAL_REVIEW_IDENTITIES):
        raise ClosureValidationError("UNRESOLVED5_COHORT_MISMATCH")
    components = Counter(row["ligand_component_id"] for row in recovered)
    if components != Counter({"1ZB": 1, "K2Z": 1, "K36": 5}):
        raise ClosureValidationError("RECOVERED7_COMPONENT_COUNTS_MISMATCH")
    return recovered


def _raw_path(pdb_id: str) -> Path:
    return RAW_ROOT / f"{pdb_id.lower()}.cif"


def _read_verified_raw(repo_root: Path, pdb_id: str) -> tuple[Path, bytes]:
    path = _raw_path(pdb_id)
    payload = _repo_path(repo_root, path).read_bytes()
    if _sha256(payload) != RAW_SHA256_BY_PDB[pdb_id]:
        raise ClosureValidationError(f"RECOVERED7_RAW_SHA256_MISMATCH:{pdb_id}")
    return path, payload


def _parse_component_topology_from_text_v1(
    component_id: str,
    source_path: str,
    source_sha256: str,
    text: str,
) -> ComponentTopologyAuthority:
    atom_tags, raw_atoms = topology_owner._parse_loop(text, "_chem_comp_atom.")
    bond_tags, raw_bonds = topology_owner._parse_loop(text, "_chem_comp_bond.")
    required_atom_tags = {
        "_chem_comp_atom.comp_id", "_chem_comp_atom.atom_id",
        "_chem_comp_atom.type_symbol", "_chem_comp_atom.pdbx_aromatic_flag",
        "_chem_comp_atom.pdbx_stereo_config",
    }
    required_bond_tags = {
        "_chem_comp_bond.comp_id", "_chem_comp_bond.atom_id_1",
        "_chem_comp_bond.atom_id_2", "_chem_comp_bond.value_order",
        "_chem_comp_bond.pdbx_aromatic_flag",
        "_chem_comp_bond.pdbx_stereo_config",
    }
    if not required_atom_tags <= set(atom_tags):
        raise ClosureValidationError(f"TOPOLOGY_ATOM_FIELDS_MISSING:{component_id}")
    if not required_bond_tags <= set(bond_tags):
        raise ClosureValidationError(f"TOPOLOGY_BOND_FIELDS_MISSING:{component_id}")
    selected_atoms = [
        row for row in raw_atoms
        if _component_value(row, "chem_comp_atom", "comp_id") == component_id
    ]
    selected_bonds = [
        row for row in raw_bonds
        if _component_value(row, "chem_comp_bond", "comp_id") == component_id
    ]
    if not selected_atoms or not selected_bonds:
        raise ClosureValidationError(f"TOPOLOGY_EVIDENCE_REQUIRED:{component_id}")

    atoms: list[dict[str, Any]] = []
    atom_ids: set[str] = set()
    for index, row in enumerate(selected_atoms):
        atom_id = _component_value(row, "chem_comp_atom", "atom_id")
        element = topology_owner.canonicalize_element_symbol_v1(
            _component_value(row, "chem_comp_atom", "type_symbol")
        )
        if not atom_id or atom_id in atom_ids:
            raise ClosureValidationError(f"TOPOLOGY_DUPLICATE_OR_EMPTY_ATOM_ID:{component_id}")
        atom_ids.add(atom_id)
        atoms.append({
            "component_id": component_id,
            "atom_id": atom_id,
            "type_symbol": element,
            "aromatic_flag": _component_value(
                row, "chem_comp_atom", "pdbx_aromatic_flag",
            ).upper(),
            "stereo_config": _component_value(
                row, "chem_comp_atom", "pdbx_stereo_config",
            ).upper(),
            "source_component_atom_row_index_0based": index,
            "explicit_hydrogen": element == "H",
        })

    bonds: list[dict[str, Any]] = []
    bond_keys: set[tuple[str, str]] = set()
    for index, row in enumerate(selected_bonds):
        left = _component_value(row, "chem_comp_bond", "atom_id_1")
        right = _component_value(row, "chem_comp_bond", "atom_id_2")
        order = _component_value(row, "chem_comp_bond", "value_order").upper()
        aromatic = _component_value(
            row, "chem_comp_bond", "pdbx_aromatic_flag",
        ).upper()
        if left not in atom_ids or right not in atom_ids or left == right:
            raise ClosureValidationError(f"TOPOLOGY_BOND_ENDPOINT_INVALID:{component_id}")
        key = tuple(sorted((left, right)))
        if key in bond_keys:
            raise ClosureValidationError(f"TOPOLOGY_DUPLICATE_BOND:{component_id}")
        bond_keys.add(key)
        bonds.append({
            "component_id": component_id,
            "atom_id_1": left,
            "atom_id_2": right,
            "source_value_order": order,
            "source_aromatic_flag": aromatic,
            "normalized_bond_order": _normalize_embedded_component_bond_order_v1(
                order, aromatic,
            ),
            "stereo_config": _component_value(
                row, "chem_comp_bond", "pdbx_stereo_config",
            ).upper(),
            "source_component_bond_row_index_0based": index,
        })

    element_by_id = {atom["atom_id"]: atom["type_symbol"] for atom in atoms}
    semantic = {
        "atoms": sorted([
            [atom["atom_id"], atom["type_symbol"], atom["aromatic_flag"],
             atom["stereo_config"]]
            for atom in atoms
        ]),
        "bonds": sorted([
            [min(bond["atom_id_1"], bond["atom_id_2"]),
             max(bond["atom_id_1"], bond["atom_id_2"]),
             bond["source_value_order"], bond["source_aromatic_flag"],
             bond["stereo_config"]]
            for bond in bonds
        ]),
    }
    semantic_sha = _sha256(_json_bytes(semantic))
    heavy_ids = {key for key, value in element_by_id.items() if value != "H"}
    return ComponentTopologyAuthority(
        component_id=component_id,
        source_path=source_path,
        source_kind=TOPOLOGY_SOURCE_KIND,
        source_sha256=source_sha256,
        semantic_topology_sha256=semantic_sha,
        atoms=tuple(atoms),
        bonds=tuple(bonds),
        atom_count=len(atoms),
        heavy_atom_count=len(heavy_ids),
        explicit_hydrogen_atom_count=len(atoms) - len(heavy_ids),
        bond_count=len(bonds),
        heavy_heavy_bond_count=sum(
            bond["atom_id_1"] in heavy_ids and bond["atom_id_2"] in heavy_ids
            for bond in bonds
        ),
        bond_order_available=all(bool(bond["normalized_bond_order"]) for bond in bonds),
    )


def load_component_topology_authorities_v1(
    repo_root: Path = REPO_ROOT,
) -> dict[str, ComponentTopologyAuthority]:
    authorities: dict[str, ComponentTopologyAuthority] = {}
    for component_id, pdb_id in TOPOLOGY_SOURCE_PDB_BY_COMPONENT.items():
        path, payload = _read_verified_raw(repo_root, pdb_id)
        authorities[component_id] = _parse_component_topology_from_text_v1(
            component_id, path.as_posix(), _sha256(payload),
            payload.decode("utf-8", errors="strict"),
        )

    k36_semantic_hashes: dict[str, str] = {}
    for pdb_id, component_id in RECOVERED_IDENTITIES:
        if component_id != "K36":
            continue
        path, payload = _read_verified_raw(repo_root, pdb_id)
        parsed = _parse_component_topology_from_text_v1(
            component_id, path.as_posix(), _sha256(payload),
            payload.decode("utf-8", errors="strict"),
        )
        k36_semantic_hashes[pdb_id] = parsed.semantic_topology_sha256
    if len(set(k36_semantic_hashes.values())) != 1:
        raise ClosureValidationError("K36_EMBEDDED_TOPOLOGY_SEMANTIC_DRIFT")
    if next(iter(k36_semantic_hashes.values())) != authorities[
        "K36"
    ].semantic_topology_sha256:
        raise ClosureValidationError("K36_SHARED_TOPOLOGY_AUTHORITY_MISMATCH")
    return authorities


def _event_stage_row(snapshot_row: Mapping[str, str]) -> dict[str, str]:
    return {
        "canonical_candidate_id": snapshot_row["canonical_candidate_id"],
        "ligand_component_id": snapshot_row["ligand_component_id"],
        "protein_chain": snapshot_row["protein_chain_if_recovered"],
        "cys_residue_sequence": snapshot_row["cys_residue_sequence_if_recovered"],
        "cys_insertion_code": snapshot_row["cys_insertion_code_if_recovered"],
    }


def _same_coordinates(row: Mapping[str, Any], xyz: Sequence[float]) -> bool:
    try:
        observed = tuple(float(_atom_value(row, axis)) for axis in (
            "Cartn_x", "Cartn_y", "Cartn_z",
        ))
    except ValueError:
        return False
    return all(abs(left - right) <= 1e-9 for left, right in zip(observed, xyz))


def _instance_matches(
    row: Mapping[str, Any], component_id: str, chain: str, sequence: str,
) -> bool:
    component = _atom_value(row, "auth_comp_id") or _atom_value(row, "label_comp_id")
    auth = (
        _atom_value(row, "auth_asym_id") == chain
        and _atom_value(row, "auth_seq_id") == sequence
    )
    label = (
        _atom_value(row, "label_asym_id") == chain
        and _atom_value(row, "label_seq_id") == sequence
    )
    return component == component_id and (auth or label)


def select_ligand_instance_atoms_v1(
    indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
    component_id: str,
    chain: str,
    sequence: str,
    selected_model: str,
    selected_altloc: str,
) -> list[tuple[int, Mapping[str, Any]]]:
    selected: list[tuple[int, Mapping[str, Any]]] = []
    for source_index, row in indexed_atom_rows:
        if not _instance_matches(row, component_id, chain, sequence):
            continue
        if (_atom_value(row, "pdbx_PDB_model_num") or "1") != selected_model:
            continue
        altloc = _atom_value(row, "label_alt_id")
        if altloc not in ({""} if not selected_altloc else {"", selected_altloc}):
            continue
        if not _finite_atom(row):
            raise ClosureValidationError("LIGAND_INSTANCE_COORDINATE_INVALID")
        selected.append((source_index, row))
    if not selected:
        raise ClosureValidationError("WRONG_OR_MISSING_LIGAND_INSTANCE")
    atom_site_ids = [_atom_value(row, "id") for _, row in selected]
    if not all(atom_site_ids) or len(atom_site_ids) != len(set(atom_site_ids)):
        raise ClosureValidationError("LIGAND_SOURCE_IDENTITY_NOT_UNIQUE")
    return selected


def map_observed_heavy_to_topology_v1(
    observed: Sequence[tuple[int, Mapping[str, Any]]],
    topology: ComponentTopologyAuthority,
    reactive_atom_name: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    topology_by_name = {atom["atom_id"]: atom for atom in topology.atoms}
    if len(topology_by_name) != len(topology.atoms):
        raise ClosureValidationError("DUPLICATE_TOPOLOGY_ATOM_MAPPING")
    heavy_observed = [
        (index, row) for index, row in observed
        if _canonical_type_symbol(_atom_value(row, "type_symbol")) != "H"
    ]
    names = [_atom_value(row, "label_atom_id") for _, row in heavy_observed]
    if not all(names) or len(names) != len(set(names)):
        raise ClosureValidationError("DUPLICATE_OR_EMPTY_OBSERVED_ATOM_MAPPING")
    mapped: list[dict[str, Any]] = []
    for source_index, row in heavy_observed:
        name = _atom_value(row, "label_atom_id")
        topology_atom = topology_by_name.get(name)
        if topology_atom is None or topology_atom["explicit_hydrogen"]:
            raise ClosureValidationError(f"MISSING_RETAINED_HEAVY_TOPOLOGY_ATOM:{name}")
        observed_symbol = _canonical_type_symbol(_atom_value(row, "type_symbol"))
        if observed_symbol.upper() != topology_atom["type_symbol"].upper():
            raise ClosureValidationError(f"TOPOLOGY_ELEMENT_MISMATCH:{name}")
        identity = _atom_identity(row, source_index)
        identity.update({
            "topology_atom_id": topology_atom["atom_id"],
            "topology_type_symbol": topology_atom["type_symbol"],
            "mapping_status": "EXACT_ATOM_NAME_AND_ELEMENT",
        })
        mapped.append(identity)
    if sum(item["topology_atom_id"] == reactive_atom_name for item in mapped) != 1:
        raise ClosureValidationError("REACTIVE_LIGAND_ATOM_MAPPING_NOT_EXACTLY_ONE")
    mapped_names = {item["topology_atom_id"] for item in mapped}
    topology_heavy_names = {
        atom["atom_id"] for atom in topology.atoms if not atom["explicit_hydrogen"]
    }
    not_observed = sorted(topology_heavy_names - mapped_names)
    return mapped, not_observed


def realize_exact10_v1(
    indexed_rows: Sequence[tuple[int, Mapping[str, Any]]], domain: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    symbols = [
        _canonical_type_symbol(_atom_value(row, "type_symbol"))
        for _, row in indexed_rows
    ]
    projection = exact10_owner.project_type_symbols_to_checkpoint_heavy_v1(symbols)
    rejected: list[dict[str, Any]] = []
    if projection.sample_rejected:
        for (source_index, row), symbol_class in zip(
            indexed_rows, projection.symbol_classes,
        ):
            if symbol_class not in {"unsupported_nonhydrogen", "missing_or_invalid"}:
                continue
            rejected.append({
                "domain": domain,
                "raw_atom_identity": _atom_identity(row, source_index),
                "element": _canonical_type_symbol(_atom_value(row, "type_symbol")),
                "model_bound_reason": (
                    "exact recovered ligand instance" if domain == "ligand"
                    else f"canonical protein atom within {POCKET_RADIUS_ANGSTROM:.1f}A pocket"
                ),
                "exact10_rejection": symbol_class,
            })
        return [], rejected, sum(
            item == "explicit_hydrogen" for item in projection.symbol_classes
        )
    retained: list[dict[str, Any]] = []
    for (source_index, row), keep, channel in zip(
        indexed_rows, projection.keep_mask, projection.checkpoint_channel_indices,
    ):
        if not keep:
            continue
        identity = _atom_identity(row, source_index)
        identity["exact10_channel_index"] = channel
        retained.append(identity)
    return retained, rejected, sum(
        item == "explicit_hydrogen" for item in projection.symbol_classes
    )


def build_canonical_pocket_v1(
    indexed_atom_rows: Sequence[tuple[int, Mapping[str, Any]]],
    ligand_heavy_rows: Sequence[tuple[int, Mapping[str, Any]]],
) -> list[tuple[int, Mapping[str, Any]]]:
    if not ligand_heavy_rows:
        raise ClosureValidationError("EMPTY_LIGAND_POCKET_SEED")
    ligand_coordinates = [
        full_atom_pocket_owner._coords(dict(row)) for _, row in ligand_heavy_rows
    ]
    pocket: list[tuple[int, Mapping[str, Any]]] = []
    for source_index, row in indexed_atom_rows:
        mutable = dict(row)
        if _atom_value(row, "group_PDB") != "ATOM":
            continue
        if not full_atom_pocket_owner._model_allowed(mutable):
            continue
        if not full_atom_pocket_owner._altloc_allowed(mutable):
            continue
        if not _finite_atom(row):
            raise ClosureValidationError("PROTEIN_COORDINATE_INVALID")
        coordinates = full_atom_pocket_owner._coords(mutable)
        minimum = min(
            full_atom_pocket_owner._distance(coordinates, ligand_xyz)
            for ligand_xyz in ligand_coordinates
        )
        if minimum <= POCKET_RADIUS_ANGSTROM:
            pocket.append((source_index, row))
    if not pocket:
        raise ClosureValidationError("EMPTY_CANONICAL_POCKET")
    identities = [_atom_value(row, "id") for _, row in pocket]
    if not all(identities) or len(identities) != len(set(identities)):
        raise ClosureValidationError("POCKET_SOURCE_IDENTITY_NOT_UNIQUE")
    return pocket


def _endpoint_candidates(
    indexed_rows: Sequence[tuple[int, Mapping[str, Any]]],
    component_id: str,
    atom_name: str,
    chain: str,
    sequence: str,
    coordinates: Sequence[float],
) -> list[tuple[int, Mapping[str, Any]]]:
    return [
        (index, row) for index, row in indexed_rows
        if _instance_matches(row, component_id, chain, sequence)
        and (_atom_value(row, "auth_atom_id") or _atom_value(row, "label_atom_id"))
        == atom_name
        and _same_coordinates(row, coordinates)
        and _finite_atom(row)
    ]


def _target_membership(
    pocket: Sequence[tuple[int, Mapping[str, Any]]],
    chain: str,
    sequence: str,
    insertion: str,
) -> tuple[bool, bool]:
    target = [
        row for _, row in pocket
        if (_atom_value(row, "auth_comp_id") or _atom_value(row, "label_comp_id"))
        == "CYS"
        and _atom_value(row, "auth_asym_id") == chain
        and _atom_value(row, "auth_seq_id") == sequence
        and (_atom_value(row, "pdbx_PDB_ins_code") or "NONE") == insertion
    ]
    return bool(target), sum(
        (_atom_value(row, "auth_atom_id") or _atom_value(row, "label_atom_id"))
        == "SG" for row in target
    ) == 1


def _topology_json(authority: ComponentTopologyAuthority) -> dict[str, Any]:
    return {
        "component_id": authority.component_id,
        "authoritative_topology_source_found": True,
        "source_path": authority.source_path,
        "source_kind": authority.source_kind,
        "source_sha256": authority.source_sha256,
        "semantic_topology_sha256": authority.semantic_topology_sha256,
        "atom_count": authority.atom_count,
        "heavy_atom_count": authority.heavy_atom_count,
        "explicit_hydrogen_atom_count": authority.explicit_hydrogen_atom_count,
        "bond_count": authority.bond_count,
        "heavy_heavy_bond_count": authority.heavy_heavy_bond_count,
        "bond_order_available": authority.bond_order_available,
        "component_atoms": list(authority.atoms),
        "component_internal_bonds": list(authority.bonds),
        "reaction_specific_post_graph_proven": False,
    }


def _build_sample(
    repo_root: Path,
    snapshot_row: Mapping[str, str],
    topology: ComponentTopologyAuthority,
    downstream_authority_context: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pdb_id = snapshot_row["pdb_id"]
    component_id = snapshot_row["ligand_component_id"]
    raw_path, raw_payload = _read_verified_raw(repo_root, pdb_id)
    text = raw_payload.decode("utf-8", errors="strict")
    decision = event_owner.recover_exact_struct_conn_event_v1(
        text, _event_stage_row(snapshot_row),
    )
    if not decision.recovered:
        raise ClosureValidationError(f"EVENT_MAPPING_FAILED:{pdb_id}:{decision.status}")
    if decision.reactive_ligand_atom != snapshot_row[
        "reactive_ligand_atom_if_recovered"
    ]:
        raise ClosureValidationError(f"EVENT_REACTIVE_ATOM_DRIFT:{pdb_id}")

    atom_rows = atom_site_owner.extract_atom_site_loop_rows_v0(text)
    indexed_rows = list(enumerate(atom_rows))
    protein_endpoints = _endpoint_candidates(
        indexed_rows, "CYS", "SG", decision.protein_chain,
        decision.cys_residue_sequence, decision.protein_coordinates or (),
    )
    ligand_endpoints = _endpoint_candidates(
        indexed_rows, component_id, decision.reactive_ligand_atom,
        decision.ligand_chain_or_instance, decision.ligand_sequence_or_instance,
        decision.ligand_coordinates or (),
    )
    if len(protein_endpoints) != 1 or len(ligand_endpoints) != 1:
        raise ClosureValidationError(f"EVENT_ENDPOINT_MAPPING_NOT_UNIQUE:{pdb_id}")
    protein_endpoint_index, protein_endpoint = protein_endpoints[0]
    ligand_endpoint_index, ligand_endpoint = ligand_endpoints[0]
    selected_model = _atom_value(ligand_endpoint, "pdbx_PDB_model_num") or "1"
    selected_altloc = _atom_value(ligand_endpoint, "label_alt_id")
    ligand_instance = select_ligand_instance_atoms_v1(
        indexed_rows, component_id, decision.ligand_chain_or_instance,
        decision.ligand_sequence_or_instance, selected_model, selected_altloc,
    )
    mapped_heavy, topology_heavy_not_observed = map_observed_heavy_to_topology_v1(
        ligand_instance, topology, decision.reactive_ligand_atom,
    )
    ligand_heavy_source_indices = {
        item["source_atom_site_row_index_0based"] for item in mapped_heavy
    }
    ligand_heavy_rows = [
        item for item in ligand_instance if item[0] in ligand_heavy_source_indices
    ]
    pocket_preprojection = build_canonical_pocket_v1(indexed_rows, ligand_heavy_rows)
    target_cys_present, target_sg_present = _target_membership(
        pocket_preprojection, decision.protein_chain, decision.cys_residue_sequence,
        decision.cys_insertion_code,
    )
    if not target_cys_present or not target_sg_present:
        raise ClosureValidationError(f"TARGET_CYS_SG_NOT_IN_POCKET:{pdb_id}")

    canonical_ligand, ligand_rejected, ligand_h_count = realize_exact10_v1(
        ligand_instance, "ligand",
    )
    canonical_pocket, pocket_rejected, pocket_h_count = realize_exact10_v1(
        pocket_preprojection, "pocket",
    )
    rejected = ligand_rejected + pocket_rejected
    exact10_pass = not rejected
    exact10_status = (
        "EXACT10_PASS" if exact10_pass else "EXACT10_REJECT_UNSUPPORTED_NONH"
    )
    mechanical = (
        "MECHANICAL_CLOSURE_PASS" if exact10_pass
        else "EXACT10_REJECT_UNSUPPORTED_NONH"
    )
    downstream_authority_audit = (
        build_downstream_chemistry_authority_audit_v1(
            snapshot_row, downstream_authority_context,
        )
    )
    downstream = downstream_authority_audit["combined_status"]
    primary_issue = (
        downstream_authority_audit["primary_remaining_issue"]
        if exact10_pass else exact10_status
    )

    channel_by_source = {
        item["source_atom_site_row_index_0based"]: item["exact10_channel_index"]
        for item in canonical_ligand
    }
    for item in mapped_heavy:
        item["exact10_channel_index"] = channel_by_source.get(
            item["source_atom_site_row_index_0based"]
        )
    matrix = {
        "canonical_candidate_id": snapshot_row["canonical_candidate_id"],
        "pdb_id": pdb_id,
        "ligand_component_id": component_id,
        "raw_sha256": _sha256(raw_payload),
        "event_reactive_residue_atom": "SG",
        "event_reactive_ligand_atom": decision.reactive_ligand_atom,
        "event_mapping_status": "EXACT_EVENT_ENDPOINT_MAPPING_PASS",
        "topology_source_kind": topology.source_kind,
        "topology_source_identity": (
            topology.source_path + f"#chem_comp_atom_and_bond:{component_id}"
        ),
        "topology_source_sha256": topology.source_sha256,
        "ligand_observed_heavy_atom_count": len(mapped_heavy),
        "topology_heavy_atom_count": topology.heavy_atom_count,
        "ligand_heavy_atom_mapping_status": "EXACT_OBSERVED_HEAVY_MAPPING_PASS",
        "topology_atom_mapping_status": "TOPOLOGY_MAPPING_PASS",
        "canonical_ligand_heavy_atom_count": len(canonical_ligand),
        "explicit_hydrogen_excluded_count": ligand_h_count + pocket_h_count,
        "unsupported_nonh_model_bound_count": len(rejected),
        "canonical_model_atom_set_status": "CANONICAL_MODEL_ATOM_SET_PASS",
        "exact10_status": exact10_status,
        "pocket_atom_count": len(canonical_pocket),
        "target_cys_present": target_cys_present,
        "target_sg_present": target_sg_present,
        "pocket_status": "POCKET_PASS",
        "mechanical_closure_status": mechanical,
        "downstream_chemistry_label_status": downstream,
        "primary_remaining_issue": primary_issue,
    }
    detail = {
        "canonical_candidate_id": snapshot_row["canonical_candidate_id"],
        "pdb_id": pdb_id,
        "ligand_component_id": component_id,
        "raw_source": {
            "path": raw_path.as_posix(),
            "sha256": _sha256(raw_payload),
            "atom_site_row_count": len(atom_rows),
        },
        "explicit_event": {
            "event_mapping_status": matrix["event_mapping_status"],
            "event_owner_status": decision.status,
            "altloc_occupancy_provenance": decision.altloc_occupancy_provenance,
            "protein_endpoint": _atom_identity(
                protein_endpoint, protein_endpoint_index,
            ),
            "ligand_endpoint": _atom_identity(ligand_endpoint, ligand_endpoint_index),
            "protein_ligand_covalent_event_edge": {
                "protein_atom_site_id": _atom_value(protein_endpoint, "id"),
                "protein_atom_name": "SG",
                "ligand_atom_site_id": _atom_value(ligand_endpoint, "id"),
                "ligand_atom_name": decision.reactive_ligand_atom,
                "evidence_kind": "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR",
                "part_of_ligand_internal_topology": False,
            },
        },
        "topology_mapping": {
            "topology_source_component_id": component_id,
            "topology_source_path": topology.source_path,
            "topology_source_sha256": topology.source_sha256,
            "semantic_topology_sha256": topology.semantic_topology_sha256,
            "mapping_status": matrix["topology_atom_mapping_status"],
            "selected_ligand_altloc": selected_altloc or "NONE",
            "selected_ligand_model": selected_model,
            "observed_heavy_atom_mapping": mapped_heavy,
            "topology_heavy_atoms_not_observed": topology_heavy_not_observed,
            "topology_heavy_atoms_not_observed_interpretation": (
                "component_graph_atoms_absent_from_observed_instance; no PRE or "
                "reaction-state reconstruction performed"
            ),
        },
        "canonical_model_bound_ligand_atoms": canonical_ligand,
        "canonical_pocket": {
            "radius_angstrom": POCKET_RADIUS_ANGSTROM,
            "selection_owner": REUSED_OWNERS["pocket"],
            "protein_only_group_PDB_ATOM": True,
            "alternate_model_policy": "model_1_only",
            "altloc_policy": "blank_or_A",
            "target_cys_present": target_cys_present,
            "target_sg_present": target_sg_present,
            "retained_atoms": canonical_pocket,
        },
        "exact10": {
            "channel_order": exact10_owner.CHECKPOINT_CHANNEL_ORDER,
            "status": exact10_status,
            "explicit_hydrogen_excluded_count": ligand_h_count + pocket_h_count,
            "unsupported_nonh_model_bound_atoms": rejected,
            "unknown_or_other_channel_present": False,
            "zero_vector_fallback_used": False,
        },
        "mechanical_closure_status": mechanical,
        "downstream_chemistry_label_status": downstream,
        "downstream_chemistry_authority_audit": downstream_authority_audit,
    }
    return matrix, detail


def build_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_artifacts_v1(
    repo_root: Path = REPO_ROOT,
) -> dict[str, bytes]:
    execution_manifest = validate_published_execution_v1(repo_root)
    recovered_rows = derive_recovered7_rows_v1(repo_root)
    topologies = load_component_topology_authorities_v1(repo_root)
    downstream_authority_context = load_downstream_authority_context_v1(repo_root)
    matrix_rows: list[dict[str, Any]] = []
    sample_details: list[dict[str, Any]] = []
    for row in recovered_rows:
        matrix, detail = _build_sample(
            repo_root, row, topologies[row["ligand_component_id"]],
            downstream_authority_context,
        )
        matrix_rows.append(matrix)
        sample_details.append(detail)

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "published_execution_commit": PUBLISHED_EXECUTION_COMMIT,
        "published_execution_manifest_sha256": PUBLISHED_EXECUTION_SHA256[
            EXECUTION_MANIFEST
        ],
        "published_recovery_snapshot_sha256": PUBLISHED_EXECUTION_SHA256[
            RECOVERY_SNAPSHOT
        ],
        "reused_owners": REUSED_OWNERS,
        "downstream_authority_owners": DOWNSTREAM_AUTHORITY_OWNERS,
        "downstream_authority_source_sha256": {
            path.as_posix(): sha256
            for path, sha256 in DOWNSTREAM_AUTHORITY_SOURCE_SHA256.items()
        },
        "component_topology_authorities": {
            component: _topology_json(topologies[component])
            for component in sorted(topologies)
        },
        "samples": sample_details,
        "k36_shared_topology_reuse": True,
        "k36_independent_sample_mapping_count": 5,
        "distance_based_bond_inference_used": False,
        "rdkit_used": False,
    }
    matrix_payload = _csv_bytes(matrix_rows)
    evidence_payload = _json_bytes(evidence)
    status_counts = Counter(row["mechanical_closure_status"] for row in matrix_rows)
    downstream_counts = Counter(
        row["downstream_chemistry_label_status"] for row in matrix_rows
    )
    if (
        set(downstream_counts) - FINAL_DOWNSTREAM_STATUSES
        or sum(downstream_counts.values()) != len(matrix_rows)
    ):
        raise ClosureValidationError("DOWNSTREAM_STATUS_COUNTS_INVALID")
    exact10_pass_count = sum(row["exact10_status"] == "EXACT10_PASS" for row in matrix_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "implementation_status": "CANDIDATE_IMPLEMENTED_AND_VALIDATED",
        "published_execution_commit": PUBLISHED_EXECUTION_COMMIT,
        "published_execution_owner_sha256": PUBLISHED_EXECUTION_SHA256[
            EXECUTION_SOURCE
        ],
        "published_execution_audit_sha256": PUBLISHED_EXECUTION_SHA256[
            EXECUTION_AUDIT
        ],
        "published_execution_manifest_sha256": PUBLISHED_EXECUTION_SHA256[
            EXECUTION_MANIFEST
        ],
        "published_recovery_snapshot_sha256": PUBLISHED_EXECUTION_SHA256[
            RECOVERY_SNAPSHOT
        ],
        "published_scientific_result": {
            key: execution_manifest[key] for key in (
                "acquisition_valid_count", "exact_structural_event_recovered_count",
                "no_explicit_event_recovered_count", "distance_only_inference_used",
            )
        },
        "recovered_candidate_count": len(matrix_rows),
        "recovered_identity_list": [f"{pdb}/{component}" for pdb, component in RECOVERED_IDENTITIES],
        "unique_ligand_component_count": len(topologies),
        "unique_ligand_component_list": sorted(topologies),
        "topology_source_available_component_count": len(topologies),
        "topology_source_missing_component_count": 0,
        "event_mapping_pass_count": sum(
            row["event_mapping_status"] == "EXACT_EVENT_ENDPOINT_MAPPING_PASS"
            for row in matrix_rows
        ),
        "topology_mapping_pass_count": sum(
            row["topology_atom_mapping_status"] == "TOPOLOGY_MAPPING_PASS"
            for row in matrix_rows
        ),
        "canonical_model_atom_set_pass_count": sum(
            row["canonical_model_atom_set_status"] == "CANONICAL_MODEL_ATOM_SET_PASS"
            for row in matrix_rows
        ),
        "exact10_pass_count": exact10_pass_count,
        "exact10_reject_count": len(matrix_rows) - exact10_pass_count,
        "pocket_pass_count": sum(row["pocket_status"] == "POCKET_PASS" for row in matrix_rows),
        "mechanical_closure_pass_count": status_counts["MECHANICAL_CLOSURE_PASS"],
        "downstream_already_authoritative_count": downstream_counts["ALREADY_AUTHORITATIVE"],
        "downstream_automatic_rule_available_count": downstream_counts["AUTOMATIC_RULE_AVAILABLE"],
        "downstream_human_chemistry_review_required_count": downstream_counts[
            "HUMAN_CHEMISTRY_REVIEW_REQUIRED"
        ],
        "downstream_chemistry_authority_audit_complete": (
            len(sample_details) == len(matrix_rows)
            and all(
                sample["downstream_chemistry_authority_audit"]["audit_complete"]
                for sample in sample_details
            )
        ),
        "downstream_authority_audited_candidate_count": sum(
            sample["downstream_chemistry_authority_audit"]["audit_complete"]
            for sample in sample_details
        ),
        "downstream_human_review_was_hardcoded_before_repair": True,
        "k36_independent_downstream_authority_audit_count": sum(
            sample["ligand_component_id"] == "K36"
            and sample["downstream_chemistry_authority_audit"]["audit_complete"]
            for sample in sample_details
        ),
        "k36_shared_topology_reuse": True,
        "k36_shared_semantic_topology_sha256": topologies[
            "K36"
        ].semantic_topology_sha256,
        "k36_independent_sample_mapping_count": 5,
        "explicit_hydrogen_excluded_total": sum(
            row["explicit_hydrogen_excluded_count"] for row in matrix_rows
        ),
        "unsupported_nonh_model_bound_total": sum(
            row["unsupported_nonh_model_bound_count"] for row in matrix_rows
        ),
        "reused_owners": REUSED_OWNERS,
        "downstream_authority_owners": DOWNSTREAM_AUTHORITY_OWNERS,
        "downstream_authority_source_sha256": {
            path.as_posix(): sha256
            for path, sha256 in DOWNSTREAM_AUTHORITY_SOURCE_SHA256.items()
        },
        "deterministic_output_sha256": {
            MATRIX_FILE: _sha256(matrix_payload),
            EVIDENCE_FILE: _sha256(evidence_payload),
        },
        "network_request_executed": False,
        "raw_structure_downloaded": False,
        "ccd_downloaded": False,
        "topology_downloaded": False,
        "distance_based_bond_inference_used": False,
        "inverse_reaction_chemistry_executed": False,
        "pre_geometry_reconstruction_executed": False,
        "torsion_sampling_executed": False,
        "mmff_executed": False,
        "uff_executed": False,
        "rdkit_used": False,
        "rdkit_minimization_executed": False,
        "geometry_loss_activation": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "trainer_fit": False,
        "formal_training": False,
        "rl": False,
        "published_execution_modified": False,
        "published_authority_modified": False,
        "published_b0_modified": False,
        "current11_modified": False,
        "raw_modified": False,
        "manifest_self_sha256_recorded": False,
        "ready_for_recovered7_closure_publication": True,
        "ready_for_automated_chemistry_label_stage": downstream_counts[
            "AUTOMATIC_RULE_AVAILABLE"
        ] > 0,
        "ready_for_automated_chemistry_label_execution": downstream_counts[
            "AUTOMATIC_RULE_AVAILABLE"
        ] > 0,
        "ready_for_targeted_chemistry_review_package_generation": (
            downstream_counts["HUMAN_CHEMISTRY_REVIEW_REQUIRED"] > 0
        ),
        "ready_for_bulk_expansion": False,
        "ready_for_geometry_loss_activation": False,
        "ready_for_training": False,
        "recommended_next_step_exactly": (
            "review_and_publish_covapie_cys_sg_recovered7_canonical_topology_"
            "exact10_pocket_closure_v1"
        ),
    }
    return {
        MATRIX_FILE: matrix_payload,
        EVIDENCE_FILE: evidence_payload,
        MANIFEST_FILE: _json_bytes(manifest),
    }


def materialize_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1(
    repo_root: Path = REPO_ROOT,
    output_root: Path | None = None,
) -> dict[str, str]:
    artifacts = (
        build_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_artifacts_v1(
            repo_root
        )
    )
    destination = output_root or _repo_path(repo_root, OUTPUT_ROOT)
    destination.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        (destination / name).write_bytes(artifacts[name])
    return {name: _sha256(artifacts[name]) for name in OUTPUT_FILES}


def main() -> None:
    materialize_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1()


if __name__ == "__main__":
    main()
