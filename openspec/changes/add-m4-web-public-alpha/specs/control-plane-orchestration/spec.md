## ADDED Requirements

中文版本：[spec.zh-CN.md](spec.zh-CN.md)

### Requirement: Versioned immutable data-job specification
The system SHALL exchange a JSON-compatible immutable data-job specification containing a schema version, stable job ID, workspace ID, project ID, job kind, input references, deterministic configuration, requested engine and runtime, output target, attempt number, and idempotency key. Credentials SHALL NOT appear in the specification; only scoped secret or object references are permitted.

#### Scenario: Submit the same command twice
- **WHEN** a client repeats a create-job command with the same workspace-scoped idempotency key and equivalent payload
- **THEN** the control plane returns the same job identity and does not create a second execution

#### Scenario: Reject a changed idempotent command
- **WHEN** a client reuses an idempotency key with a semantically different payload
- **THEN** the control plane rejects the request as an idempotency conflict

#### Scenario: Keep credentials out of work
- **WHEN** a job requires protected input or output access
- **THEN** its specification contains a scoped reference resolvable by the worker and no embedded access key, password, or bearer token

### Requirement: Authoritative product job lifecycle
The control plane SHALL enforce the lifecycle `queued → leased → running → succeeded | failed | cancelling → cancelled`. It SHALL prevent state regression and SHALL record every accepted transition with job identity, attempt identity, actor, time, and correlation ID.

#### Scenario: Complete a publishing job
- **WHEN** a running publication job reports success
- **THEN** the transition is accepted only with terminal Domena `JobRun` evidence and a verified `MaterializationReference`

#### Scenario: Request cancellation
- **WHEN** a user cancels a queued job
- **THEN** the job becomes cancelled without worker execution

#### Scenario: Cancel running work
- **WHEN** a user cancels running work
- **THEN** the job enters cancelling until the worker acknowledges cancellation or reports a terminal failure

#### Scenario: Receive a stale event
- **WHEN** an event from an older attempt would regress or replace the accepted state
- **THEN** the control plane rejects or idempotently ignores it and preserves the current state

### Requirement: Bounded worker lease and retry
The control plane SHALL lease queued jobs to authenticated workers for a bounded interval. A lease SHALL identify one immutable attempt and lease token. Expired non-terminal work MAY be requeued; every retry SHALL create a new attempt while preserving the stable job identity and prior attempt evidence.

#### Scenario: Worker leases available work
- **WHEN** an authorized compatible worker requests work and a queued job is available
- **THEN** the control plane atomically creates an attempt, grants one lease, and prevents another worker from leasing the same attempt

#### Scenario: Lease expires without terminal evidence
- **WHEN** a worker stops heartbeating and its lease expires
- **THEN** the attempt is marked expired and policy may return the job to queued without deleting attempt evidence

### Requirement: Workspace isolation and authorization
Every product resource SHALL belong to a workspace and project where applicable. User-facing and internal APIs SHALL verify the authenticated actor's access before returning metadata, issuing object access, or mutating state. Cross-workspace identifiers SHALL be indistinguishable from unavailable resources to unauthorized callers.

#### Scenario: Access another workspace's release
- **WHEN** a user supplies a valid release ID owned by a workspace they cannot access
- **THEN** the API returns no release data and issues no object-storage authorization

### Requirement: Single database owner
The Go control plane SHALL be the only application component that writes control-plane PostgreSQL state. Python workers SHALL lease work and report progress or terminal evidence through authenticated internal APIs and SHALL NOT receive direct database write credentials.

#### Scenario: Worker publishes terminal evidence
- **WHEN** a Python worker finishes a job
- **THEN** it submits versioned terminal evidence to the internal API and the Go control plane validates and commits the state transactionally

### Requirement: M3 execution evidence compatibility
The orchestration layer SHALL preserve the input release fingerprint, transform fingerprint, engine name, runtime name, failure evidence, and materialization evidence produced by the M3 data plane. It SHALL NOT infer a successful publication from process exit alone.

#### Scenario: Process exits successfully without materialization
- **WHEN** a publication worker exits with code zero but supplies no verified materialization evidence
- **THEN** the control plane does not mark the job succeeded
