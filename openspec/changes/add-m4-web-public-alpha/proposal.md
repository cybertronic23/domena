## Status

**Approved — M3.5 prepares the product boundary and M4 delivers the Web Public Alpha.**

中文版本：[proposal.zh-CN.md](proposal.zh-CN.md)

## Why

M1–M3 established Domena's source-neutral experience contracts, dataset lineage, ROS 2 MCAP ingestion, Ray Data execution, and Lance materialization. Those capabilities are currently a Python library surface. The intended public product is a web platform: users should be able to bring embodied data into Domena, define episode boundaries, run processing, inspect quality, and publish a traceable dataset release without understanding internal Python APIs.

The public launch is therefore moved to the end of M4. The CLI remains an expert and automation interface, but it is not the primary product.

## What Changes

- Add an M3.5 control/data-plane exchange contract and freeze the product-facing job lifecycle before service implementation.
- Add a Go control plane backed by PostgreSQL for identity, workspaces, projects, data sources, datasets, jobs, audit state, and API orchestration.
- Add a TypeScript single-page web product for the complete ROS 2 MCAP-to-Lance workflow.
- Add Python quality operators and persisted quality reports executed through the existing Ray/Lance data plane.
- Add object-storage boundaries for source assets, Lance releases, and report artifacts; PostgreSQL stores metadata only.
- Add a secondary CLI/API client surface that uses the same control-plane API and domain semantics as the web product.
- Add a reproducible single-node deployment and the security, observability, and end-to-end verification required for a Public Alpha.

## Capabilities

### New Capabilities

- `control-plane-orchestration`: Product-owned job specifications, lifecycle state, leases, idempotency, project isolation, and Go/Python orchestration.
- `web-product-workflow`: Browser workflow for source registration, episode planning, processing, release publication, quality inspection, and lineage.
- `quality-reporting`: Versioned, reproducible episode/release quality measurements and failure slices.
- `public-alpha-deployment`: Secure, observable, reproducible single-node deployment and release gate.

### Modified Capabilities

- `data-plane-execution`: M3 terminal `JobRun` evidence is incorporated into the longer-lived control-plane job lifecycle without changing its release or materialization semantics.

## Milestone Boundary

- **M3.5**: specifications, exchange contracts, API/state-machine fixtures, sample workflow, and data-plane hardening. It remains internal.
- **M4a**: Go control plane and PostgreSQL persistence.
- **M4b**: TypeScript web workflow.
- **M4c**: quality operators and report product.
- **M4d**: deployment, security, recovery, documentation, and end-to-end testing.
- **M4e**: Public Alpha release.

## Impact

- Adds `control-plane/` (Go), `web/` (TypeScript), and deployment assets only after the M3.5 protocol is verified.
- Keeps `src/domena/` as the authoritative Python data plane.
- Selects PostgreSQL as the control-plane database. MySQL is not an M4 target.
- Requires S3-compatible object storage in deployed environments, with filesystem storage allowed for local tests.
- Does not add Kafka, Spark, Flink, Kubernetes, a generic workflow engine, collaborative annotation, billing, or a full training service.
