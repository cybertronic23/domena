## Context

The core needs a stable interaction boundary before it can safely accept robot, simulation, or teleoperation adapters. Industry requirements show that pure files plus metadata are insufficient: algorithms need task success criteria, time alignment, physical context, actions, feedback, and failure evidence. M1a must nevertheless run locally and avoid a premature platform stack.

## Goals / Non-Goals

**Goals:** explicit immutable value objects; generic structural validation; deterministic JSON envelope; external media references; source isolation; useful inspection.

**Non-Goals:** ROS/ManiSkill integration, binary media decoding, annotation/quality scoring, datasets/manifests, training/evaluation execution, UI, cloud, scheduling, or distributed compute.

## Decisions

1. `Episode` is an immutable bounded trajectory and durable interchange unit. A list/tuple of contiguous `Step` values is sufficient for local v0.1.
2. The shared contract has `TaskContext`, `PhysicalContext`, `Outcome`, `Asset`, `AssetReference`, and JSON-compatible channel mappings. This preserves required context without modeling source internals.
3. A timestamp is optional integer nanoseconds, constrained only to be non-decreasing when supplied. Clock domains are explicit but source adapters remain responsible for conversion.
4. Large data stays external. `AssetReference` points to an episode asset registry, leaving storage selection open.
5. Contract validation returns structured path-addressable issues rather than making constructor exceptions the sole feedback mechanism.
6. JSON serialisation uses tagged asset-reference values and stable key ordering; it is a local exchange envelope, not a lakehouse format.
7. Extension keys must contain `:`. This provides a visible ownership boundary without a source-specific type hierarchy.

## Risks / Trade-offs

- JSON-compatible channels are intentionally broad. Typed modality schemas are deferred until a real adapter demonstrates a shared need.
- A non-decreasing timestamp rule permits equal times; strict sampling/cross-sensor synchronisation is source- and task-specific.
- URI references offer portability but do not guarantee asset availability. Checksum and storage-policy enforcement belongs to later quality/storage work.

## Migration Plan

There is no previous implementation. Future adapters map their source payloads to this boundary; incompatibilities require a new schema version rather than silently changing `v0.1`.

## Open Questions

- Whether the first production adapter should be ROS bag or ManiSkill.
- Manifest identity and episode-selection semantics for M1b.
