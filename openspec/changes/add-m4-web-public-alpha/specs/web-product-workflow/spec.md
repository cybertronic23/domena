## ADDED Requirements

中文版本：[spec.zh-CN.md](spec.zh-CN.md)

### Requirement: Web-first source-to-release workflow
The Web product SHALL let an authorized user register or upload a ROS 2 MCAP source, inspect its topics and time range, define one whole-source episode or multiple explicit half-open episode segments, validate the plan, submit processing, and inspect the resulting immutable dataset release without requiring CLI or Python use.

#### Scenario: Import one episode
- **WHEN** a user chooses the complete source as one episode and submits a valid plan
- **THEN** the product displays the source, resulting episode identity, processing job, and published release lineage

#### Scenario: Import multiple explicit episodes
- **WHEN** a user provides non-overlapping explicit `[start, end)` segments with episode IDs
- **THEN** the product previews and persists those boundaries without heuristic splitting

#### Scenario: Invalid segment plan
- **WHEN** a segment is empty, overlaps another segment, or lies outside the source range
- **THEN** the product prevents submission and identifies the invalid boundary

### Requirement: Reproducibility is visible in the product
Dataset release and job views SHALL expose source identity, Episode composite identity, release fingerprint, transform/operator versions, deterministic configuration, engine/runtime, materialization reference, quality evidence, and parent lineage where applicable.

#### Scenario: Inspect a release
- **WHEN** a user opens a published release
- **THEN** the UI provides its immutable fingerprint, member count, source/parent lineage, producing job, and physical materialization without presenting a mutable path as release identity

### Requirement: Actionable job diagnostics
The Web product SHALL show current control-plane state, current attempt, timestamps, progress when available, cancellation availability, and sanitized failure evidence. User-visible errors SHALL preserve a stable error code and correlation ID while excluding credentials and internal secrets.

#### Scenario: Processing fails
- **WHEN** a worker reports terminal failure evidence
- **THEN** the job page shows the failure code, actionable message, attempt history, and correlation ID and does not display a successful release

### Requirement: Shared API semantics
The browser, CLI remote mode, and external clients SHALL consume the same versioned control-plane API. The Web client SHALL NOT directly call Ray, Python worker endpoints, PostgreSQL, or object storage except through scoped upload/download URLs issued by the API.

#### Scenario: Browser uploads a source
- **WHEN** the Web client requests an upload
- **THEN** the API authorizes the workspace, creates an object registration, and returns only a bounded scoped upload grant
