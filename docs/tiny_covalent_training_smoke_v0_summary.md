# Tiny Covalent Training Smoke v0 Summary

This step runs a tiny toy covalent model training smoke test.
It verifies that the current covalent batch supports forward, loss, backward, gradient, and optimizer step.
It uses device=auto and prefers cuda:0 when available.
It does not use DiffSBDD.
It does not load checkpoint.
It does not save checkpoint.
It does not train or fine-tune a real model.
It does not modify DiffSBDD model code.

- requested_device: auto
- resolved_device: cuda:0
- cuda_available: True
- cuda_device_count: 1
- cuda_device_name: NVIDIA A100-SXM4-80GB

| mask_level | target_atom_count | initial_total_loss | post_step_total_loss | gradient_norm | smoke_status |
| --- | ---: | ---: | ---: | ---: | --- |
| A_warhead_only | 12 | 51.04842 | 50.514015 | 10.666517 | passed |
| B_linker_warhead | 30 | 49.799744 | 49.353333 | 8.9513638 | passed |
| B2_scaffold_warhead | 86 | 60.167923 | 59.927406 | 5.075222 | passed |
| C_scaffold_linker_warhead | 104 | 58.844738 | 58.553383 | 6.184418 | passed |

Conclusion: if all rows are passed, the next step is DiffSBDD input interface inspection or adapter.
