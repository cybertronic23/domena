## Status

**Ready for implementation — Ray Data and Lance are the approved Phase 1 backend pair.**

中文版本：[design.zh-CN.md](design.zh-CN.md)

## Context

M1a provides immutable source-neutral episodes, M1b provides immutable dataset membership and lineage, and M2 imports ROS 2 MCAP into that boundary. M3 supplies the first compute/storage data plane without making those established contracts depend on a framework.

## Goals / Non-Goals

**Goals**

- Execute bounded episode-level transforms locally and through Ray Data.
- Persist one verified materialization of an immutable dataset release in Lance.
- Keep Domena release identity, provenance, and quality evidence authoritative; Lance versions are physical output references.
- Make dependency loading optional and keep core imports usable without Ray or Lance.

**Non-Goals**

- No implementation of Daft, Spark, Flink, streaming data plane, cloud scheduler, distributed catalog, vector-search API, or training runner; this change does fix the Daft executor integration point.
- No conversion of every source modality to a decoded columnar payload in M3. Unhandled large assets remain stable asset locators.
- No use of Ray's object store as durable dataset storage.

## Decisions

### 1. Domena owns plans, runs, and materialization identity

`TransformPlan` identifies an immutable input `DatasetManifest`, a versioned deterministic transform declaration, and requested output schema. `JobRun` separately records the logical processing engine (`engine_name`) and execution substrate (`runtime_name`), plus status, input release fingerprint, transform fingerprint, timestamps, and failure evidence. This separation allows a future Daft engine to run locally or on Ray without changing the job-run contract. `MaterializationReference` binds a completed run to its Domena release fingerprint, backend name, URI, backend snapshot/version, schema fingerprint, and checksums.

The Domena release fingerprint is never derived from a Lance table version. One release may have several physical materializations later.

### 2. Ray Data is the sole Phase 1 distributed executor

`RayDataExecutor` translates a bounded plan into a Ray Data dataset and applies approved transform callables with explicit batch/resource options. It writes only to a unique staging output. A coordinator verifies output metadata and atomically records a successful Domena materialization reference; failed or cancelled jobs cannot become published materializations.

The local executor implements the same observable plan contract for unit tests and developer workflows. It is intentionally single-process and bounded.

### 3. Lance is the Phase 1 physical multi-modal lake format

`LanceMaterializer` converts a release into Arrow-compatible rows. Each row contains Domena identity/provenance fields and a source-neutral representation of steps and asset locators. Decoded scalar channels can be represented as typed Arrow values; media, point clouds, ROS payloads, and unsupported data remain explicit locators with checksums rather than silently copied or decoded.

The materializer writes a staged Lance dataset, validates row counts, release fingerprint, and schema fingerprint, then publishes its `MaterializationReference` only after success. The initial reader supports release-scoped scan and lookup by `(source_namespace_id, episode_id)`; it does not expose a generic query service.

### 4. Dependency and package boundary

`domena.core`, episode and manifest modules remain free of Ray, Lance, and PyArrow imports. Engine modules are lazy-loaded optional integrations. Public extras are `ray`, `lance`, and their combined extra. Tests requiring these extras are separately marked and skipped with a clear reason when absent; core tests stay runnable without them.

### 5. Fix a Daft executor integration point without implementing Daft

The Domena-owned plan/run/materialization contracts are deliberately not named after Ray or Lance. Core defines a minimal `BoundedExecutor` protocol: it accepts an immutable `TransformPlan` and explicit execution options, and produces an immutable `JobRun`; only verified materializations may be published. `LocalExecutor` and `RayDataExecutor` must implement it. `DaftExecutor` is reserved as the next-iteration peer implementation and may not bypass plan, fingerprint, staging, or publication validation.

This does not pre-abstract a Daft operator API: Phase 1 transform functions remain constrained by what Ray Data executes. Adding Daft requires only a plan-to-Daft-DataFrame mapping, `JobRun` status reporting, and reuse of the Lance materialization and publication boundary. Spark and Flink receive neither an implementation point nor a Phase 1 design commitment.

## Risks / Trade-offs

- [Ray and Lance installation/ABI variance on local machines] → optional extras, lazy imports, pinned compatible ranges, and integration-test markers.
- [Large assets are expensive to decode/copy] → keep locators in M3 and require explicit future format-specific materializers.
- [Partial distributed output could be mistaken for a release] → staging URI, verification, and one coordinator-controlled publication step.
- [A generic executor abstraction becomes speculative] → `BoundedExecutor` contains only plan submission, status, and result references; it does not abstract Ray/Daft operator graphs or optimizers.

## Migration Plan

1. Add contracts and local implementation with no external dependency.
2. Add optional Lance materialization and verification.
3. Add optional Ray Data execution of the same bounded plan.
4. Demonstrate a local M2 MCAP-derived manifest materialized through the M3 path; retain all existing JSON manifest workflows.

## Open Questions

- None for the Phase 1 boundary. Detailed Arrow column naming and first supported transform set are implementation decisions constrained by the normative specifications.
