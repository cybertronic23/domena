# Architecture

[简体中文](architecture.zh-CN.md)

## Current intent

Domena is a Python-native data plane. Its first deliverable is a local, CPU-only path from a mock source to a validated, serialised dataset that can be read and inspected. The architecture must make that path useful without coupling the core to the mock source.

```text
Source / Adapter Layer
          ↓
Experience Layer
          ↓
Validation, Quality, and Annotation (Data Plane)
          ↓
Dataset / Storage Layer
          ↓
Training and Evaluation Consumers
          ↓
Failure Analysis and Collection Feedback
```

### Source / adapter layer

Sources include simulators, real robots, and teleoperation systems. An adapter owns source-specific lifecycle, terminology, payload decoding, clock semantics, and conversion into Domena-owned boundary contracts. The core must not import or expose ManiSkill, SAPIEN, Isaac Sim, MuJoCo, Gazebo, or a robot SDK.

### Experience layer

Experience is the first-class domain concept for interaction-derived information. It guides the vocabulary and invariants of the system; it is not yet a commitment to a single persisted `Experience` object. The v0.1 data boundary remains to be decided in the experience-schema specification.

### Data plane

The Python data plane validates, normalises only where a generic invariant requires it, transforms data, and creates datasets. It includes distinct extension points for quality assessment and annotation. It must preserve enough provenance to trace data back to a source without making source internals part of the common model.

### Quality and annotation

Structural validation answers whether data is well-formed; data quality answers whether it is fit for a declared use; annotation adds human- or machine-produced semantic information. These are separate, versioned assets linked to experience and datasets. They must support review and provenance, but neither a labelling UI nor an automated labeller belongs in the first milestone.

### Dataset and storage layer

Dataset construction and storage are separate concerns. Storage representations optimise durability and reading; they may evolve independently from domain-facing contracts. No storage engine is selected in this phase.

### Consumers

Training and evaluation consume datasets through stable reading and inspection interfaces. Evaluation produces versioned results and failure evidence that can be associated with datasets, model/policy versions, tasks, and source conditions. Consumers are downstream dependencies, not core dependencies.

### Feedback loop

Failure analysis turns evaluation evidence and collection/quality issues into recommendations for targeted collection, curation, annotation, or quality rules. This closes the loop without requiring Domena v0.1 to own training, deployment, or a scheduler.

## Dependency direction

Core domain contracts sit at the centre. Validation, processing, storage, and adapters may depend on them. Concrete adapters and backends must not be imported by the core. Application-level composition is responsible for wiring implementations together.

## Deliberately absent

There is currently no Go service, web UI, database requirement, scheduler, distributed runtime, authentication system, or cloud deployment topology. A future Go control plane may manage registries, jobs, metadata, or APIs, but it is outside the first milestones and must communicate with—not replace—the Python data plane.

## Decisions to revisit

- The versioning and compatibility policy for schemas and datasets.
- The canonical storage representation and media-asset layout.
- Whether a durable episode is the v0.1 interchange unit.
- The minimum provenance and time model needed across sources.
- The identity and versioning model for annotations, quality reports, evaluations, and failure cases.
