## Status

**Ready for implementation — normative specifications and tasks are approved.**

中文版本：[proposal.zh-CN.md](proposal.zh-CN.md)

## Why

M1a defines, validates, and serializes individual source-neutral `Episode` values. Algorithm and training workflows need a second durable boundary: a reproducible answer to which episodes formed a dataset release, why they were selected, and which contract and processing evidence produced them. Without that boundary, dataset export, experiment comparison, quality review, and failure-case feedback would rely on mutable folders or ad hoc queries.

## What This Change Proposes

- Define a local-first, immutable dataset-manifest contract that enumerates episode membership explicitly.
- Record dataset identity, provenance, source episode references, selection rationale, schema compatibility, and aggregate statistics.
- Provide a minimal link model so future training, evaluation, and failure analysis can refer back to a precise dataset release and its episode members.
- Keep quality-policy execution, annotation workflows, remote registries, and training/evaluation runners outside M1b.

## Capabilities

### New Capabilities

- `dataset-manifest`: Reproducible local dataset release description and validation.
- `dataset-lineage`: Traceability from a dataset release to its source episodes and declared construction inputs.

## Impact

- This change adds a local contract and no storage backend, remote registry, source adapter, or public service API.
- If approved, it will add a new contract beside M1a's `experience-contract`; it will not alter `domena.experience/v0.1`.
- The resulting manifest must remain source-neutral and locally runnable before any ROS, simulator, cloud, or distributed integration is considered.
