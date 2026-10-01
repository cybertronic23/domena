## ADDED Requirements

中文版本：[spec.zh-CN.md](spec.zh-CN.md)

### Requirement: Reproducible single-node deployment
The project SHALL provide a documented, versioned single-node deployment containing the Web application, Go API, Python worker, PostgreSQL, S3-compatible object storage, and Ray runtime. It SHALL initialize schema migrations and expose health/readiness status without requiring Kubernetes.

#### Scenario: Start a clean deployment
- **WHEN** an operator starts the documented deployment with required secrets configured
- **THEN** migrations complete once, services become ready in dependency order, and the reference workflow can be submitted

### Requirement: Secure bounded data access
The deployment SHALL enforce authentication, workspace authorization, upload size/type policy, scoped object grants, secret separation, and resource quotas. Logs and API errors SHALL NOT expose credentials or signed object URLs.

#### Scenario: Unauthorized object request
- **WHEN** a user requests an object from an inaccessible workspace
- **THEN** the service returns no object grant and records a sanitized audit event

### Requirement: Operational evidence and recovery
Requests and jobs SHALL carry correlation IDs through Go and Python logs. The deployment SHALL expose structured logs, job/attempt state, health checks, and documented backup/restore for PostgreSQL plus object-reference reconciliation. Restarting a component SHALL NOT convert an unverified attempt into success.

#### Scenario: API restarts during execution
- **WHEN** the Go API restarts while a worker owns a valid lease
- **THEN** persisted job state remains authoritative and the worker can resume heartbeats or expire according to lease policy

### Requirement: Public Alpha release gate
The Public Alpha SHALL NOT be published until a clean supported environment completes the browser-driven ROS 2 MCAP-to-Lance workflow, quality report inspection, cancellation/failure diagnostics, workspace isolation tests, and backup/restart smoke tests. The product SHALL visibly identify itself as Alpha and state that APIs may change before 1.0.

#### Scenario: Release gate fails
- **WHEN** any mandatory end-to-end, isolation, or recovery check fails
- **THEN** the version is not promoted as the M4 Public Alpha
