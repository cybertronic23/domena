# Domena agent guide

## Purpose

Domena is experience data infrastructure for embodied intelligence and Physical AI. It connects data produced by simulators, real robots, and teleoperation systems to validation, dataset construction, training, evaluation, and failure analysis.

It is not a wrapper for one simulator, a robotics tutorial, a collection of scripts, or a generic big-data platform.

## Architecture principles

- Treat **experience** as the primary domain concept. Do not reduce it prematurely to a storage schema.
- Preserve the boundary between Domena core and sources. Simulator-, robot-, and teleoperation-specific concepts belong in adapters, never in the core domain.
- The data plane is Python 3.11+ with Ray Data and Lance. M4 adds the approved Go control plane and TypeScript web product; Go owns product/API orchestration and must not reimplement Python data-plane logic. Do not add Rust or another control-plane stack without an approved architecture decision.
- Add dependencies only for a present, demonstrated need. Do not pre-add distributed systems, GPU tooling, cloud services, or a specific simulator.
- Prefer small composable interfaces and standard-library types before choosing frameworks or model libraries.
- Keep domain concepts, protocols/interfaces, validation, storage representations, and adapters distinct. A persisted representation is not automatically the domain model.

## Engineering rules

- Use explicit type hints for public APIs and keep Python package boundaries clear.
- Keep imports directed inward: adapters and storage may depend on core contracts; core must not depend on a concrete source or backend.
- Write automated tests for observable behavior, edge cases, validation failures, and serialization boundaries. Tests must run locally on macOS without GPU or external services.
- Do not introduce a concrete Experience/Episode/Step implementation until the corresponding OpenSpec change specification is approved.
- Do not leak a source's terminology or payload shape into a generic API. Translate at the adapter boundary.
- Record implementation-ready architecture decisions in OpenSpec. Keep unresolved trade-offs and exploratory rationale in local `notes/` rather than exposing them as public documentation.
- Keep committed design, OpenSpec, and public documentation bilingual: maintain the English source and a corresponding `*.zh-CN.md` Chinese version, with reciprocal links near the top. Chinese is the primary reading path for this project owner.

## Change discipline

Before changing a public domain boundary, explain the compatibility impact, update the specification and architecture documents, and add focused tests. Prefer the smallest change that advances the approved milestone. Avoid speculative abstractions and keep the end-to-end local workflow runnable.
