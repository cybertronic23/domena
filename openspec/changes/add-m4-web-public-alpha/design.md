## Status

**Approved for phased implementation.**

中文版本：[design.zh-CN.md](design.zh-CN.md)

## Context

Domena's Python data plane already owns immutable experience, dataset releases, bounded transform plans, terminal execution evidence, and verified Lance materializations. M4 introduces a user-facing product without moving those semantics into a web framework or duplicating them in Go.

## Goals / Non-Goals

**Goals**

- Make the Web application the primary product surface and keep CLI/API as expert surfaces.
- Preserve a strict Go control-plane / Python data-plane boundary.
- Let a user complete ROS 2 MCAP registration, explicit episode segmentation, processing, Lance publication, quality inspection, and lineage inspection in one product workflow.
- Persist authoritative product state transactionally in PostgreSQL and large immutable data in object storage/Lance.
- Deliver an invite-ready, single-node Public Alpha at M4 completion.

**Non-Goals**

- No raw multimodal payloads or Lance tables in PostgreSQL.
- No MCAP parsing, quality computation, or Lance writing in Go or TypeScript.
- No direct browser access to Ray, Python workers, PostgreSQL, or unrestricted object-store credentials.
- No Kafka, Kubernetes, multi-region high availability, billing, public anonymous signup, collaborative annotation, model training service, Spark, or Flink in M4.
- Daft remains an executor extension after the first Web vertical slice; it may not delay the M4 Public Alpha.

## Decisions

### 1. One product, three deliberate surfaces

The TypeScript Web application is the default user experience. A versioned HTTP API is the shared automation boundary. CLI and SDK clients consume that API in remote mode; an explicitly separate local mode may call the Python package for offline engineering work. Business behavior may not be implemented independently in the browser and CLI.

### 2. Go owns the control plane; Python owns the data plane

The Go service owns authentication integration, workspaces, projects, data-source registrations, episode-plan metadata, dataset/release catalog records, job commands, idempotency, leases, audit events, and user-facing API responses.

Python workers own source inspection, MCAP decoding, episode construction, transform execution, quality computation, Ray Data execution, and Lance publication. Workers receive a versioned, immutable job specification and return versioned progress/terminal evidence. Go treats the existing Domena `JobRun` and `MaterializationReference` as data-plane evidence rather than reconstructing their rules.

Python workers do not write PostgreSQL directly. They lease work and report progress/results through authenticated internal Go endpoints. This leaves database ownership in one service and makes worker credentials narrow.

### 3. PostgreSQL is authoritative metadata storage

PostgreSQL stores accounts/identities, workspaces, projects, source registrations, episode plans, dataset catalog metadata, release fingerprints, jobs, attempts, quality-report summaries, audit events, idempotency records, and object references.

Schema migrations are ordered and immutable after release. Every tenant-owned row carries a `workspace_id`; authorization is checked in the service and reinforced with database constraints. JSONB is allowed for versioned configuration and evidence, never as a substitute for core relational identity or state-transition constraints.

### 4. Object storage and Lance store data, not product state

Original MCAP/HDF5/media, generated Episode artifacts, full quality-report artifacts, and Lance datasets live in S3-compatible object storage. Local development may use a filesystem implementation behind the same object-reference contract. Uploads use short-lived scoped URLs; the browser never receives general object-store credentials.

Lance remains the physical multimodal dataset format. A published product release references the Domena release fingerprint and verified `MaterializationReference`; it is not identified only by an object path or Lance version.

### 5. Product job lifecycle wraps immutable execution attempts

The control-plane job state machine is:

`queued → leased → running → succeeded | failed | cancelling → cancelled`

`leased` work may return to `queued` only after its lease expires and no terminal result was accepted. Cancellation is a requested control-plane state until a worker acknowledges it. Each retry creates a new immutable attempt while retaining one stable product job identity. A successful terminal result must contain verified materialization evidence when the job type publishes a release. Late or duplicate events are accepted idempotently or rejected without regressing state.

M3.5 freezes a JSON-compatible exchange envelope with schema version, job identity, workspace/project identity, job kind, input references, deterministic configuration, requested engine/runtime, output target, attempt number, and idempotency key. Secrets are references, never embedded credentials.

### 6. PostgreSQL-backed dispatch before a message broker

M4 uses transactional job creation plus bounded worker leasing exposed through the Go internal API. PostgreSQL locking and lease expiry provide the initial reliable dispatch mechanism. A transactional outbox records externally relevant events. Kafka/NATS or a workflow engine may be introduced only from measured scale or delivery requirements, without changing the job exchange contract.

### 7. The Web application is a lightweight TypeScript SPA

The default implementation is TypeScript with React, Vite, TanStack Query, a typed API client generated from OpenAPI, and a small accessible component layer. Server-side rendering is not required for the authenticated data application. The information architecture contains:

- sign-in and workspace selection;
- project overview;
- data sources and source inspection;
- MCAP topic/timeline inspection and episode segmentation;
- datasets and immutable releases;
- pipelines/jobs and run diagnostics;
- quality reports and failure slices;
- lineage; and
- workspace settings.

### 8. Quality reports are versioned data products

The first report version records channel presence, step/time coverage, timestamp monotonicity, observed rates, gaps, episode duration, and validation issues. Metrics identify their operator ID/version, configuration fingerprint, source Episode/release fingerprint, and generation time. Aggregate release reports link back to episode evidence. Threshold-based quality policy is explicit and versioned; metrics are not silently converted into pass/fail.

### 9. Public Alpha is invite-ready and single-node first

The reference deployment uses containers for the Web assets, Go API, Python worker, PostgreSQL, S3-compatible object storage, and a Ray runtime. It supports health/readiness checks, migrations, bounded uploads, structured logs, request/job correlation IDs, backups of control metadata, cancellation, retries, and documented recovery. Kubernetes is not required for M4.

The initial authentication integration may be invite-only OIDC. Public anonymous registration is not required. Workspace authorization, upload limits, content-type validation, scoped object access, audit records, and resource quotas are release blockers.

## Compatibility

- Existing M1–M3 Python public contracts remain supported.
- New exchange schemas start at `v0.1` and may evolve before 1.0 only through explicit versioning.
- Web and CLI use the same versioned API. Local CLI behavior is explicitly separate and cannot imply remote persistence.
- M4 does not rename Domena release fingerprints, composite Episode identity, or Lance publication evidence.

## Risks / Trade-offs

- [M4 becomes too broad] → deliver one ROS 2 MCAP-to-Lance vertical slice and defer generic workflow construction.
- [Go and Python duplicate domain logic] → Go stores and orchestrates versioned evidence; Python remains authoritative for data validation and execution.
- [PostgreSQL dispatch reaches scale limits] → retain a broker-neutral lease contract and add a broker only from measured need.
- [Object storage introduces unsafe access] → scoped upload/download grants, checksum verification, allow-listed schemes, and no browser credentials.
- [Web UI hides reproducibility details] → expose fingerprints, versions, configuration, evidence, and lineage on every run/release.
- [Quality scores become misleading] → publish metric evidence and versioned policies instead of one opaque score.

## Implementation Sequence

1. M3.5: exchange contract, state-transition tests, sample job fixtures, API resource vocabulary, and data-plane quality-report contract.
2. M4a: Go service skeleton, PostgreSQL migrations/repositories, OpenAPI, auth/workspace boundary, job leasing, and Python worker integration.
3. M4b: TypeScript shell and the end-to-end source/episode/dataset/job workflow.
4. M4c: quality operators, quality report persistence, and report/failure-slice UI.
5. M4d: container deployment, security hardening, observability, recovery, docs, and end-to-end test.
6. M4e: tag and publish the Web Public Alpha.

## Open Questions

None for the M4 architecture boundary. Exact OIDC provider and visual component library are deployment choices and may not change the specified security or API behavior.
