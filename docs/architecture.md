# Architecture

[简体中文](architecture.zh-CN.md)

## Current intent

Domena is a Python-native data plane. Its first deliverable is a local, CPU-only path from a mock source to a validated, serialised dataset that can be read and inspected. The architecture must make that path useful without coupling the core to the mock source.

```text
Source / Adapter Layer
          ↓
Experience Layer
          ↓
Validation and Processing (Data Plane)
          ↓
Dataset / Storage Layer
          ↓
Training and Evaluation Consumers
```

### Source / adapter layer

Sources include simulators, real robots, and teleoperation systems. An adapter owns source-specific lifecycle, terminology, payload decoding, clock semantics, and conversion into Domena-owned boundary contracts. The core must not import or expose ManiSkill, SAPIEN, Isaac Sim, MuJoCo, Gazebo, or a robot SDK.

### Experience layer

Experience is the first-class domain concept for interaction-derived information. It guides the vocabulary and invariants of the system; it is not yet a commitment to a single persisted `Experience` object. The v0.1 data boundary remains to be decided in the experience-schema specification.

### Data plane

The Python data plane validates, normalises only where a generic invariant requires it, transforms data, and creates datasets. It must preserve enough provenance to trace data back to a source without making source internals part of the common model.

### Dataset and storage layer

Dataset construction and storage are separate concerns. Storage representations optimise durability and reading; they may evolve independently from domain-facing contracts. No storage engine is selected in this phase.

### Consumers

Training and evaluation consume datasets through stable reading and inspection interfaces. They are downstream consumers, not dependencies of the core.

## Dependency direction

Core domain contracts sit at the centre. Validation, processing, storage, and adapters may depend on them. Concrete adapters and backends must not be imported by the core. Application-level composition is responsible for wiring implementations together.

## Deliberately absent

There is currently no Go service, web UI, database requirement, scheduler, distributed runtime, authentication system, or cloud deployment topology. A future Go control plane may manage registries, jobs, metadata, or APIs, but it is outside the first milestones and must communicate with—not replace—the Python data plane.

## Decisions to revisit

- The versioning and compatibility policy for schemas and datasets.
- The canonical storage representation and media-asset layout.
- Whether a durable episode is the v0.1 interchange unit.
- The minimum provenance and time model needed across sources.
