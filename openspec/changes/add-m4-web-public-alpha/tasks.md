## M3.5 — Product boundary and data-plane readiness

中文版本：[tasks.zh-CN.md](tasks.zh-CN.md)

- [x] 1.1 Add the versioned immutable control/data-plane job specification, canonical serialization/fingerprinting, and secret-free validation.
- [x] 1.2 Add the product job lifecycle and transition rules, attempt/lease identities, cancellation semantics, and exhaustive transition tests.
- [ ] 1.3 Add versioned worker progress and terminal-result envelopes that preserve M3 `JobRun`, failure, and materialization evidence.
- [ ] 1.4 Add representative JSON fixtures for job creation, lease, progress, success, failure, cancellation, expiry, duplicate delivery, and stale attempt rejection.
- [ ] 1.5 Add the v0.1 quality-report contract and deterministic core operators with unit tests.
- [ ] 1.6 Add one curated ROS 2 MCAP workflow fixture and a dependency-free local reference path from source inspection through report/release evidence.
- [ ] 1.7 Freeze the M4 API resource vocabulary and initial OpenAPI boundary before creating Web or CLI clients.
- [ ] 1.8 Validate the bilingual OpenSpec change in strict mode and run the complete M1–M3 regression suite.

## M4a — Go control plane

- [ ] 2.1 Create the Go service with configuration validation, structured logging, request correlation, health/readiness endpoints, and graceful shutdown.
- [ ] 2.2 Add ordered PostgreSQL migrations for identities, workspaces, projects, object registrations, sources, episode plans, datasets/releases, jobs/attempts/leases, quality summaries, idempotency, audit events, and outbox events.
- [ ] 2.3 Implement workspace authorization and invite-ready OIDC integration behind a testable identity boundary.
- [ ] 2.4 Implement source/object registration and scoped upload/download grants with checksum and content-policy verification.
- [ ] 2.5 Implement idempotent job creation, atomic leasing, heartbeat/expiry, cancellation, retry, terminal-evidence validation, and audit history.
- [ ] 2.6 Implement authenticated internal Worker APIs and a Python worker client/runner without direct PostgreSQL access.
- [ ] 2.7 Publish versioned OpenAPI and generate a TypeScript client plus API contract tests.

## M4b — TypeScript Web product

- [ ] 3.1 Create the TypeScript/React/Vite application shell, generated API client, authentication flow, workspace/project routing, accessible component baseline, and error boundary.
- [ ] 3.2 Implement project overview and data-source registration/upload flows.
- [ ] 3.3 Implement MCAP topic/time inspection and single/multiple explicit Episode segmentation with validation preview.
- [ ] 3.4 Implement dataset, immutable release, job/run diagnostics, cancellation/retry, and lineage views.
- [ ] 3.5 Add browser tests for the primary workflow, invalid segmentation, authorization isolation, processing failure, and cancellation.

## M4c — Quality product

- [ ] 4.1 Execute v0.1 quality operators locally and through Ray Data with deterministic parity.
- [ ] 4.2 Persist full report artifacts to object storage/Lance and indexed summaries to PostgreSQL through the control plane.
- [ ] 4.3 Implement release aggregation, explicit unsupported checks, versioned policy verdicts, and deterministic failure slices.
- [ ] 4.4 Implement quality overview, Episode evidence, temporal/channel diagnostics, and failure-slice Web views.

## M4d — Productization and deployment

- [ ] 5.1 Add the versioned single-node container deployment for Web, Go API, Python worker, PostgreSQL, S3-compatible object storage, and Ray runtime.
- [ ] 5.2 Add migrations, bootstrap, health/readiness ordering, bounded resources, secret handling, and backup/restore documentation.
- [ ] 5.3 Add CI for Python core/integrations, Go tests, TypeScript checks/browser tests, schema compatibility, container build, and clean end-to-end deployment.
- [ ] 5.4 Add the secondary CLI remote mode using the same API; retain an explicitly separate local engineering mode.
- [ ] 5.5 Add public installation, operator, user, troubleshooting, security, and contribution documentation in English and Chinese.
- [ ] 5.6 Complete security review for workspace isolation, object grants, upload policy, secret/log redaction, quotas, and dependency/container scanning.

## M4e — Public Alpha gate

- [ ] 6.1 Verify the browser-driven ROS 2 MCAP → Episode plan → Ray processing → Lance release → quality report → lineage workflow on a clean supported environment.
- [ ] 6.2 Verify failure diagnostics, cancellation, retry, component restart, backup/restore, object reconciliation, and cross-workspace isolation.
- [ ] 6.3 Publish the versioned Web Public Alpha only after every mandatory gate passes; label product and API stability accurately.
