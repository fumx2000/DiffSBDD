# CovaPIE Dataloader Interface QA Gate v0 Retirement

`covapie_dataloader_interface_qa_gate_v0` is retired and is no longer
executable. Its historical QA artifacts remain read-only evidence and must not
be regenerated.

The historical 35/45-field QA contract is not a canonical dataloader admission
contract. This retirement adds no schema alias, dual-schema support, QA v1
artifact, runtime dataloader, or training readiness claim. The canonical
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
