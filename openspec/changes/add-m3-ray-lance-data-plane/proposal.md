## Status

**Ready for implementation — Ray Data and Lance are approved as the Phase 1 execution and storage engines.**

中文版本：[proposal.zh-CN.md](proposal.zh-CN.md)

## Why

M1a/M1b/M2 can describe, version, and import embodied experience, but the project cannot yet execute a distributed transform or materialize a multi-modal training dataset. Phase 1 needs one concrete, coherent data plane rather than a collection of engine-specific scripts.

## What Changes

- Add an optional Ray Data execution integration for distributed, bounded dataset transforms.
- Add an optional Lance materialization integration for multi-modal dataset rows, immutable output references, and training-oriented scans.
- Add source-neutral job-run and materialization-reference contracts, owned by Domena rather than by Ray or Lance.
- Add a small local executor for deterministic tests and local fallback; Ray remains the only distributed engine in Phase 1, while the future Daft executor contract is fixed without adding a Daft dependency.
- Add opt-in extras `domena[ray]`, `domena[lance]`, and `domena[ray,lance]`.

## Capabilities

### New Capabilities

- `data-plane-execution`: Source-neutral bounded transform plans, job lifecycle records, and local/Ray Data execution.
- `lance-materialization`: Deterministic Lance materialization and verification of Domena dataset releases.

### Modified Capabilities

- None.

## Impact

- New public modules for execution plans/runs and Lance materialization, plus optional Ray and Lance dependencies.
- M1a `Episode`, M1b `DatasetManifest`, and M2 adapters remain source-neutral and backward compatible.
- This change does not implement Spark, Flink, or Daft; Daft only receives a fixed executor integration point, while Spark/Flink receive no implementation entry point. It also adds no cloud control plane, streaming ingestion, or mutable data catalog.
