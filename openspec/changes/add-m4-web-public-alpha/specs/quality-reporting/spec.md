## ADDED Requirements

中文版本：[spec.zh-CN.md](spec.zh-CN.md)

### Requirement: Versioned reproducible quality report
The data plane SHALL produce a versioned quality report bound to an Episode or dataset release fingerprint. Each metric SHALL identify its operator ID/version and deterministic configuration fingerprint. Regenerating a report from equivalent immutable input and configuration SHALL produce equivalent metric evidence, excluding declared volatile metadata.

#### Scenario: Generate an Episode report
- **WHEN** a valid Episode is evaluated with a supported quality operator set
- **THEN** the report records source fingerprint, operator versions, configuration fingerprint, metric evidence, issues, and generation metadata

### Requirement: Minimum M4 quality evidence
The first report version SHALL support channel presence, step/time coverage, timestamp monotonicity, observed sample rates, temporal gaps, Episode duration, and existing contract-validation issues. Unsupported modality-specific checks SHALL be explicit rather than reported as passing.

#### Scenario: Required channel is absent
- **WHEN** policy declares a channel required and the Episode has no such channel
- **THEN** the report contains a missing-channel issue with the channel identity and supporting counts

#### Scenario: Check is unsupported
- **WHEN** a configured check cannot evaluate the source representation
- **THEN** the report marks the check unsupported and does not count it as pass

### Requirement: Evidence before policy verdict
Quality metrics and issues SHALL remain separate from a versioned quality policy verdict. A policy SHALL identify its thresholds and version. Changing policy SHALL NOT mutate previously recorded metric evidence.

#### Scenario: Re-evaluate with a new policy
- **WHEN** the same report evidence is evaluated under a newer threshold policy
- **THEN** the system records a new verdict linked to the same evidence without rewriting the original report

### Requirement: Release aggregation and failure slices
A dataset-release quality report SHALL aggregate Episode evidence without hiding member-level results. It SHALL support deterministic failure slices that identify the member composite identities and the policy/check that selected them.

#### Scenario: Inspect an aggregate failure
- **WHEN** a release-level metric indicates failed members
- **THEN** the user can navigate to the selected Episode identities and their supporting evidence
