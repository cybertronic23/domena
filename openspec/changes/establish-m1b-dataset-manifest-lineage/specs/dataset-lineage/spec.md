## ADDED Requirements

### Requirement: Declared construction lineage

The system SHALL retain a source-neutral construction record for a dataset release. The record SHALL include the producing tool identity/version, M1a experience schema version, selection rationale or recipe reference, and zero or more parent release references. It MAY include opaque quality, annotation, evaluation, or failure evidence references.

#### Scenario: Trace a derived release to its declared parent

- **WHEN** a curated release names an earlier dataset release as a parent
- **THEN** inspection exposes the parent release reference and construction tool identity without requiring a remote registry

### Requirement: Stable downstream references

The system SHALL expose reference values that can name a dataset release and, optionally, a source namespace, episode, and inclusive step interval. The contract SHALL not introduce metric schemas, quality scores, training execution, evaluation execution, or failure taxonomies.

#### Scenario: Record an evaluation target without running evaluation

- **WHEN** a caller creates a reference to a release member and step interval
- **THEN** the value validates and serializes without importing an evaluator or model runtime
