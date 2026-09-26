# Roadmap

[简体中文](roadmap.zh-CN.md)

This roadmap describes intended stages, not commitments to a fixed technology stack or delivery date.

## Phase 0 — Architecture and domain model

Document vocabulary, dependency boundaries, engineering rules, and the first schema specification. Resolve only the decisions necessary to start a small implementation.

## Phase 1 — Experience schema and mock source

Implement the approved v0.1 boundary and a CPU-only mock source that produces representative small interaction trajectories. The mock source validates Domena abstractions; it is not a simulator product.

## Phase 2 — Validation and dataset storage

Add generic validation, a local dataset serialisation and reading path, and basic inspection/statistics. Establish tests around malformed data and round trips.

## Phase 3 — First real simulator adapter

Add a ManiSkill adapter behind the established source boundary. Its installation and data conventions remain isolated from the core.

## Phase 4 — Larger-scale data processing

Evaluate batch processing, richer multimodal asset handling, dataset versioning, lineage, quality workflows, and distributed execution only when workloads demonstrate the need.

## Phase 5 — Control plane and platformisation

Consider registry, job, metadata, API, and orchestration capabilities. A Go control plane is a possible future implementation choice, subject to a separate design decision.
