## ADDED Requirements

### Requirement: Source-neutral bounded episode

The system SHALL expose an immutable `Episode` contract identified by `domena.experience/v0.1`. An episode SHALL carry a non-empty ID, task context, ordered steps, outcome, provenance, extensions, and an asset registry without importing source-adapter dependencies.

#### Scenario: Construct a minimal episode

- **WHEN** a caller supplies a non-empty episode ID, task ID, a valid outcome, and zero or more ordered steps
- **THEN** the caller can construct an `Episode` without providing a simulator, robot SDK, or storage backend

### Requirement: Temporal and physical context

The system SHALL support optional clock domain, embodiment/environment IDs, coordinate-frame references, calibration asset references, and per-step integer-nanosecond timestamps.

#### Scenario: Preserve robot interaction context

- **WHEN** an episode contains a clock domain, frame references, calibration assets, and timestamped steps
- **THEN** validation and serialisation preserve that context without interpreting source-specific semantics

### Requirement: Structural validation

The system SHALL report path-addressable validation issues for unsupported schema version, invalid identifiers, non-contiguous step ordering, decreasing supplied timestamps, unknown asset references, non-JSON-compatible values, and unnamespaced extension keys.

#### Scenario: Detect a missing asset reference

- **WHEN** a step refers to an asset absent from the episode asset registry
- **THEN** validation returns an issue identifying the step channel path and missing asset ID

### Requirement: Local lossless envelope

The system SHALL serialise supported episode data to a local UTF-8 JSON envelope with an explicit schema identifier and read it back without silent loss.

#### Scenario: Round trip an episode with an external asset

- **WHEN** a valid episode contains an asset reference in an observation
- **THEN** serialising and reading the episode retains its ID, task/outcome context, ordered steps, extensions, asset metadata, and reference relationship

### Requirement: Basic inspection

The system SHALL provide source-neutral inspection for an episode's step count, timestamp coverage, channel names, and asset count.

#### Scenario: Inspect a mock episode

- **WHEN** a caller inspects the built-in mock episode
- **THEN** the result reports its trajectory length, available channel groups, timestamp count, and assets without requiring training code
