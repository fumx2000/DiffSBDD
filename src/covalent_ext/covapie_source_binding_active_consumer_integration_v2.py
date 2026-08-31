"""Read-only integration of all published source-binding V2 consumers."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Mapping, NoReturn

from covalent_ext import (
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2 as two_a2_v2,
)
from covalent_ext import (
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v2 as cht_v2,
)
from covalent_ext import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v2 as f24_v2,
)
from covalent_ext import (
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v2 as neq_v2,
)
from covalent_ext import (
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2 as ozj_v2,
)
from covalent_ext import covapie_source_binding_policy_v2 as source_binding_v2
from covalent_ext import (
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v2 as yun_v2,
)


__all__ = (
    "SourceBindingActiveConsumerIntegrationV2Error",
    "verify_covapie_source_binding_active_consumer_integration_v2",
)


_ERROR_PREFIX = "COVAPIE_SOURCE_BINDING_ACTIVE_CONSUMER_INTEGRATION_V2_ERROR"

_SOURCE_BINDING_POLICY_SPEC = (
    "SOURCE_BINDING_POLICY_V2",
    Path("src/covalent_ext/covapie_source_binding_policy_v2.py"),
    3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
)

_ACTIVE_CONSUMER_SPECS = (
    (
        "YUN",
        Path(
            "src/covalent_ext/"
            "covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        21294,
        "a10c929ea86258ac39bc787b3108d622b65c97617e62b19a44bf3711fbffbd52",
        Path(
            "scripts/"
            "check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        28382,
        "f0de27832eb557d1f1150ecddc00a023c7e1d81642cc1c92ef606b302c2a54b2",
        "5a34e260e57598ab62905f0171e43a67acc188e2",
    ),
    (
        "NEQ",
        Path(
            "src/covalent_ext/"
            "covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        26491,
        "21c6d4f13589a72d8762185108eaa26387c124121bdbbed8f6258b689b0a9b4d",
        Path(
            "scripts/"
            "check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        36383,
        "07c8a64442752a39aaba448db79b5f8299ea97524485e75be956de62337e465b",
        "baab1358bcc8f776df20d8dc76ed476d51ba27f3",
    ),
    (
        "CHT",
        Path(
            "src/covalent_ext/"
            "covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        27636,
        "e163f77de8bb03f107efc955ce8662291f9b39deb0ba341b72494d07b97cf87a",
        Path(
            "scripts/"
            "check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        38205,
        "9642786fb9807da59f189a4a9023b0e9310c06780b357054b464179ddc5a226d",
        "9e7d520de0baa5e5f107985f45b97f576bbd8fc0",
    ),
    (
        "OZJ",
        Path(
            "src/covalent_ext/"
            "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        30745,
        "51af9985cf4de28d48cc55eab71b536472220221d160ee6070677512ba22ef21",
        Path(
            "scripts/"
            "check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        42913,
        "dec67ac8e86273d49b3da048a7286b900b1171f93ffe85a07a6c1830383dd825",
        "33d08ee6069592f0fe28ca53bed5615f578d10fc",
    ),
    (
        "F24",
        Path(
            "src/covalent_ext/"
            "covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        25212,
        "c83aa221721849cff1ee9e3fed4154204333edb6207ec6cceb70348802bcf253",
        Path(
            "scripts/"
            "check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        44863,
        "51a8af193c8c2eeb097a53cac66a25c0688b5e9066c6e07f0891fbbf897746a9",
        "a81be8b1260d14b385b0faf05e2ddcc56bd403d8",
    ),
    (
        "2A2",
        Path(
            "src/covalent_ext/"
            "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        34512,
        "9f6c7c935358cc2f8dd1d5e71c285abc5c22eb7160be74afa12f42c85de4a0a9",
        Path(
            "scripts/"
            "check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py"
        ),
        49029,
        "0a132b715abbfcb7c53f7b354d1b7cb6211993d2355675d3631843bd5aef905c",
        "1e77d93929e491e589060269416b34fe47c0fb15",
    ),
)

_PUBLISHED_V1_PROJECTION_SPECS = (
    (
        "YUN",
        (
            (
                "covapie_yun_completed_human_decision_snapshot_v1.json",
                34388,
                "6ce626eb5fcbc8f875f727732daa6047ac35152319db8cfe444725e648d6a012",
            ),
            (
                "covapie_yun_event_task_label_availability_v1.csv",
                13886,
                "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e",
            ),
            (
                "covapie_yun_completed_decision_ingestion_summary_v1.json",
                3983,
                "899faf081224d113bd6e8b277464dbb0b0ee1a992d5262d9b34736b68f42c32e",
            ),
            (
                "covapie_yun_completed_decision_ingestion_manifest_v1.json",
                16350,
                "18eb6bbfcebb0498b84da22d2e32770f10cf3f3a03f4db6aa58b0c9e6d34204c",
            ),
        ),
    ),
    (
        "NEQ",
        (
            (
                "covapie_neq_completed_human_decision_snapshot_v1.json",
                33094,
                "9f3b8a29410852fe9fdd42cea10f8778e84a1ffe0627b1795fd6380989a2db1c",
            ),
            (
                "covapie_neq_event_task_label_availability_v1.csv",
                11706,
                "b4b9a301440724464cb92f1b0f28ef1151b24b12eb3ec001a971dacda3632d4a",
            ),
            (
                "covapie_neq_completed_decision_ingestion_summary_v1.json",
                4196,
                "a6e3fe3326e1cc51746817b547d0b737d3f4be56fe4d5427667c11d9bf019ef3",
            ),
            (
                "covapie_neq_completed_decision_ingestion_manifest_v1.json",
                18257,
                "4c6ad894929b93a0f450bcad56488aa2c4993de58e88660fd14819b3bd332488",
            ),
        ),
    ),
    (
        "CHT",
        (
            (
                "covapie_cht_completed_human_decision_snapshot_v1.json",
                30409,
                "9185ecb6ee62349c4f4cc9c384c30c1fa6d5dedc9e3eaa50e2e352f72e74a163",
            ),
            (
                "covapie_cht_event_task_label_availability_v1.csv",
                10225,
                "a754c0764ec61eacf7ec64dabdc370e4bca5a00abdfb94ea3923b52be55df6b6",
            ),
            (
                "covapie_cht_completed_decision_ingestion_summary_v1.json",
                4266,
                "22e89e8938438f01d35aa1b66be0613f5fc532cd495f9b424b5500458eee91f6",
            ),
            (
                "covapie_cht_completed_decision_ingestion_manifest_v1.json",
                18366,
                "f4614719cd554c47eb67f895415e8595f00a346095ffb53cffd4bffec0e85b59",
            ),
        ),
    ),
    (
        "OZJ",
        (
            (
                "covapie_ozj_completed_human_decision_snapshot_v1.json",
                31404,
                "3458c3559963b09f69495ffe8cf43511a1e84b7de5ad0c84279ccdcd100a4b25",
            ),
            (
                "covapie_ozj_event_task_label_availability_v1.csv",
                9031,
                "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3",
            ),
            (
                "covapie_ozj_completed_decision_ingestion_summary_v1.json",
                4803,
                "305bb814c97a450e8dc95961433daf1e9aca942537469153a89d7e322c6c3214",
            ),
            (
                "covapie_ozj_completed_decision_ingestion_manifest_v1.json",
                18554,
                "ca1e305920afd724c138ed572764bd3147039345034ebd172dfb1e274a4a1468",
            ),
        ),
    ),
    (
        "F24",
        (
            (
                "covapie_f24_completed_human_decision_snapshot_v1.json",
                22044,
                "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11",
            ),
            (
                "covapie_f24_event_task_label_availability_v1.csv",
                7641,
                "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c",
            ),
            (
                "covapie_f24_completed_decision_ingestion_summary_v1.json",
                3462,
                "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385",
            ),
            (
                "covapie_f24_completed_decision_ingestion_manifest_v1.json",
                16125,
                "02f56545297fb78c2b2cbd205115d9dca680a8446bfb753109428b698bdd5dfd",
            ),
        ),
    ),
    (
        "2A2",
        (
            (
                "covapie_2a2_completed_human_decision_snapshot_v1.json",
                29063,
                "87cfffd1c9e2e82db6d9aeba2dfedc907b459d89c0160c50fb9fbddee7393000",
            ),
            (
                "covapie_2a2_event_task_label_availability_v1.csv",
                8950,
                "f6533013dcb2eea5fcee579d906c7ab3009d1db8c9f2d9f906aca5ee0122f52b",
            ),
            (
                "covapie_2a2_completed_decision_ingestion_summary_v1.json",
                4623,
                "6c5a92910becab41a4e3af0317fa3438d6a682e1dac4d4ef1d4e48fe34773ea2",
            ),
            (
                "covapie_2a2_completed_decision_ingestion_manifest_v1.json",
                19083,
                "af20556b9a9197d2c9ddfd3fc19d01ef43a51f935aa1fdc29bac0e4c5f410287",
            ),
        ),
    ),
)

_CURRENT_CENSUS_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"
)
_CURRENT_CENSUS_SPECS = (
    (
        "CURRENT_2A2_CENSUS_CSV",
        _CURRENT_CENSUS_ROOT
        / "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.csv",
        529994,
        "5b56422e9c8d0ec6c09fe71c49d51fff0c7e7a9720ccf3c4c20dc324e409c57d",
    ),
    (
        "CURRENT_2A2_CENSUS_SUMMARY",
        _CURRENT_CENSUS_ROOT
        / "covapie_cumulative1000_current_global_readiness_summary_with_2a2_v1.json",
        17389,
        "3217bf5e45de40e66f1af22d000a48fef81548c6431c3e6d9349c4824b1c80f3",
    ),
    (
        "CURRENT_2A2_CENSUS_MANIFEST",
        _CURRENT_CENSUS_ROOT
        / "covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json",
        47068,
        "c30f8f52fc20495a06f7bead98ac80197f434eeb0b4776a1ef2c152f13d1e2b7",
    ),
)

_CURRENT_CENSUS_HEADER = (
    "scaleup_rank",
    "canonical_event_id",
    "pdb_id",
    "ligand_component_id",
    "raw_structure_available",
    "exact_cys_sg_event_recovered",
    "explicit_covalent_evidence",
    "distance_only_event_inference_used",
    "full_coordinate_post_evidence_available",
    "ccd_graph_complete",
    "feature_compatible",
    "structural_processing_success",
    "post_geometry_source_evidence_available",
    "representation_gap",
    "feature_incompatible",
    "current_global_status",
    "priority_review_in_scope",
    "review_unit_id",
    "current_review_status",
    "human_review_completed",
    "human_review_authority_source",
    "chemistry_disposition",
    "chemistry_authority_source",
    "task_relevance_disposition",
    "task_relevance_authority_source",
    "training_use_disposition",
    "human_training_excluded",
    "reactive_pair_raw_structural_evidence",
    "reactive_pair_sample_authoritative",
    "reactive_pair_training_target_available",
    "role_partition_sample_authoritative",
    "role_profile",
    "canonical_mask_structural_labels_available",
    "structurally_applicable_task_ids_json",
    "post_geometry_sample_authoritative",
    "post_geometry_training_target_available",
    "pre_geometry_authoritative",
    "pre_geometry_training_target_available",
    "training_use_include",
    "future_training_admission_candidate",
    "formal_split_authoritative",
    "formal_split",
    "formal_training_admitted",
    "current_runtime_model_usable",
    "training_materialization_allowed_current_source",
    "positive_authority_source",
    "feature_semantics_status",
)

_EXPECTED_CANONICAL_TASKS = (
    (0, "warhead_only", "A", 112),
    (1, "linker_plus_warhead", "B", 52),
    (2, "scaffold_plus_warhead", "B2", 52),
    (3, "scaffold_only", "B3", 112),
    (4, "scaffold_plus_linker_plus_warhead", "C", 112),
)

_EXPECTED_SUMMARY_VALUES = (
    (("schema_version",), "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"),
    (("universe", "event_count"), 1000),
    (("chemistry", "POSITIVE", "count"), 112),
    (("task_relevance", "RELEVANT", "count"), 113),
    (("training_use", "INCLUDE", "count"), 44),
    (("training_use", "EXCLUDE_FROM_TRAINING_ONLY", "count"), 68),
    (("training_stage", "future_training_admission_candidate_count"), 27),
    (("reactive_pair", "sample_level_authoritative_pair_count"), 112),
    (("role", "role_partition_sample_authoritative_count"), 112),
    (("human_review", "completed_positive_event_count"), 95),
    (("human_review", "completed_positive_unit_count"), 13),
    (("human_review", "completed_negative_event_count"), 24),
    (("human_review", "completed_negative_unit_count"), 4),
    (("human_review", "completed_event_count"), 119),
    (("human_review", "completed_unit_count"), 17),
    (("human_review", "unreviewed_event_count"), 219),
    (("human_review", "unreviewed_unit_count"), 114),
    (("human_review", "pending_event_count"), 219),
    (("human_review", "current_pending_review_unit_count"), 114),
    (("training_stage", "formal_training_admitted_count"), 5),
    (("training_stage", "current_runtime_model_usable_count"), 17),
    (("geometry", "POST_source_evidence_available_count"), 867),
    (("geometry", "POST_sample_authoritative_count"), 21),
    (("geometry", "POST_training_target_available_count"), 17),
    (("geometry", "PRE_source_evidence_available_count"), 0),
    (("geometry", "PRE_sample_authoritative_count"), 0),
    (("geometry", "PRE_training_target_available_count"), 0),
    (("geometry", "POST_to_PRE_promotion_performed"), False),
    (("geometry", "PRE_zero_fill_performed"), False),
    (("geometry", "PRE_is_v1_hard_requirement"), False),
    (("canonical_exact5", "task_count"), 5),
    (("canonical_exact5", "B3_present"), True),
    (("canonical_exact5", "sixth_task_present"), False),
    (("authority_boundary", "I12_REVIEW_STARTED"), False),
    (("authority_boundary", "training_admission_created"), False),
    (("authority_boundary", "training_started"), False),
    (("authority_boundary", "training_performed"), False),
    (("authority_boundary", "READY_FOR_TRAINING"), False),
    (("authority_boundary", "feature_semantics_audit_performed"), False),
)


class SourceBindingActiveConsumerIntegrationV2Error(ValueError):
    """Raised when the published active-consumer integration fails closed."""


def _fail(reason: str) -> NoReturn:
    raise SourceBindingActiveConsumerIntegrationV2Error(
        f"{_ERROR_PREFIX}:{reason}"
    )


def _bind_source(
    *, repo_root: Path, spec: tuple[str, Path, int, str]
) -> bytes:
    label, relative, byte_count, sha256 = spec
    try:
        return source_binding_v2.verify_bound_source_v2(
            path=repo_root / relative,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=False,
        )
    except source_binding_v2.SourceBindingPolicyV2Error as error:
        raise SourceBindingActiveConsumerIntegrationV2Error(
            f"{_ERROR_PREFIX}:BOUND_SOURCE_REJECTED:{label}"
        ) from error


def _bind_all_published_sources(repo_root: Path) -> dict[str, bytes]:
    _bind_source(repo_root=repo_root, spec=_SOURCE_BINDING_POLICY_SPEC)
    for (
        consumer,
        owner_path,
        owner_bytes,
        owner_sha256,
        checker_path,
        checker_bytes,
        checker_sha256,
        _published_commit,
    ) in _ACTIVE_CONSUMER_SPECS:
        _bind_source(
            repo_root=repo_root,
            spec=(
                f"{consumer}_V2_OWNER",
                owner_path,
                owner_bytes,
                owner_sha256,
            ),
        )
        _bind_source(
            repo_root=repo_root,
            spec=(
                f"{consumer}_V2_CHECKER",
                checker_path,
                checker_bytes,
                checker_sha256,
            ),
        )
    return {
        label: _bind_source(repo_root=repo_root, spec=spec)
        for label, *rest in _CURRENT_CENSUS_SPECS
        for spec in ((label, *rest),)
    }


def _project_yun_v2(*, repo_root: Path) -> dict[str, bytes]:
    return yun_v2.verify_published_yun_v1_projection_v2(repo_root=repo_root)


def _project_neq_v2(*, repo_root: Path) -> dict[str, bytes]:
    return neq_v2.verify_published_neq_v1_projection_v2(repo_root=repo_root)


def _project_cht_v2(*, repo_root: Path) -> dict[str, bytes]:
    return cht_v2.verify_published_cht_v1_projection_v2(repo_root=repo_root)


def _project_ozj_v2(*, repo_root: Path) -> dict[str, bytes]:
    return ozj_v2.verify_published_ozj_v1_projection_v2(repo_root=repo_root)


def _project_f24_v2(*, repo_root: Path) -> dict[str, bytes]:
    return f24_v2.verify_published_f24_v1_projection_v2(repo_root=repo_root)


def _project_two_a2_v2(*, repo_root: Path) -> dict[str, bytes]:
    return two_a2_v2.verify_published_two_a2_v1_projection_v2(
        repo_root=repo_root
    )


def _verify_projection_digests(
    projections: tuple[tuple[str, Mapping[str, bytes]], ...],
) -> dict[str, object]:
    if tuple(consumer for consumer, _artifacts in projections) != tuple(
        consumer for consumer, _specs in _PUBLISHED_V1_PROJECTION_SPECS
    ):
        _fail("ACTIVE_CONSUMER_ORDER_INVALID")
    result: dict[str, object] = {}
    artifact_count = 0
    for (consumer, artifacts), (expected_consumer, specs) in zip(
        projections, _PUBLISHED_V1_PROJECTION_SPECS, strict=True
    ):
        if consumer != expected_consumer:
            _fail("PROJECTION_CONSUMER_MISMATCH")
        if tuple(artifacts) != tuple(filename for filename, _size, _sha in specs):
            _fail(f"{consumer}_V1_ARTIFACT_INVENTORY_MISMATCH")
        consumer_result: dict[str, object] = {}
        for filename, expected_size, expected_sha256 in specs:
            payload = artifacts[filename]
            if not isinstance(payload, bytes):
                _fail(f"{consumer}_V1_ARTIFACT_NOT_BYTES:{filename}")
            if len(payload) != expected_size:
                _fail(f"{consumer}_V1_ARTIFACT_BYTE_COUNT_MISMATCH:{filename}")
            digest = hashlib.sha256(payload).hexdigest()
            if digest != expected_sha256:
                _fail(f"{consumer}_V1_ARTIFACT_SHA256_MISMATCH:{filename}")
            consumer_result[filename] = {
                "byte_count": expected_size,
                "sha256": digest,
            }
            artifact_count += 1
        result[consumer] = consumer_result
    if artifact_count != 24:
        _fail("ARTIFACT_PROJECTION_COUNT_INVALID")
    return result


def _json_document(payload: bytes, label: str) -> dict[str, object]:
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceBindingActiveConsumerIntegrationV2Error(
            f"{_ERROR_PREFIX}:{label}_JSON_INVALID"
        ) from error
    if not isinstance(document, dict):
        _fail(f"{label}_DOCUMENT_TYPE_INVALID")
    return document


def _value_at(document: Mapping[str, object], path: tuple[str, ...]) -> object:
    value: object = document
    for key in path:
        if not isinstance(value, dict) or key not in value:
            _fail(f"SUMMARY_FIELD_MISSING:{'.'.join(path)}")
        value = value[key]
    return value


def _verify_summary(summary: Mapping[str, object]) -> None:
    for path, expected in _EXPECTED_SUMMARY_VALUES:
        actual = _value_at(summary, path)
        if type(actual) is not type(expected) or actual != expected:
            _fail(f"SUMMARY_FIELD_VALUE_INVALID:{'.'.join(path)}")
    tasks = _value_at(summary, ("canonical_exact5", "tasks"))
    if not isinstance(tasks, list) or len(tasks) != 5:
        _fail("CANONICAL_TASK_INVENTORY_INVALID")
    for record, (task_id, semantic_name, display_alias, count) in zip(
        tasks, _EXPECTED_CANONICAL_TASKS, strict=True
    ):
        expected = {
            "display_alias": display_alias,
            "semantic_name": semantic_name,
            "structurally_applicable_authoritative_role_count": count,
            "task_id": task_id,
        }
        if record != expected:
            _fail(f"CANONICAL_TASK_INVALID:{semantic_name}")


def _count(rows: tuple[dict[str, str], ...], field: str, value: str) -> int:
    return sum(row[field] == value for row in rows)


def _verify_census_rows(
    rows: tuple[dict[str, str], ...],
    *,
    pre_source_evidence_available_count: int,
) -> dict[str, object]:
    if len(rows) != 1000:
        _fail("CURRENT_CENSUS_ROW_COUNT_INVALID")
    boolean_fields = (
        "future_training_admission_candidate",
        "reactive_pair_sample_authoritative",
        "role_partition_sample_authoritative",
        "formal_training_admitted",
        "current_runtime_model_usable",
        "post_geometry_source_evidence_available",
        "post_geometry_sample_authoritative",
        "post_geometry_training_target_available",
        "pre_geometry_authoritative",
        "pre_geometry_training_target_available",
    )
    if any(
        {row[field] for row in rows} - {"true", "false"}
        for field in boolean_fields
    ):
        _fail("CURRENT_CENSUS_BOOLEAN_DOMAIN_INVALID")

    counts = {
        "positive": _count(rows, "chemistry_disposition", "POSITIVE"),
        "relevant": _count(rows, "task_relevance_disposition", "RELEVANT"),
        "INCLUDE": _count(rows, "training_use_disposition", "INCLUDE"),
        "EXCLUDE_FROM_TRAINING_ONLY": _count(
            rows,
            "training_use_disposition",
            "EXCLUDE_FROM_TRAINING_ONLY",
        ),
        "future_training_admission_candidate": _count(
            rows, "future_training_admission_candidate", "true"
        ),
        "sample_level_pair_authority": _count(
            rows, "reactive_pair_sample_authoritative", "true"
        ),
        "sample_level_role_authority": _count(
            rows, "role_partition_sample_authoritative", "true"
        ),
    }
    expected_counts = {
        "positive": 112,
        "relevant": 113,
        "INCLUDE": 44,
        "EXCLUDE_FROM_TRAINING_ONLY": 68,
        "future_training_admission_candidate": 27,
        "sample_level_pair_authority": 112,
        "sample_level_role_authority": 112,
    }
    if counts != expected_counts:
        _fail("CURRENT_CENSUS_GLOBAL_COUNTS_INVALID")

    task_counts = {task_id: 0 for task_id, *_rest in _EXPECTED_CANONICAL_TASKS}
    for row in rows:
        try:
            task_ids = json.loads(row["structurally_applicable_task_ids_json"])
        except json.JSONDecodeError as error:
            raise SourceBindingActiveConsumerIntegrationV2Error(
                f"{_ERROR_PREFIX}:CURRENT_CENSUS_TASK_IDS_JSON_INVALID"
            ) from error
        if task_ids is None:
            continue
        if (
            not isinstance(task_ids, list)
            or any(type(task_id) is not int for task_id in task_ids)
            or len(task_ids) != len(set(task_ids))
            or any(task_id not in task_counts for task_id in task_ids)
        ):
            _fail("CURRENT_CENSUS_TASK_IDS_INVALID")
        for task_id in task_ids:
            task_counts[task_id] += 1
    expected_task_counts = {
        task_id: count
        for task_id, _semantic_name, _display_alias, count in _EXPECTED_CANONICAL_TASKS
    }
    if task_counts != expected_task_counts:
        _fail("CURRENT_CENSUS_CANONICAL_TASK_COUNTS_INVALID")

    completed_positive = tuple(
        row
        for row in rows
        if row["priority_review_in_scope"] == "true"
        and row["human_review_completed"] == "true"
        and row["chemistry_disposition"] == "POSITIVE"
    )
    completed_negative = tuple(
        row
        for row in rows
        if row["priority_review_in_scope"] == "true"
        and row["human_review_completed"] == "true"
        and row["chemistry_disposition"] == "NOT_ESTABLISHED"
    )
    pending = tuple(
        row for row in rows if row["current_global_status"] == "CURRENTLY_UNREVIEWED"
    )
    human_review = {
        "completed_positive_event_count": len(completed_positive),
        "completed_positive_unit_count": len(
            {row["review_unit_id"] for row in completed_positive}
        ),
        "completed_negative_event_count": len(completed_negative),
        "completed_negative_unit_count": len(
            {row["review_unit_id"] for row in completed_negative}
        ),
        "completed_event_count": len(completed_positive) + len(completed_negative),
        "completed_unit_count": len(
            {
                row["review_unit_id"]
                for row in (*completed_positive, *completed_negative)
            }
        ),
        "unreviewed_event_count": len(pending),
        "unreviewed_unit_count": len({row["review_unit_id"] for row in pending}),
    }
    if human_review != {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_event_count": 119,
        "completed_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
    }:
        _fail("CURRENT_CENSUS_HUMAN_REVIEW_COUNTS_INVALID")

    training_runtime = {
        "formal_training_admitted_count": _count(
            rows, "formal_training_admitted", "true"
        ),
        "current_runtime_model_usable_count": _count(
            rows, "current_runtime_model_usable", "true"
        ),
    }
    if training_runtime != {
        "formal_training_admitted_count": 5,
        "current_runtime_model_usable_count": 17,
    }:
        _fail("CURRENT_CENSUS_TRAINING_RUNTIME_COUNTS_INVALID")

    geometry = {
        "POST_source_evidence_available_count": _count(
            rows, "post_geometry_source_evidence_available", "true"
        ),
        "POST_sample_authoritative_count": _count(
            rows, "post_geometry_sample_authoritative", "true"
        ),
        "POST_training_target_available_count": _count(
            rows, "post_geometry_training_target_available", "true"
        ),
        "PRE_source_evidence_available_count": pre_source_evidence_available_count,
        "PRE_sample_authoritative_count": _count(
            rows, "pre_geometry_authoritative", "true"
        ),
        "PRE_training_target_available_count": _count(
            rows, "pre_geometry_training_target_available", "true"
        ),
    }
    if geometry != {
        "POST_source_evidence_available_count": 867,
        "POST_sample_authoritative_count": 21,
        "POST_training_target_available_count": 17,
        "PRE_source_evidence_available_count": 0,
        "PRE_sample_authoritative_count": 0,
        "PRE_training_target_available_count": 0,
    }:
        _fail("CURRENT_CENSUS_GEOMETRY_COUNTS_INVALID")

    canonical_tasks = {
        semantic_name: {
            "display_alias": display_alias,
            "structurally_applicable_authoritative_role_count": task_counts[
                task_id
            ],
        }
        for task_id, semantic_name, display_alias, _count_value in _EXPECTED_CANONICAL_TASKS
    }
    return {
        "global_counts": counts,
        "canonical_tasks": canonical_tasks,
        "human_review_counts": human_review,
        "training_runtime_counts": training_runtime,
        "geometry_counts": geometry,
    }


def _verify_census_manifest(manifest: Mapping[str, object]) -> None:
    csv_path = _CURRENT_CENSUS_SPECS[0][1].as_posix()
    summary_path = _CURRENT_CENSUS_SPECS[1][1].as_posix()
    manifest_path = _CURRENT_CENSUS_SPECS[2][1].as_posix()
    expected_inventory = {
        "exact_output_count": 3,
        "paths": [csv_path, summary_path, manifest_path],
    }
    if manifest.get("output_inventory") != expected_inventory:
        _fail("CURRENT_CENSUS_MANIFEST_INVENTORY_INVALID")
    expected_bindings = [
        {
            "artifact_role": "REFRESHED_CENSUS_CSV",
            "byte_count": _CURRENT_CENSUS_SPECS[0][2],
            "path": csv_path,
            "sha256": _CURRENT_CENSUS_SPECS[0][3],
        },
        {
            "artifact_role": "REFRESHED_SUMMARY_JSON",
            "byte_count": _CURRENT_CENSUS_SPECS[1][2],
            "path": summary_path,
            "sha256": _CURRENT_CENSUS_SPECS[1][3],
        },
    ]
    if manifest.get("output_bindings_excluding_manifest_self") != expected_bindings:
        _fail("CURRENT_CENSUS_MANIFEST_OUTPUT_BINDINGS_INVALID")
    self_binding = manifest.get("manifest_self_binding")
    if self_binding != {
        "path": manifest_path,
        "policy": "MANIFEST_SELF_SHA256_PROHIBITED",
        "sha256_recorded_inside_self": False,
    }:
        _fail("CURRENT_CENSUS_MANIFEST_SELF_BINDING_INVALID")


def _verify_current_census(bound: Mapping[str, bytes]) -> dict[str, object]:
    summary = _json_document(bound["CURRENT_2A2_CENSUS_SUMMARY"], "SUMMARY")
    manifest = _json_document(bound["CURRENT_2A2_CENSUS_MANIFEST"], "MANIFEST")
    _verify_summary(summary)
    _verify_census_manifest(manifest)
    try:
        text = bound["CURRENT_2A2_CENSUS_CSV"].decode("utf-8")
    except UnicodeDecodeError as error:
        raise SourceBindingActiveConsumerIntegrationV2Error(
            f"{_ERROR_PREFIX}:CURRENT_CENSUS_UTF8_INVALID"
        ) from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != _CURRENT_CENSUS_HEADER:
        _fail("CURRENT_CENSUS_HEADER_INVALID")
    pre_source_evidence_available_count = _value_at(
        summary, ("geometry", "PRE_source_evidence_available_count")
    )
    if type(pre_source_evidence_available_count) is not int:
        _fail("PRE_SOURCE_EVIDENCE_SUMMARY_TYPE_INVALID")
    return _verify_census_rows(
        tuple(reader),
        pre_source_evidence_available_count=pre_source_evidence_available_count,
    )


def verify_covapie_source_binding_active_consumer_integration_v2(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Verify the published V2 acceptance layer without changing V1 science."""

    if not isinstance(repo_root, Path):
        _fail("REPO_ROOT_TYPE_INVALID")
    repo_root = repo_root.resolve()

    bound_census = _bind_all_published_sources(repo_root)
    try:
        projections = (
            ("YUN", _project_yun_v2(repo_root=repo_root)),
            ("NEQ", _project_neq_v2(repo_root=repo_root)),
            ("CHT", _project_cht_v2(repo_root=repo_root)),
            ("OZJ", _project_ozj_v2(repo_root=repo_root)),
            ("F24", _project_f24_v2(repo_root=repo_root)),
            ("2A2", _project_two_a2_v2(repo_root=repo_root)),
        )
    except ValueError as error:
        raise SourceBindingActiveConsumerIntegrationV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_V2_PROJECTION_REJECTED"
        ) from error
    projection_digests = _verify_projection_digests(projections)
    census = _verify_current_census(bound_census)

    return {
        "schema_version": "covapie_source_binding_active_consumer_integration_v2",
        "filesystem_source_acceptance_authority": "SOURCE_BINDING_POLICY_V2",
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "active_consumer_order": ["YUN", "NEQ", "CHT", "OZJ", "F24", "2A2"],
        "active_consumer_count": 6,
        "per_consumer_projection_digests": projection_digests,
        "artifact_projection_count": 24,
        "current_global_counts": census["global_counts"],
        "current_canonical_tasks": census["canonical_tasks"],
        "current_human_review_counts": census["human_review_counts"],
        "current_training_runtime_counts": census["training_runtime_counts"],
        "current_geometry_counts": census["geometry_counts"],
        "all_V2_successor_sources_bound": True,
        "all_V2_projections_executed": True,
        "all_V1_scientific_projections_preserved": True,
        "current_2A2_census_bound": True,
        "current_2A2_census_unchanged": True,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "scientific_authority_reinterpreted": False,
        "global_census_refreshed": False,
        "reconciliation_executed": False,
        "training_admission_created": False,
        "data_materialized": False,
        "v2_migration_phase_b2_effective_state_integrated": True,
        "ready_for_v2_migration_phase_b3_historical_immutability_proof": True,
        "ready_for_training": False,
    }
