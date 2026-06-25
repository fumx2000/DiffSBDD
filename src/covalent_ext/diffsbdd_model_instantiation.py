from __future__ import annotations

import importlib
import inspect
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MODEL_MODULE_NAME = "lightning_modules"
MODEL_CLASS_NAME = "LigandPocketDDPM"
CONFIG_SOURCE = "configs/crossdock_fullatom_cond.yml"
DATASET_INFO_SOURCE = "constants.dataset_params['crossdock_full']"
ATOM_ENCODER_SOURCE = "constants.dataset_params['crossdock_full']['atom_encoder']"
INSPECTED_SOURCE_FILES = [
    "lightning_modules.py",
    "equivariant_diffusion/en_diffusion.py",
    "equivariant_diffusion/dynamics.py",
    "equivariant_diffusion/conditional_model.py",
    "train.py",
    "generate_ligands.py",
    "optimize.py",
    "configs/crossdock_fullatom_cond.yml",
    "configs/crossdock_fullatom_joint.yml",
    "process_crossdock.py",
    "constants.py",
    "scripts/covalent_inpaint_demo.py",
]


def _source_files_present() -> list[str]:
    present = []
    for relative in INSPECTED_SOURCE_FILES:
        path = REPO_ROOT / relative
        if path.is_file():
            path.read_text(encoding="utf-8", errors="replace")
            present.append(relative)
    return present


def _namespace(value: dict[str, Any]) -> Namespace:
    return Namespace(**value)


def _load_yaml_config() -> dict[str, Any]:
    path = REPO_ROOT / CONFIG_SOURCE
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def inspect_diffsbdd_model_constructor_v0() -> dict[str, Any]:
    module = importlib.import_module(MODEL_MODULE_NAME)
    model_class = getattr(module, MODEL_CLASS_NAME)
    signature = inspect.signature(model_class.__init__)
    required = []
    optional = []
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
        else:
            optional.append(name)
    return {
        "model_class_name": MODEL_CLASS_NAME,
        "module_name": MODEL_MODULE_NAME,
        "constructor_signature": str(signature),
        "required_constructor_args": required,
        "optional_constructor_args": optional,
        "inspected_source_files": _source_files_present(),
        "detected_config_sources": [
            "train.py YAML merge path",
            CONFIG_SOURCE,
            "configs/crossdock_fullatom_joint.yml",
        ],
        "detected_dataset_info_sources": [
            "constants.dataset_params",
            DATASET_INFO_SOURCE,
            "process_crossdock.py full-atom branch",
        ],
        "notes": [
            "train.py constructs LigandPocketDDPM from YAML config plus a node histogram file.",
            "process_crossdock.py uses constants.dataset_params['crossdock_full'] for full-atom processed data.",
            "This dry-run inspects the constructor only and does not call model forward paths.",
        ],
    }


def build_minimal_diffsbdd_instantiation_config_v0() -> dict[str, Any]:
    blocking_reasons: list[str] = []
    missing_or_uncertain = [
        "repository does not include the original processed size_distribution.npy; dry-run uses a minimal positive 2x2 histogram for constructor-only initialization",
        "configs/crossdock_fullatom_cond.yml names dataset as crossdock while process_crossdock.py full-atom branch uses constants.dataset_params['crossdock_full']; dry-run uses crossdock_full to match 11-dimensional full-atom fields",
        "configs/crossdock_fullatom_cond.yml does not explicitly set virtual_nodes; dry-run uses the constructor default false",
    ]
    try:
        config = _load_yaml_config()
    except Exception as exc:  # pragma: no cover - exercised through blocked path if config disappears
        return {
            "config_status": "blocked",
            "config_source": CONFIG_SOURCE,
            "model_class_name": MODEL_CLASS_NAME,
            "dataset_info_source": DATASET_INFO_SOURCE,
            "atom_encoder_source": ATOM_ENCODER_SOURCE,
            "config_dict": {},
            "missing_or_uncertain_config_fields": missing_or_uncertain,
            "blocking_reasons": [f"config_load_failed:{type(exc).__name__}:{exc}"],
        }
    required_top = [
        "mode",
        "pocket_representation",
        "batch_size",
        "lr",
        "egnn_params",
        "diffusion_params",
        "eval_params",
        "loss_params",
        "eval_epochs",
        "visualize_sample_epoch",
        "visualize_chain_epoch",
        "auxiliary_loss",
        "num_workers",
        "augment_noise",
        "augment_rotation",
        "clip_grad",
    ]
    missing_top = [key for key in required_top if key not in config]
    if missing_top:
        blocking_reasons.append(f"missing_config_keys:{','.join(missing_top)}")
    try:
        constants = importlib.import_module("constants")
        dataset_info = constants.dataset_params["crossdock_full"]
    except Exception as exc:
        dataset_info = None
        blocking_reasons.append(f"dataset_info_unavailable:{type(exc).__name__}:{exc}")
    if dataset_info is not None and len(dataset_info["atom_encoder"]) != 11:
        blocking_reasons.append("crossdock_full_atom_encoder_dim_not_11")
    config_dict = {
        "outdir": "data/derived/covalent_small/training_tensor_materialized_v0/diffsbdd_model_instantiation_dry_run_no_outputs",
        "dataset": "crossdock_full",
        "datadir": "data/derived/covalent_small/training_tensor_materialized_v0/no_training_data_dir_used",
        "batch_size": 3,
        "lr": float(config.get("lr", 1.0e-3)),
        "egnn_params": dict(config.get("egnn_params", {}), device="cpu"),
        "diffusion_params": dict(config.get("diffusion_params", {})),
        "num_workers": 0,
        "augment_noise": 0,
        "augment_rotation": False,
        "clip_grad": False,
        "eval_epochs": int(config.get("eval_epochs", 50)),
        "eval_params": dict(config.get("eval_params", {}), smiles_file=None),
        "visualize_sample_epoch": int(config.get("visualize_sample_epoch", 50)),
        "visualize_chain_epoch": int(config.get("visualize_chain_epoch", 50)),
        "auxiliary_loss": False,
        "loss_params": dict(config.get("loss_params", {})),
        "mode": config.get("mode", "pocket_conditioning"),
        "node_histogram": [[1.0, 1.0], [1.0, 1.0]],
        "pocket_representation": config.get("pocket_representation", "full-atom"),
        "virtual_nodes": False,
    }
    if config_dict["mode"] != "pocket_conditioning":
        blocking_reasons.append("config_mode_not_pocket_conditioning")
    if config_dict["pocket_representation"] != "full-atom":
        blocking_reasons.append("config_pocket_representation_not_full_atom")
    for key in [
        "joint_nf",
        "hidden_nf",
        "n_layers",
        "attention",
        "tanh",
        "norm_constant",
        "inv_sublayers",
        "sin_embedding",
        "aggregation_method",
        "normalization_factor",
        "reflection_equivariant",
    ]:
        if key not in config_dict["egnn_params"]:
            blocking_reasons.append(f"missing_egnn_param:{key}")
    for key in [
        "diffusion_steps",
        "diffusion_noise_schedule",
        "diffusion_noise_precision",
        "diffusion_loss_type",
        "normalize_factors",
    ]:
        if key not in config_dict["diffusion_params"]:
            blocking_reasons.append(f"missing_diffusion_param:{key}")
    return {
        "config_status": "ready" if not blocking_reasons else "blocked",
        "config_source": CONFIG_SOURCE,
        "model_class_name": MODEL_CLASS_NAME,
        "dataset_info_source": DATASET_INFO_SOURCE,
        "atom_encoder_source": ATOM_ENCODER_SOURCE,
        "config_dict": config_dict,
        "missing_or_uncertain_config_fields": missing_or_uncertain,
        "blocking_reasons": blocking_reasons,
    }


def _constructor_kwargs(config_dict: dict[str, Any]) -> dict[str, Any]:
    return {
        "outdir": Path(config_dict["outdir"]),
        "dataset": config_dict["dataset"],
        "datadir": config_dict["datadir"],
        "batch_size": config_dict["batch_size"],
        "lr": config_dict["lr"],
        "egnn_params": _namespace(config_dict["egnn_params"]),
        "diffusion_params": _namespace(config_dict["diffusion_params"]),
        "num_workers": config_dict["num_workers"],
        "augment_noise": config_dict["augment_noise"],
        "augment_rotation": config_dict["augment_rotation"],
        "clip_grad": config_dict["clip_grad"],
        "eval_epochs": config_dict["eval_epochs"],
        "eval_params": _namespace(config_dict["eval_params"]),
        "visualize_sample_epoch": config_dict["visualize_sample_epoch"],
        "visualize_chain_epoch": config_dict["visualize_chain_epoch"],
        "auxiliary_loss": config_dict["auxiliary_loss"],
        "loss_params": _namespace(config_dict["loss_params"]),
        "mode": config_dict["mode"],
        "node_histogram": config_dict["node_histogram"],
        "pocket_representation": config_dict["pocket_representation"],
        "virtual_nodes": config_dict["virtual_nodes"],
    }


def try_instantiate_diffsbdd_model_without_checkpoint_v0(device: str = "cpu") -> dict[str, Any]:
    inspection = inspect_diffsbdd_model_constructor_v0()
    config = build_minimal_diffsbdd_instantiation_config_v0()
    result: dict[str, Any] = {
        "device": device,
        "model_class_imported": False,
        "constructor_signature_resolved": bool(inspection.get("constructor_signature")),
        "config_status": config["config_status"],
        "config_source": config["config_source"],
        "dataset_info_source": config["dataset_info_source"],
        "atom_encoder_source": config["atom_encoder_source"],
        "model_initialized": False,
        "model_class_name": config["model_class_name"],
        "parameter_count": 0,
        "trainable_parameter_count": 0,
        "module_count": 0,
        "instantiation_exception_type": "",
        "instantiation_exception_message": "",
        "checkpoint_loaded": False,
        "checkpoint_saved": False,
        "forward_called": False,
        "diffsbdd_model_called": False,
        "training_step_called": False,
        "training_executed": False,
        "smoke_status": "blocked",
        "blocking_reasons": list(config["blocking_reasons"]),
        "missing_or_uncertain_config_fields": list(config["missing_or_uncertain_config_fields"]),
    }
    if config["config_status"] != "ready":
        if not result["blocking_reasons"]:
            result["blocking_reasons"].append("config_not_ready")
        return result
    try:
        module = importlib.import_module(MODEL_MODULE_NAME)
        model_class = getattr(module, MODEL_CLASS_NAME)
        result["model_class_imported"] = True
        model = model_class(**_constructor_kwargs(config["config_dict"]))
        model = model.to(device)
        model.eval()
        result["model_initialized"] = True
        result["parameter_count"] = int(sum(parameter.numel() for parameter in model.parameters()))
        result["trainable_parameter_count"] = int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad))
        result["module_count"] = int(len(list(model.modules())))
    except Exception as exc:  # pragma: no cover - tested via safe blocked contract if environment changes
        result["instantiation_exception_type"] = type(exc).__name__
        result["instantiation_exception_message"] = str(exc)
        result["blocking_reasons"].append(f"instantiation_failed:{type(exc).__name__}")
    if (
        result["model_class_imported"]
        and result["constructor_signature_resolved"]
        and result["model_initialized"]
        and result["parameter_count"] > 0
        and result["trainable_parameter_count"] > 0
        and result["checkpoint_loaded"] is False
        and result["checkpoint_saved"] is False
        and result["forward_called"] is False
        and result["diffsbdd_model_called"] is False
        and result["training_step_called"] is False
        and result["training_executed"] is False
    ):
        result["smoke_status"] = "passed"
        result["blocking_reasons"] = []
    return result
