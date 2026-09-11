# CovaPIE POST distance target packer V1

`pack_covapie_post_distance_targets_v1` is a small, pure in-memory adapter for
POST-only distance values. It accepts an explicit, unique event-ID order and a
mapping with exactly the same keys. Mapping insertion order is ignored; output
rows always follow `event_ids`.

Each mapping value is either a built-in Python `int`/`float` containing a
finite positive distance, or explicit `None` for an unknown POST value. Boolean
values, numeric strings, tensors, NaN, infinities, zero, negative values, and
values that overflow or underflow to a non-positive/non-finite `float32` are
rejected. Values are not clamped or normalized. Units are fixed to angstrom,
and no coordinates are read or used to recompute a distance.

The typed result contains:

- immutable `event_ids`, preserving the requested row order;
- CPU `float32` `pre_post_geometry_target_angstrom` with shape `[B, 2]`;
- CPU `bool` `pre_post_geometry_component_valid_mask` with shape `[B, 2]`;
- CPU `bool` `pre_post_geometry_component_loss_mask` with shape `[B, 2]`.

Component 0 is PRE and is always NaN/invalid/no-loss. Component 1 is POST: a
valid input number is represented as its checked `float32` value with
`valid=true`, while `None` is represented as NaN with `valid=false`. The loss
mask is always false for both components. Every call creates independent CPU
storage and does not participate in autograd.

Here, `valid` means only that a numeric value exists and satisfies this packing
format. It does not mean human approval, sample admission, task applicability,
source authority, intended-use approval, or loss authorization. This API has no
permission switch and returns no admission or authority field.

The tests use only conspicuously synthetic event IDs and synthetic values
`2.25`, `3.75`, and `None`. They pass the three packed geometry fields, converted
to the published Python-list payload form, into the real
`tensorize_covapie_current11_training_supervision_v1` with its minimal synthetic
CPU fixture. This verifies tensorizer format compatibility without mocking the
tensorizer and without executing a model, forward pass, loss, training,
checkpoint, external data, or real FFQ observation.

No real source values or training targets were materialized in this increment.
A future caller must supply values through a separately verified source binding
and must still satisfy the applicable real-target materialization, sample
admission, source, purpose, and runtime-eligibility gates. This packer does not
authorize that later integration or close the global feature-semantics/use
audit; Step12D remains only a smoke legality check.
