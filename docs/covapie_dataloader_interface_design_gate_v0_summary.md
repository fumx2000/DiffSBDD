# CovaPIE Dataloader Interface Design Gate v0 Retirement

`covapie_dataloader_interface_design_gate_v0` is retired and is no longer
executable. Its historical artifacts remain read-only evidence and must not be
regenerated.

The historical 35/45-field interface contracts are not canonical admission
contracts. This retirement does not add `final_dataset_field_name` aliases,
dual-schema support, or a replacement dataloader implementation. The canonical
dataloader interface remains pending redesign.

- successor availability: `redesign_pending`
- successor stage: none
- successor manifest: none
- recommended next step: `covapie_final_dataset_qa_gate_v1`
- training readiness: false
- feature semantics audit required before training: true

Thirty-five transitive legacy-admission consumers remain for later staged
retirement or re-anchoring. The two independent Step14Z consumers are not
retired by this policy.
