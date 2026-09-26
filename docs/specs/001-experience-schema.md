# Specification 001: Experience Schema v0.1

[简体中文](001-experience-schema.zh-CN.md)

**Status:** Proposed — architecture review required before implementation.

## Scope

Define the smallest source-neutral contract needed to carry a bounded interaction trajectory from a mock source through validation, local serialisation, reading, and basic inspection. The specification will decide whether that contract is an episode and will define its minimal identity, ordering, modality references/values, outcomes, provenance, and extension mechanism.

## Requirements

- Be implementable in Python 3.11+ with explicit type hints and no GPU, network service, or concrete simulator dependency.
- Preserve ordered interaction data and support optional observations, actions, state, feedback, timestamps, and metadata without requiring every modality.
- Represent or reference common multimodal values without prescribing a tensor library or storage engine.
- Keep generic concepts separate from source-specific payloads and adapters.
- Define structural validation invariants, actionable validation errors, and a path for source/task-specific validation rules.
- Define a versioned serialisation envelope and a read/write round-trip expectation without prematurely selecting a columnar, database, or media backend.
- Allow inspection to report basic trajectory and modality statistics without depending on training code.
- Carry the minimum provenance needed for later annotations, quality reports, and evaluation/failure evidence to reference the trajectory. Those assets are not part of the v0.1 trajectory payload.

## Non-goals

- A universal robotics ontology, simulator API, or real-robot protocol.
- A fixed Pydantic hierarchy for every concept or modality.
- Distributed ingestion, cloud storage, registry services, user authentication, or dataset version management.
- Training, evaluation, replay, or visualisation frameworks.
- Annotation operations, labelling UIs, automatic labellers, quality scoring systems, or evaluation runners.
- A ManiSkill adapter or any concrete source implementation beyond the later mock source.

## Domain boundaries

The schema must state which elements are domain concepts, public contracts/protocols, value objects, validation results, and storage representations. It must avoid equating an in-memory domain object with its on-disk representation. Adapter input is source-owned; the serialisation envelope is storage-owned; only the approved contract belongs to Domena core.

## API expectations

The later implementation should expose a small, source-neutral way to construct or stream a bounded trajectory, validate it, serialise it locally, read it back, and inspect it. Public APIs should accept extension data deliberately rather than leaking untyped source payloads. Concrete names and class choices are deferred until this specification is approved.

## Validation requirements

At minimum, validation must cover schema version recognition, required identifiers, ordering/uniqueness rules, time consistency where timestamps are supplied, modality reference integrity, and consistency of declared terminal/outcome data. It must identify the trajectory and location of an error. Quality thresholds and simulator/task semantics remain pluggable rules.

## Serialization requirements

The v0.1 format must be local, deterministic enough for tests, carry an explicit schema version, preserve extension data, and round-trip supported values/references without silent loss. Large binary media should not force an early storage choice; the design must specify its treatment or explicitly bound it out of the first implementation.

## Testing requirements

Tests must run locally on macOS without GPU or external services. Cover valid mock trajectories, omitted optional modalities, malformed ordering, invalid terminal signals, unsupported versions, extension preservation, and write/read round trips. Add adapter-isolation tests once a real adapter exists.

## Acceptance criteria

Architecture review approves the data boundary, minimum required fields, temporal model, extension policy, and storage envelope. A subsequent implementation can then demonstrate:

1. mock-source generation of valid sample trajectories;
2. deterministic generic validation failures for invalid samples;
3. local serialisation and read-back without loss of supported data; and
4. basic inspection/statistics over the read dataset.

## Decisions required before implementation

- Confirm episode (or an alternative) as the v0.1 durable/interchange unit.
- Select the minimal identifiers, lifecycle/terminal semantics, and temporal ordering contract.
- Select the extension and metadata namespacing policy.
- Set the v0.1 boundary for media payloads versus references.
- Choose a minimal serialisation envelope and its compatibility policy.
